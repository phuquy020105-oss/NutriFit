[CmdletBinding()]
param(
    [ValidateSet('Run','Init','Seed','Verify','Test','Check')][string]$Action='Run',
    [ValidatePattern('^(nutrifitdb_java|nutrifit_[a-z0-9_]+_test)$')][string]$Database='nutrifitdb_java',
    [string]$EnvFile=(Join-Path $PSScriptRoot '..\.env')
)
$ErrorActionPreference='Stop'
$projectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if (-not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) { throw 'Configuration file missing. Copy .env.example to .env and fill values locally.' }
# Literal first '=' split; no interpolation, evaluation, inline-comment stripping or secret output.
foreach ($line in [IO.File]::ReadAllLines([IO.Path]::GetFullPath($EnvFile))) {
    if ($line -match '^\s*(#|$)') { continue }
    $separator=$line.IndexOf('=')
    if ($separator -lt 1) { throw 'Invalid environment assignment.' }
    $name=$line.Substring(0,$separator).Trim(); $value=$line.Substring($separator+1).Trim()
    if ($name -notmatch '^[A-Z][A-Z0-9_]*$') { throw 'Invalid environment variable name.' }
    if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))) { $value=$value.Substring(1,$value.Length-2) }
    if ($name -match '^(LOCAL_DB_|NUTRIFIT_|BREVO_|GEMINI_|VNPAY_)' -or $name -eq 'PORT') { [Environment]::SetEnvironmentVariable($name,$value,'Process') }
}
$java=Join-Path $env:JAVA_HOME 'bin\java.exe'
if (-not (Test-Path -LiteralPath $java)) { throw 'JAVA_HOME must point to JDK21.' }
Push-Location $projectRoot
try {
    if ($Action -eq 'Run') {
        if (-not $env:CATALINA_HOME -or -not (Test-Path (Join-Path $env:CATALINA_HOME 'bin\catalina.bat'))) { throw 'Set CATALINA_HOME to Tomcat10.1.' }
        if (-not (Test-Path 'target\nutrifit.war')) { throw 'Run mvn clean package first.' }
        Copy-Item -LiteralPath 'target\nutrifit.war' -Destination (Join-Path $env:CATALINA_HOME 'webapps\nutrifit.war')
        & (Join-Path $env:CATALINA_HOME 'bin\catalina.bat') run
    } else {
        if (-not (Test-Path 'target\nutrifit\WEB-INF\lib')) { throw 'Run mvn clean package first.' }
        $env:LOCAL_DB_NAME=$Database
        & $java --class-path 'target/classes;target/nutrifit/WEB-INF/lib/*' 'database/seed/CatalogSeed.java' $Action.ToLowerInvariant()
        if ($LASTEXITCODE -ne 0) { throw 'Catalog command failed. No automatic retry.' }
        if ($Action -in @('Test','Check')) {
            & $java --class-path 'target/test-classes;target/classes;target/nutrifit/WEB-INF/lib/*' com.nutrifit.dao.MealPlanHistoryReadOnlyCheck
        }
    }
    if ($LASTEXITCODE -ne 0) { throw 'Local command failed. No automatic retry.' }
} finally { Pop-Location }
