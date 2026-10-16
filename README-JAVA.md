# NUTRIFIT --- HƯỚNG DẪN PHÁT TRIỂN JAVA WEB

> **Tài liệu dành cho các thành viên nhóm NutriFit**\
> Nhánh tích hợp: `develop-java` · Công nghệ: Java 21, Maven, Jakarta
> Servlet 6, JSP, Tomcat 10.1, MySQL, JDBC\
> Cập nhật: 16/10/2026

## 1. Mục tiêu

NutriFit là hệ thống web hỗ trợ quản lý dinh dưỡng và luyện tập. Nhóm
phát triển ứng dụng theo kiến trúc **MVC / Controller → Service → DAO →
MySQL**, giao diện sử dụng **JSP, CSS và JavaScript**.

**Trạng thái hiện tại:** Dự án đã chạy được trên Tomcat, trang JSP mẫu
hoạt động và endpoint `/health/db` đã kết nối MySQL thành công trên máy
tích hợp. **Các chức năng nghiệp vụ chưa được xem là hoàn thành**.

-   Repository: <https://github.com/phuquy020105-oss/NutriFit>
-   Nhánh tích hợp Java: `develop-java`
-   Commit nền tảng JSP đã push: `8b7b341`
-   Database thiết kế: `database/schema.sql` (23 bảng, 24 khóa ngoại
    theo bản thiết kế nhóm)

> **Quan trọng:** Nhánh `main` có thể chứa phiên bản cũ khác công nghệ.
> Khi làm Java Web, **lấy `develop-java` làm nhánh gốc**, không tự merge
> `main` vào nhánh Java.

## 2. Phân công module và nhánh Git

  -----------------------------------------------------------------------
  Nhánh                               Phạm vi chức năng
  ----------------------------------- -----------------------------------
  `feature/java-auth-profile`         Đăng ký, đăng nhập, đăng xuất, hồ
                                      sơ cá nhân

  `feature/java-workout`              Quản lý bài tập và kế hoạch luyện
                                      tập 7 ngày

  `feature/java-nutrition`            Thực phẩm, công thức, Meal Planner,
                                      sở thích ăn uống

  `feature/java-payment-chatbot`      Thanh toán VNPay Sandbox và Chatbot

  `feature/java-dashboard-admin`      Dashboard, chức năng quản trị
  -----------------------------------------------------------------------

Tên thành viên phụ trách từng nhánh cần được nhóm trưởng xác nhận. Người
tích hợp duyệt Pull Request và kiểm thử trên `develop-java`.

## 3. Công cụ cần cài

-   **JDK 21**; kiểm tra `java -version`.
-   **Apache Maven**; kiểm tra `mvn -version`.
-   **Apache Tomcat 10.1.x** (Jakarta Servlet 6).
-   **MySQL Server** và công cụ quản lý như MySQL Workbench.
-   **Git**, VS Code hoặc IDE Java tương đương.

Dự án dùng Maven để quản lý thư viện, trong đó có `mysql-connector-j`.
**Không cần tải JDBC Driver thủ công** nếu `mvn clean package` đóng gói
thành công.

## 4. Lấy source code

Clone repository:

``` bash
git clone https://github.com/phuquy020105-oss/NutriFit.git
cd NutriFit
git fetch origin
git switch develop-java
git pull origin develop-java
```

Nếu bạn được phân công nhánh `feature/java-workout` (thay tên theo
module của mình):

**Nếu nhánh đã tồn tại trên remote:**

``` bash
git fetch origin
git switch --track origin/feature/java-workout
```

Nếu Git báo nhánh local đã tồn tại, chỉ cần:

``` bash
git switch feature/java-workout
```

**Nếu nhánh chưa tồn tại:**

``` bash
git switch -c feature/java-workout develop-java
git push -u origin feature/java-workout
```

Không chạy cả hai cách tạo nhánh cùng lúc.

## 5. Thiết lập MySQL trên máy riêng

Mỗi thành viên phải có MySQL hoạt động tại máy mình và **tự tạo tài
khoản ứng dụng, mật khẩu riêng**.

