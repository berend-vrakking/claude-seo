# Claude SEO - Ahrefs extension installer (Windows / PowerShell).
# Mirrors extensions/ahrefs/install.sh.
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$SkillDir = Join-Path $HOME ".claude/skills"
# MCP servers live in ~/.claude.json (the file `claude mcp add` writes).
# NOT ~/.claude/settings.json - `mcpServers` is not a key Claude Code reads
# there, so entries written to settings.json silently never load.
$McpConfigJson = Join-Path $HOME ".claude.json"

if (-not (Test-Path (Join-Path $SkillDir "seo"))) {
    throw "claude-seo base plugin not installed."
}

$Token = Read-Host "Ahrefs MCP key" -AsSecureString
$Plain = [System.Net.NetworkCredential]::new("", $Token).Password
if (-not $Plain) { throw "No token provided." }

$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillTarget = Join-Path $SkillDir "seo-ahrefs"
New-Item -ItemType Directory -Path (Join-Path $SkillTarget "references") -Force | Out-Null
Copy-Item -Path (Join-Path $SourceDir "skills/seo-ahrefs/SKILL.md") `
          -Destination (Join-Path $SkillTarget "SKILL.md") -Force
Copy-Item -Path (Join-Path $SourceDir "skills/seo-ahrefs/references/*.md") `
          -Destination (Join-Path $SkillTarget "references") -Force
Write-Host "[OK] Installed skill: $SkillTarget"
$AgentDir = Join-Path $HOME ".claude/agents"
New-Item -ItemType Directory -Path $AgentDir -Force | Out-Null
Copy-Item -Path (Join-Path $SourceDir "agents/seo-ahrefs.md") `
          -Destination (Join-Path $AgentDir "seo-ahrefs.md") -Force
Write-Host "[OK] Installed agent: $AgentDir/seo-ahrefs.md"

# Merge ~/.claude.json.
$settingsContent = if (Test-Path $McpConfigJson) { Get-Content $McpConfigJson -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
if (-not $settingsContent.mcpServers) { $settingsContent | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{}) -Force }
# Remote HTTP server; the key travels as a Bearer header.
$settingsContent.mcpServers | Add-Member -NotePropertyName 'ahrefs' -NotePropertyValue @{
    type = 'http'
    url = 'https://api.ahrefs.com/mcp/mcp'
    headers = @{ Authorization = "Bearer $Plain" }
} -Force
# Write atomically: stage to a temp file in the same directory, then swap
# it into place, so a crash mid-write never leaves ~/.claude.json truncated
# or half-written (it is shared with Claude Code and other installers).
# -Depth 100 (not the ConvertTo-Json default of 2) so an existing
# ~/.claude.json with deeply nested config round-trips intact.
$TempConfigJson = Join-Path (Split-Path -Parent $McpConfigJson) ".claude.json.$([guid]::NewGuid().ToString('N')).tmp"
$jsonText = $settingsContent | ConvertTo-Json -Depth 100
# Write without a byte-order mark: on Windows PowerShell 5.1, Set-Content -Encoding UTF8
# emits a BOM and Node's JSON.parse rejects it, which would make ~/.claude.json unreadable.
[System.IO.File]::WriteAllText($TempConfigJson, $jsonText, (New-Object System.Text.UTF8Encoding $false))
Move-Item -Path $TempConfigJson -Destination $McpConfigJson -Force
Write-Host "Wrote mcpServers.ahrefs to $McpConfigJson"

Write-Host ""
Write-Host "Done. Open a new Claude Code session and run /seo ahrefs metrics <domain>."
