[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('Backup','LocalTrial','ApplyAiven')][string]$Mode,
    [string]$EnvFile='D:\NutriFit-backups\aiven-migration\.env',
    [Parameter(Mandatory=$true)][string]$BackupDirectory,
    [string]$LocalDatabase,
    [string]$GoLiveApprovedManifest,
    [switch]$ResumeEmptyLocal
)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../..')).Path
Push-Location -LiteralPath $projectRoot
try {
    if (-not $env:JAVA_HOME) { throw 'Set JAVA_HOME to JDK21 before running.' }
    $java=Join-Path $env:JAVA_HOME 'bin/java.exe'
    $javac=Join-Path $env:JAVA_HOME 'bin/javac.exe'
    if (-not (Test-Path -LiteralPath 'target/nutrifit/WEB-INF/lib')) { throw 'Run Maven package with JDK21 first.' }
    if (-not (Test-Path -LiteralPath $EnvFile)) { throw 'Private configuration file not found.' }
    if ($Mode -eq 'ApplyAiven' -and $GoLiveApprovedManifest -notmatch '^[a-f0-9]{64}$') {
        throw 'Production requires explicit owner approval of the exact final-manifest SHA256.'
    }
    $classPath='target/food-quality-tools;target/classes;target/nutrifit/WEB-INF/lib/*'
    $sources=@('LocalFoodQualityTrial.java','FoodQualityReadOnly.java','FoodQualityReleaseSnapshot.java','CatalogReleaseMigration.java') |
        ForEach-Object { Join-Path $PSScriptRoot $_ }
    & $javac --release 21 -encoding UTF-8 -cp $classPath -d target/food-quality-tools @sources
    if ($LASTEXITCODE -ne 0) { throw 'Release tooling compilation failed.' }
    if ($Mode -eq 'Backup') {
        & $java -cp $classPath com.nutrifit.config.FoodQualityReleaseSnapshot $EnvFile $BackupDirectory
    } elseif ($Mode -eq 'LocalTrial') {
        if ($LocalDatabase -notmatch '^nutrifit_fq_[a-z0-9_]+_test$' -or $LocalDatabase.Length -gt 64) { throw 'Dedicated local test database name required.' }
        $toolArgs=@('--local-trial',$EnvFile,$LocalDatabase,$BackupDirectory)
        if ($ResumeEmptyLocal) { $toolArgs+='--resume-empty-local' }
        & $java -cp $classPath com.nutrifit.service.CatalogReleaseMigration @toolArgs
    } else {
        & $java -cp $classPath com.nutrifit.service.CatalogReleaseMigration --apply-aiven $EnvFile $BackupDirectory --go-live-approved-manifest $GoLiveApprovedManifest
    }
    if ($LASTEXITCODE -ne 0) { throw 'Release tool stopped; do not retry a partial production operation. Review read-only first.' }
} finally { Pop-Location }