### 5.1. Tạo schema

Mở `database/schema.sql`, kiểm tra các lệnh `CREATE DATABASE` / `USE` và
chạy bằng MySQL Workbench. Tên database mà cấu hình Java hiện tại sử
dụng là:

``` text
nutrifitdb_java
```

Nếu file SQL tạo database với cách viết hoa khác, kiểm tra tên thực tế
qua `SHOW DATABASES;`. Tránh tự đổi cấu trúc bảng; nếu cần thay đổi
schema, phải thảo luận trước với nhóm.

Kiểm tra:

``` sql
USE nutrifitdb_java;
SHOW TABLES;
```

Theo thiết kế nhóm, dự kiến có **23 bảng**. Các bảng có thể chưa có dữ
liệu mẫu.

### 5.2. Tạo user riêng cho ứng dụng

Đăng nhập MySQL bằng tài khoản có quyền quản trị, chạy SQL sau **sau khi
thay tên user và mật khẩu bằng giá trị riêng của bạn**:

``` sql
CREATE USER IF NOT EXISTS 'nutrifit_app'@'localhost'
IDENTIFIED BY 'THAY_BANG_MAT_KHAU_RIENG';

GRANT SELECT, INSERT, UPDATE, DELETE
ON nutrifitdb_java.* TO 'nutrifit_app'@'localhost';
```

Nếu cần cấp quyền tạo/sửa bảng trong môi trường phát triển, trao đổi với
người phụ trách database; không cấp quyền rộng một cách tùy tiện.

### 5.3. Biến môi trường

Ứng dụng lấy thông tin đăng nhập từ:

-   `NUTRIFIT_DB_USER`
-   `NUTRIFIT_DB_PASSWORD`

**macOS / zsh:**

``` bash
export NUTRIFIT_DB_USER="nutrifit_app"
read -s "NUTRIFIT_DB_PASSWORD?Nhập mật khẩu MySQL: "
echo
export NUTRIFIT_DB_PASSWORD
```

**Windows PowerShell (trong phiên làm việc hiện tại):**

``` powershell
$env:NUTRIFIT_DB_USER = "nutrifit_app"
$secure = Read-Host "Nhap mat khau MySQL" -AsSecureString
$env:NUTRIFIT_DB_PASSWORD = [System.Net.NetworkCredential]::new("", $secure).Password
```

> Không commit mật khẩu, `.env`, `setenv.sh` chứa bí mật, hoặc thông tin
> đăng nhập cá nhân. Không ghi mật khẩu trực tiếp vào
> `DatabaseConfig.java`. Khi khởi động Tomcat từ IDE, cần cấu hình biến
> môi trường trong cấu hình chạy của IDE.

### 5.4. Lưu ý cấu hình kết nối

`DatabaseConfig.java` hiện kết nối tới `127.0.0.1:3306/nutrifitdb_java`.
Nếu MySQL của bạn chạy cổng khác, cần thống nhất cách cấu hình với nhóm
trước khi thay đổi file dùng chung. Không commit thay đổi riêng cho máy
mình vào nhánh tích hợp.

## 6. Build và chạy dự án

Tại thư mục gốc có `pom.xml`:

``` bash
mvn clean package
```

Khi build thành công, file WAR dự kiến nằm tại:

``` text
target/nutrifit.war
```

**macOS (ví dụ Tomcat cài tại `~/tools/apache-tomcat-10.1.61`):**

``` bash
export CATALINA_HOME="$HOME/tools/apache-tomcat-10.1.61"
"$CATALINA_HOME/bin/shutdown.sh"
cp target/nutrifit.war "$CATALINA_HOME/webapps/"
"$CATALINA_HOME/bin/startup.sh"
```

Tomcat phải được khởi động trong môi trường có `NUTRIFIT_DB_USER` và
`NUTRIFIT_DB_PASSWORD`. Nếu đây là lần đầu chạy và Tomcat chưa khởi
động, lệnh `shutdown.sh` có thể báo không có server đang chạy; khi đó có
thể bỏ qua và tiếp tục.

