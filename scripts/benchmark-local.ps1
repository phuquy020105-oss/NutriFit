[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-z0-9-]+$')][string]$Label,
    [string]$EnvFile=(Join-Path $PSScriptRoot '..\.env'),
    [switch]$Setup,
    [ValidateSet(0,2)][int]$FixtureIndex=0,
    [switch]$NewEquivalentFixture,
    [string]$WarFile,
    [switch]$ServiceChecks
)
$ErrorActionPreference='Stop'
$projectRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
if(-not (Test-Path -LiteralPath $EnvFile -PathType Leaf)){throw 'Private local configuration file required.'}
# First '=' only; no shell interpolation, inline-comment stripping, logging or cloud variables.
$config=@{}
foreach($line in [IO.File]::ReadAllLines([IO.Path]::GetFullPath($EnvFile))){
    if($line -match '^\s*(#|$)'){continue}
    $split=$line.IndexOf('=');if($split -lt 1){throw 'Invalid configuration assignment.'}
    $name=$line.Substring(0,$split).Trim()
    if($name -notmatch '^(LOCAL_DB_(HOST|PORT|USER|PASSWORD)|NUTRIFIT_DB_(USER|PASSWORD))$'){continue}
    $value=$line.Substring($split+1).Trim()
    if($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))){$value=$value.Substring(1,$value.Length-2)}
    $config[$name]=$value
}
if(($config.LOCAL_DB_HOST -and $config.LOCAL_DB_HOST -ne '127.0.0.1') -or ($config.LOCAL_DB_PORT -and $config.LOCAL_DB_PORT -ne '3306')){throw 'Only approved loopback MySQL127.0.0.1:3306 allowed.'}
$env:NUTRIFIT_DB_USER=if($config.LOCAL_DB_USER){$config.LOCAL_DB_USER}else{$config.NUTRIFIT_DB_USER}
$env:NUTRIFIT_DB_PASSWORD=if($config.LOCAL_DB_PASSWORD){$config.LOCAL_DB_PASSWORD}else{$config.NUTRIFIT_DB_PASSWORD}
if(-not $env:NUTRIFIT_DB_USER -or -not $env:NUTRIFIT_DB_PASSWORD){throw 'Missing local credentials; never use cloud credentials as fallback.'}
$env:NUTRIFIT_DB_URL='';$env:NUTRIFIT_DB_CA_FILE=''
$env:NUTRIFIT_LOCAL_DB_NAME='nutrifit_performance_20261020_test'
$env:PYTHONDONTWRITEBYTECODE='1'
$java=Join-Path $env:JAVA_HOME 'bin\java.exe'
if(-not (Test-Path -LiteralPath $java) -or -not $env:TOMCAT_HOME){throw 'Set JAVA_HOME(JDK21) and TOMCAT_HOME(Tomcat10.1).'}
# Only a generated TEST fixture password is retained, encrypted with current-user Windows DPAPI.
$secretPath=Join-Path ([IO.Path]::GetTempPath()) 'nutrifit-perf-test-password.dpapi'
if(-not (Test-Path -LiteralPath $secretPath)){
    if(-not $Setup){throw 'First fixture run requires -Setup and an empty users table.'}
    ConvertTo-SecureString ([Guid]::NewGuid().ToString('N')) -AsPlainText -Force | ConvertFrom-SecureString | Set-Content -LiteralPath $secretPath
}
$encrypted=([IO.File]::ReadAllText($secretPath)).Trim()
$env:NUTRIFIT_BENCH_PASSWORD=[Net.NetworkCredential]::new('',(ConvertTo-SecureString $encrypted)).Password
Push-Location $projectRoot
try{
    $classpath='target/test-classes;target/classes;target/nutrifit/WEB-INF/lib/*'
    if($Setup -and $FixtureIndex -ne 0){throw 'Initial Setup creates fixture0/1 only.'}
    if($NewEquivalentFixture){
        if($FixtureIndex -ne 2){throw 'Equivalent fixture must use index2.'}
        & $java -cp $classpath com.nutrifit.performance.LocalPerformanceCheck setup-additional
        if($LASTEXITCODE -ne 0){throw 'Equivalent fixture setup failed; never overwrite/retry automatically.'}
    }
    $benchmarkArgs=@('scripts/benchmark_local.py','--label',$Label,'--fixture-index',[string]$FixtureIndex)
    if($WarFile){
        if(-not (Test-Path -LiteralPath $WarFile -PathType Leaf)){throw 'Baseline WAR does not exist.'}
        $benchmarkArgs+=@('--war',[IO.Path]::GetFullPath($WarFile))
    }
    if($Setup){$benchmarkArgs+='--setup'}
    & python @benchmarkArgs
    if($LASTEXITCODE -ne 0){throw 'Benchmark failed; stop without resetting or clearing fixtures.'}
    if($ServiceChecks){
        if($FixtureIndex -ne 0){throw 'ServiceChecks uses fixture0, not an equivalent comparison fixture.'}
        $classpath='target/test-classes;target/classes;target/nutrifit/WEB-INF/lib/*'
        & $java -cp $classpath com.nutrifit.performance.LocalPerformanceCheck integration
        if($LASTEXITCODE -ne 0){throw 'Local pool/dashboard checks failed.'}
        $env:VNPAY_TMN_CODE='LOCAL-PERFORMANCE-TEST'
        $env:VNPAY_HASH_SECRET=[Guid]::NewGuid().ToString('N')
        $env:VNPAY_RETURN_URL='http://127.0.0.1:9088/nutrifit/payment/return'
        & $java -cp $classpath com.nutrifit.service.LocalServiceTransactionCheck
        if($LASTEXITCODE -ne 0){throw 'Local transaction checks failed; no automatic retry.'}
    }
}finally{
    $env:NUTRIFIT_BENCH_PASSWORD=$null
    Pop-Location
}
