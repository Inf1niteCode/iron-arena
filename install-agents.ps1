$agentsDir = "$env:USERPROFILE\.claude\agents"
$repoDir = "C:\Inf1niteCode\agency-agents"

New-Item -ItemType Directory -Force -Path $agentsDir

$files = @(
    "specialized\agents-orchestrator.md",
    "project-management\project-manager-senior.md",
    "engineering\engineering-backend-architect.md",
    "engineering\engineering-frontend-developer.md",
    "engineering\engineering-senior-developer.md",
    "engineering\engineering-rapid-prototyper.md",
    "engineering\engineering-security-engineer.md",
    "design\design-ui-designer.md",
    "testing\testing-reality-checker.md",
    "testing\testing-evidence-collector.md"
)

foreach ($f in $files) {
    Copy-Item "$repoDir\$f" $agentsDir
    Write-Host "OK: $f"
}

Write-Host ""
Write-Host "Готово! Агентов установлено: $(ls $agentsDir | Measure-Object).Count"