Trên Windows, copy WAR vào thư mục `webapps` của Tomcat rồi dùng
`bin\startup.bat` (với các biến môi trường đã được thiết lập).

**Kiểm tra trên trình duyệt:**

  ----------------------------------------------------------------------------------------------------
  URL                                          Kết quả mong đợi
  -------------------------------------------- -------------------------------------------------------
  `http://localhost:8080/nutrifit/`            Trang JSP mẫu

  `http://localhost:8080/nutrifit/health`      `{"status":"ok","application":"NutriFit"}`

  `http://localhost:8080/nutrifit/health/db`   `{"status":"connected","database":"nutrifitdb_java"}`
  ----------------------------------------------------------------------------------------------------

Nếu `/health/db` lỗi, kiểm tra log Tomcat, thông tin user, password,
cổng MySQL và JDBC Driver trong WAR. **Không gửi mật khẩu lên nhóm chat
hoặc GitHub.**

## 7. Cấu trúc thư mục và quy tắc MVC

``` text
NutriFit/
├── pom.xml
├── database/
│   └── schema.sql
└── src/
    ├── main/
    │   ├── java/com/nutrifit/
    │   │   ├── config/         # Cấu hình kết nối, hạ tầng
    │   │   ├── controller/     # Servlet xử lý HTTP
    │   │   ├── service/        # Logic nghiệp vụ
    │   │   ├── dao/            # Truy vấn MySQL
    │   │   ├── model/          # Entity / đối tượng dữ liệu
    │   │   ├── dto/            # Dữ liệu request/response
    │   │   ├── filter/         # Authentication, authorization
    │   │   └── util/           # Tiện ích dùng chung
    │   └── webapp/
    │       ├── index.jsp
    │       ├── WEB-INF/views/
    │       │   ├── auth/
    │       │   ├── profile/
    │       │   ├── workout/
    │       │   ├── nutrition/
    │       │   ├── payment/
    │       │   ├── chatbot/
    │       │   └── admin/
    │       └── assets/
    │           ├── css/
    │           ├── js/
    │           └── images/
    └── test/java/com/nutrifit/
```

**Luồng xử lý chuẩn:**

`JSP → Servlet (Controller) → Service → DAO → MySQL`

Quy ước:

-   `controller`: nhận request, kiểm tra đầu vào cơ bản, gọi service,
    chuyển tiếp/redirect.
-   `service`: xử lý quy tắc nghiệp vụ, không viết SQL trực tiếp.
-   `dao`: truy vấn SQL bằng JDBC và `PreparedStatement`; đóng tài
    nguyên bằng `try-with-resources`.
-   `model`: bám sát các cột/bảng trong `database/schema.sql`; không tự
    suy đoán tên cột.
-   `dto`: dùng cho dữ liệu form/API khi cần; không bắt buộc mỗi entity
    có DTO.
-   JSP trong `WEB-INF/views` được truy cập qua Servlet, không truy cập
    trực tiếp từ URL.
-   Dùng package gốc `com.nutrifit` và `jakarta.servlet.*` (không dùng
    `javax.servlet.*`).
-   Tách code theo module, tránh sửa các file dùng chung khi chưa trao
    đổi.

> Git không theo dõi thư mục rỗng. Nếu chưa thấy thư mục trên GitHub,
> hãy tạo khi thêm file Java/JSP thực tế.

## 8. Quy ước URL và giao tiếp giữa module

Các đường dẫn dưới đây là **đề xuất cần thống nhất**, chưa khẳng định đã
được triển khai:

  Module              Prefix đề xuất
  ------------------- ----------------------------
  Auth / Profile      `/auth/*`, `/profile/*`
  Workout             `/workouts/*`
  Nutrition           `/nutrition/*`
  Payment             `/payment/*`
  Chatbot             `/chatbot/*`
  Dashboard / Admin   `/dashboard/*`, `/admin/*`

Trước khi code, nhóm cần chốt: URL, phương thức GET/POST, tên form
field/DTO, cách lưu session, phân quyền, giao diện lỗi và các service
dùng chung. Không tạo hai Servlet trùng URL mapping.

