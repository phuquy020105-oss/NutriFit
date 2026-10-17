# Chạy integration test Nutrition bằng Maven và PowerShell

Yêu cầu: JDK 21, Maven 3.9, PowerShell 5.1+ và catalog đã có trong MySQL local. Không cần Python hoặc dependency mới.
Test hiện dùng URL cố định trong DatabaseConfig: `127.0.0.1:3306/nutrifitdb_java`; đổi DB_HOST/DB_NAME trong .env không thay URL Java.
Các lệnh dưới không import SQL hoặc tạo user; suite chỉ đọc catalog và đóng transaction bằng rollback.

## 1. Tạo lại fixture từ JSON trên mỗi checkout

Chạy nguyên khối PowerShell dưới từ repository. Fixture nằm trong target, không cần commit; chạy lại sau `mvn clean` hoặc khi đổi checkout.
Không lấy fixture/hashes cũ từ máy khác vì byte xuống dòng của JSON có thể khác. Không tự sửa fixture để làm test PASS.

```powershell
Set-Location D:\Web\NutriFit
$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$utf8 = New-Object System.Text.UTF8Encoding($false)
$invariant = [System.Globalization.CultureInfo]::InvariantCulture
$fixtureDir = Join-Path $root 'target\nutrition-integration\fixtures'
New-Item -ItemType Directory -Path $fixtureDir -Force | Out-Null
$jsonPath = Join-Path $root 'database\seed\vietnamese_catalog.json'
$catalog = [System.IO.File]::ReadAllText($jsonPath, $utf8) | ConvertFrom-Json
$keys = @('calories_per_100g','protein_per_100g','carbs_per_100g','fat_per_100g','fiber_per_100g')
function Get-NfDecimal($value) { [decimal]::Parse([string]$value, $invariant) }
function ConvertTo-NfBase64($value) { [Convert]::ToBase64String($utf8.GetBytes([string]$value)) }
function Write-NfRows($name, $rows) {
    [System.IO.File]::WriteAllLines((Join-Path $fixtureDir $name), [string[]]@($rows), $utf8)
}
if (@($catalog.foods).Count -ne 82 -or @($catalog.recipes).Count -ne 30) { throw 'Unexpected catalog counts' }
$foods = @{}
$foodRows = foreach ($food in $catalog.foods) {
    if ($foods.ContainsKey($food.ref)) { throw 'Duplicate Food ref' }
    $foods[$food.ref] = $food
    $values = foreach ($key in $keys) {
        $number = Get-NfDecimal $food.nutrients.$key
        if ($number -lt 0 -or $number -gt 9999999.999) { throw 'Food nutrient outside DECIMAL(10,3)' }
        $number.ToString($invariant)
    }
    (@($food.ref, (ConvertTo-NfBase64 $food.name)) + @($values)) -join "`t"
}
$recipeRows = foreach ($recipe in $catalog.recipes) {
    if ((Get-NfDecimal $recipe.base_servings) -ne 1) { throw 'Expected base_servings=1.00' }
    @($recipe.ref, (ConvertTo-NfBase64 $recipe.name), $recipe.meal_type, $recipe.base_servings,
      [string]$recipe.prep_minutes, (ConvertTo-NfBase64 $recipe.instructions)) -join "`t"
}
foreach ($meal in @('BREAKFAST','LUNCH','DINNER')) {
    if (@($catalog.recipes | Where-Object { $_.meal_type -eq $meal }).Count -ne 10) { throw 'Expected 10 recipes per meal' }
}
$ingredientRows = foreach ($recipe in $catalog.recipes) {
    foreach ($ingredient in $recipe.ingredients) {
        if (-not $foods.ContainsKey($ingredient.food_ref) -or (Get-NfDecimal $ingredient.quantity_grams) -le 0) { throw 'Invalid ingredient' }
        @($recipe.ref, $ingredient.food_ref, $ingredient.quantity_grams) -join "`t"
    }
}
if (@($ingredientRows).Count -ne 383) { throw 'Expected 383 ingredients' }
$published = @{}
foreach ($line in [System.IO.File]::ReadAllLines((Join-Path $root 'docs\nutrition\vietnamese-food-nutrition-data.md'), $utf8)) {
    if ($line -match '^\| (R\d{3}) \|') {
        $cells = $line.Split('|') | ForEach-Object { $_.Trim() }
        $published[$cells[1]] = ($cells[4..8] -join "`t")
    }
}
if ($published.Count -ne 30) { throw 'Expected 30 published nutrition rows' }
$totalRows = foreach ($recipe in $catalog.recipes) {
    foreach ($servings in @('0.5','1','2')) {
        $values = foreach ($key in $keys) {
            $entire = [decimal]0
            foreach ($ingredient in $recipe.ingredients) {
                $entire += (Get-NfDecimal $ingredient.quantity_grams) / 100 * (Get-NfDecimal $foods[$ingredient.food_ref].nutrients.$key)
            }
            $value = $entire * (Get-NfDecimal $servings) / (Get-NfDecimal $recipe.base_servings)
            [decimal]::Round($value, 3, [MidpointRounding]::AwayFromZero).ToString('0.000', $invariant)
        }
        if ($servings -eq '1' -and (@($values) -join "`t") -cne $published[$recipe.ref]) { throw 'Nutrition differs from published table' }
        (@($recipe.ref, $servings) + @($values)) -join "`t"
    }
}
Write-NfRows 'foods.tsv' $foodRows
Write-NfRows 'recipes.tsv' $recipeRows
Write-NfRows 'ingredients.tsv' $ingredientRows
Write-NfRows 'totals.tsv' $totalRows
Write-NfRows 'catalog.sha256' @((Get-FileHash -LiteralPath $jsonPath -Algorithm SHA256).Hash.ToLowerInvariant())
Write-Output 'Fixture ready: 82 Foods, 30 Recipes, 383 ingredients, 90 nutrition cases.'
```

Decimal .NET và AwayFromZero trên giá trị không âm tương ứng HALF_UP ở bước cuối; không làm tròn mỗi nguyên liệu hoặc nhân snapshot một phần đã làm tròn. Bộ dữ liệu này nằm trong độ chính xác Decimal .NET.
Đoạn lệnh còn kiểm tra 30 tổng một phần với tài liệu công bố; nó không thay thế toàn bộ bộ kiểm tra SQL/JSON trước đây.

## 2. Chạy unit test hoặc build thông thường

Chạy từ CMD ở root repository:

```cmd
mvn.cmd test
mvn.cmd -DskipTests package
```

Mặc định suite MySQL bị skip nếu không có NUTRIFIT_MYSQL_INTEGRATION=true. Không tính các test skip là PASS.
Máy local hiện dùng được cache `target/maven-repository`; nếu cache mặc định không ghi được, thêm đối số `-Dmaven.repo.local=D:\Web\NutriFit\target\maven-repository`.
Máy thành viên khác có thể dùng cache Maven mặc định của họ. Không chạy clean giữa bước sinh fixture và test; nếu đã clean thì sinh fixture lại.

## 3. Chạy suite MySQL thật

Sau bước 1, tiếp tục trong cùng PowerShell. Nhập credentials trực tiếp tại prompt; không ghi password vào README, -D, argv hoặc chat. Suite không tự đọc .env.

```powershell
$env:NUTRIFIT_DB_USER = Read-Host 'MySQL user'
$password = Read-Host 'MySQL password' -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
try {
    $env:NUTRIFIT_DB_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    $env:NUTRIFIT_MYSQL_INTEGRATION = 'true'
    $env:NUTRIFIT_CATALOG_FIXTURES = $fixtureDir
    & mvn.cmd -B '-Dtest=NutritionMySqlIntegrationTest' '-Duser.timezone=Asia/Bangkok' test
    if ($LASTEXITCODE -ne 0) { throw 'Integration test failed' }
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    $password.Dispose()
    Remove-Item Env:NUTRIFIT_DB_PASSWORD,Env:NUTRIFIT_DB_USER,Env:NUTRIFIT_MYSQL_INTEGRATION,Env:NUTRIFIT_CATALOG_FIXTURES -ErrorAction SilentlyContinue
}
```

Thêm đối số cache nêu ở bước 2 vào lệnh mvn nếu cần. Các biến credential của shell chỉ dùng cho lần kiểm thử này; không in chúng ra terminal.
Tomcat/IDE phải nhận NUTRIFIT_DB_USER/NUTRIFIT_DB_PASSWORD trong tiến trình riêng của nó theo [README-JAVA](../../README-JAVA.md); không cần các công cụ thiết lập ban đầu để chạy WAR.
Các test hiện giữ nguyên 94 trường hợp đọc; CRUD/HTTP sau login vẫn cần Auth và tài khoản thử nghiệm được xác nhận.