**Module Auth & Profile** nên thống nhất sớm cách biểu diễn user đăng
nhập trong session để Workout, Nutrition và Payment có thể sử dụng.

## 9. Quy trình làm việc với Git

Mỗi thành viên chỉ code và push lên **nhánh feature được phân công**.

Trước khi bắt đầu phiên làm việc:

``` bash
git switch feature/java-workout
git status
git fetch origin
git pull --ff-only
```

Thay `feature/java-workout` bằng nhánh của bạn. Để lấy thay đổi mới từ
`develop-java`, chỉ merge/rebase khi đã lưu hoặc commit công việc đang
làm và xử lý xung đột cẩn thận:

``` bash
git fetch origin
git merge origin/develop-java
```

Khi hoàn thành một phần:

``` bash
git status
git add <duong-dan-file-cua-ban>
git commit -m "feat(workout): add workout service"
git push origin feature/java-workout
```

Sau đó mở **Pull Request**:

`feature/java-workout` → `develop-java`

**Không push trực tiếp vào `develop-java` hoặc `main`** nếu không được
người tích hợp cho phép. Không dùng `git push --force` trên nhánh chung.

## 10. Checklist trước khi gửi Pull Request

-   [ ] Code đúng module và đúng nhánh feature.
-   [ ] Không chứa mật khẩu, token, API key hoặc file cấu hình bí mật.
-   [ ] `mvn clean package` chạy thành công.
-   [ ] Không tự ý sửa `database/schema.sql` hoặc `pom.xml` khi chưa
    trao đổi.
-   [ ] JDBC sử dụng `PreparedStatement` và xử lý lỗi phù hợp.
-   [ ] URL Servlet không trùng với module khác.
-   [ ] Chức năng được thử trên máy cá nhân; mô tả cách kiểm tra.
-   [ ] Nếu thay đổi dữ liệu/bảng, ghi rõ yêu cầu migration.
-   [ ] PR nêu mục tiêu, file chính, ảnh giao diện (nếu có), cách test
    và hạn chế còn tồn tại.

## 11. Quy tắc phối hợp nhóm

1.  Thông báo sớm nếu cần sửa **file dùng chung**: `pom.xml`,
    `DatabaseConfig.java`, `database/schema.sql`, filter xác thực, CSS
    toàn cục.
2.  Không đổi tên bảng/cột hoặc quan hệ trong database khi chưa được
    thống nhất.
3.  Không commit file sinh ra khi build (`target/`), file log hoặc dữ
    liệu nhạy cảm.
4.  Nếu có xung đột Git, hỏi người tích hợp trước khi giải quyết các
    thay đổi liên quan đến module khác.
5.  Mỗi PR nên nhỏ, dễ kiểm tra; không gom toàn bộ module thành một
    commit lớn.
6.  Khi báo tiến độ, ghi rõ **đã làm / đang làm / vướng mắc / bước tiếp
    theo**.

## 12. Các mốc triển khai đề xuất

**Mốc A --- Nền tảng:** Java, Maven, Tomcat, MySQL, JDBC, JSP mẫu,
GitHub `develop-java` --- **đã kiểm tra hoạt động trên máy tích hợp**.

**Mốc B --- Phát triển chức năng:** các thành viên xây dựng Model, DAO,
Service, Servlet và JSP trên nhánh riêng.

**Mốc C --- Tích hợp:** review PR, hợp nhất vào `develop-java`, kiểm thử
luồng đăng nhập → sử dụng chức năng → lưu dữ liệu.

**Mốc D --- Hoàn thiện:** kiểm thử phân quyền, dữ liệu, giao diện, lỗi
và chuẩn bị báo cáo/demo.

------------------------------------------------------------------------

**Liên hệ khi gặp lỗi:** gửi ảnh hoặc nội dung lỗi, lệnh đã chạy, hệ
điều hành, phiên bản Java/Maven/Tomcat và nhánh Git đang sử dụng.
**Không gửi mật khẩu hay API key.**
