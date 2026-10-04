# 🥗 NUTRIFIT - HỆ THỐNG THEO DÕI DINH DƯỠNG, THỂ TRẠNG & GỢI Ý THỰC ĐƠN VIỆT

> **Đồ án / Dự án**: Ứng dụng Quản trị Dinh dưỡng & Vận động Thể chất Cá
> nhân hóa\
> **Kiến trúc hiện tại**: Web SPA + Flask REST API + MySQL + Gemini AI\
> **Triển khai**: GitHub + MySQL Cloud + Render

------------------------------------------------------------------------

## 📌 MỤC LỤC

1.  Giới Thiệu Tổng Quan & Công Nghệ Sử Dụng
2.  Cấu Trúc Thư Mục & Chú Thích Chi Tiết Từng File
3.  Quy Trình Cài Đặt & Chạy Local
4.  Cấu Hình Biến Môi Trường
5.  Triển Khai Website Lên Internet
6.  Các Lỗi Thường Gặp
7.  Hướng Dẫn Chi Tiết Các Chức Năng Nghiệp Vụ

------------------------------------------------------------------------

## 🌟 GIỚI THIỆU TỔNG QUAN & CÔNG NGHỆ SỬ DỤNG

NutriFit là ứng dụng web hỗ trợ người dùng theo dõi thể trạng, nhu cầu
năng lượng, hoạt động luyện tập và xây dựng gợi ý thực đơn Việt Nam phù
hợp với mục tiêu cá nhân.

Hệ thống được phát triển theo mô hình Client - Server - Database. Phiên
bản hiện tại sử dụng **MySQL** và đã được chuẩn hóa để có thể chạy local
cũng như triển khai thành website trên Internet.

### 🛠️ Kiến trúc công nghệ

-   **Front-end**: HTML5, CSS3, JavaScript, Tailwind CSS, Lucide Icons,
    Chart.js.
-   **Back-end**: Python 3, Flask, Flask-CORS, REST API, Gunicorn.
-   **Kết nối CSDL**: `mysql-connector-python`.
-   **Database**: MySQL; local sử dụng `NutriFitDB`, production sử dụng
    MySQL Cloud.
-   **AI**: Google Gemini API kết hợp dữ liệu thực đơn Việt Nam.
-   **Triển khai**: GitHub + MySQL Cloud + Render.

### 🌐 Kiến trúc khi triển khai

``` text
Người dùng
    │
    ▼
Website NutriFit
    │
    ▼
Flask / Gunicorn
    │
    ├──────────────► Gemini API
    │
    ▼
MySQL Cloud
```

------------------------------------------------------------------------

## 📁 CẤU TRÚC THƯ MỤC & CHÚ THÍCH CHI TIẾT TỪNG FILE

``` text
FoodAndHealth_Deploy/
│
├── index.html
├── api.js
├── server.py
├── vietnamese_menus.py
├── storage.js
├── schema_cloud.sql
├── requirements.txt
├── Procfile
├── README.md
├── DEPLOY.md
├── feature.txt
├── .gitignore
│
└── meal-suggest/
    ├── index.html
    ├── app.js
    ├── single-dishes.js
    ├── full-menus.js
    ├── ai-rank.js
    └── api-client.js
```

  -----------------------------------------------------------------------
  Tên file / thư mục                  Vai trò
  ----------------------------------- -----------------------------------
  `index.html`                        Giao diện SPA chính: đăng nhập/đăng
                                      ký, khảo sát thể trạng, dashboard,
                                      thực đơn, món lẻ và luyện tập.

  `api.js`                            Client REST API. Bản deploy dùng
                                      `/api` để frontend và backend chạy
                                      cùng domain.

  `server.py`                         Flask backend xử lý tài khoản, hồ
                                      sơ, workout, thống kê, thực đơn,
                                      MySQL và Gemini.

  `vietnamese_menus.py`               Kho và logic thực đơn Việt Nam.

  `schema_cloud.sql`                  Schema MySQL dùng để khởi tạo
                                      database cloud và dữ liệu mặc định.

  `requirements.txt`                  Các package Python cần cài đặt.

  `Procfile`                          Cấu hình khởi động production bằng
                                      Gunicorn.

  `meal-suggest/`                     Module món lẻ mua ngoài và thuật
                                      toán xếp hạng.

  `storage.js`                        Dữ liệu/logic frontend được giữ
                                      trong kiến trúc hiện tại.

  `feature.txt`                       Đặc tả yêu cầu nghiệp vụ của đồ án.

  `DEPLOY.md`                         Tài liệu triển khai.

  `.gitignore`                        Loại `.venv`, `.env`, cache và file
                                      hệ thống khỏi GitHub.

  `README.md`                         Tài liệu tổng quan và bàn giao dự
                                      án.
  -----------------------------------------------------------------------

> `schema.sql` SQL Server cũ và `run.bat` dành cho Windows không còn cần
> thiết cho bản deploy MySQL.

------------------------------------------------------------------------

## 🚀 QUY TRÌNH CÀI ĐẶT & CHẠY LOCAL

### BƯỚC 1: Chuẩn bị MySQL

Tạo database:

``` sql
CREATE DATABASE NutriFitDB
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

Các bảng chính: `Users`, `UserProfiles`, `Workouts`, `WorkoutLogs`,
`MealSuggestions`.

Hệ thống có 18 bài tập mặc định.

### BƯỚC 2: Tạo môi trường Python

macOS/Linux:

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

``` powershell
python -m venv .venv
.venv\Scripts\activate
```

### BƯỚC 3: Cài thư viện

``` bash
pip install -r requirements.txt
```

### BƯỚC 4: Cấu hình MySQL

macOS/Linux:

``` bash
export MYSQL_HOST='localhost'
export MYSQL_USER='root'
export MYSQL_PASSWORD='YOUR_MYSQL_PASSWORD'
export MYSQL_DATABASE='NutriFitDB'
```

Nếu sử dụng Gemini:

``` bash
export GEMINI_API_KEY='YOUR_GEMINI_API_KEY'
```

### BƯỚC 5: Chạy hệ thống

``` bash
python server.py
```

Mở:

``` text
http://localhost:5000
```

Kiểm tra backend/database:

``` text
http://localhost:5000/api/health
```

Flask phục vụ cả frontend và backend nên không cần chạy frontend riêng ở
port 8000.

------------------------------------------------------------------------

## 🔐 CẤU HÌNH BIẾN MÔI TRƯỜNG

``` text
MYSQL_HOST
MYSQL_PORT
MYSQL_USER
MYSQL_PASSWORD
MYSQL_DATABASE
GEMINI_API_KEY
PORT
```

Không đưa mật khẩu MySQL hoặc Gemini API key lên GitHub. Nếu dùng
`.env`, file này phải nằm trong `.gitignore`.

------------------------------------------------------------------------

## ☁️ TRIỂN KHAI WEBSITE LÊN INTERNET

``` text
GitHub Repository
       │
       ▼
Render Web Service
       │
       ▼
MySQL Cloud
```

### GitHub

Source code được lưu trên GitHub nhưng không chứa `.venv`, `.env`, mật
khẩu database hoặc API key.

### MySQL Cloud

Tạo MySQL online và chạy `schema_cloud.sql`. Lấy `Host`, `Port`,
`Database`, `User`, `Password` để cấu hình cho backend.

### Render

Build Command:

``` text
pip install -r requirements.txt
```

Start Command:

``` text
gunicorn server:app
```

Thêm các Environment Variables của MySQL và Gemini. Sau khi deploy thành
công, website có URL public dạng:

``` text
https://<ten-website>.onrender.com
```

------------------------------------------------------------------------

## 🛠️ CÁC LỖI THƯỜNG GẶP

### 1. `ModuleNotFoundError`

``` bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. MySQL `Access denied`

Kiểm tra `MYSQL_USER`, `MYSQL_PASSWORD`, host, port và quyền database.

### 3. Port 5000 đang được sử dụng trên macOS

``` bash
lsof -nP -iTCP:5000 -sTCP:LISTEN
```

AirPlay Receiver trên macOS có thể sử dụng port 5000.

### 4. `/favicon.ico` trả về 404

Không ảnh hưởng chức năng chính; project chỉ chưa có icon cho tab trình
duyệt.

### 5. Deploy nhưng không kết nối database

Production không sử dụng MySQL `localhost` trên máy cá nhân. Backend
online phải kết nối MySQL Cloud.

------------------------------------------------------------------------

## 📖 HƯỚNG DẪN CHI TIẾT CÁC CHỨC NĂNG NGHIỆP VỤ

### 1. Quản lý tài khoản

-   Tạo tài khoản mới.
-   Đăng nhập.
-   Lưu tài khoản trong MySQL.
-   Bản deploy hash mật khẩu cho tài khoản mới.

### 2. Quản lý thể trạng & hồ sơ sức khỏe

Người dùng nhập/cập nhật giới tính, tuổi, chiều cao, cân nặng, mức vận
động và mục tiêu.

Các chỉ số gồm BMI, BMR, TDEE, calo mục tiêu, Carbs, Protein, Fat, Fiber
và lượng nước khuyến nghị.

### 3. Gợi ý thực đơn Việt

-   Gợi ý bữa trưa và bữa tối.
-   Nhiều lựa chọn cho mỗi bữa.
-   Lưu lựa chọn.
-   Xem lịch sử.
-   Đổi thực đơn.
-   Kết hợp kho thực đơn Việt Nam với Gemini khi API key được cấu hình.

### 4. Món lẻ mua ngoài

Module `meal-suggest` cung cấp dữ liệu các món ăn quen thuộc như phở,
bún, cơm, bánh mì cùng thông tin giá, calo và macro.

Hỗ trợ lọc/xếp hạng món, ngân sách, calo, C-P-F và liên kết tìm quán ăn
phù hợp.

### 5. Luyện tập & vận động

Hệ thống có 18 bài tập mặc định thuộc Cardio, Gym, Thể thao và Yoga/Giãn
cơ.

Người dùng có thể tạo bài tập tùy chỉnh, xóa bài tập do mình tạo, ghi
nhận buổi tập, lưu thời lượng/calo và xem lịch sử hoạt động.

### 6. Thống kê luyện tập

Chart.js trực quan hóa tổng số buổi, tổng thời lượng, tổng calo, số ngày
hoạt động và dữ liệu vận động các ngày gần nhất.

------------------------------------------------------------------------

## 🔒 BẢO MẬT & NGUYÊN TẮC DEPLOY

1.  Không commit mật khẩu MySQL.
2.  Không commit Gemini API key.
3.  Dùng Environment Variables.
4.  Không push `.venv`.
5.  Không push `.env`.
6.  Database production nằm trên cloud.
7.  Production chạy bằng Gunicorn thay cho Flask development server.

------------------------------------------------------------------------

## 🧪 KIỂM TRA HỆ THỐNG

``` text
Trang chủ
   ↓
/api/health
   ↓
Đăng ký
   ↓
Đăng nhập
   ↓
Lưu hồ sơ
   ↓
18 bài tập
   ↓
Ghi nhận tập
   ↓
Thống kê
   ↓
Sinh/chọn thực đơn
   ↓
Lịch sử
```

------------------------------------------------------------------------

## 📌 TRẠNG THÁI PHIÊN BẢN

``` text
SQL Server / PyODBC (phiên bản ban đầu)
                 ↓
MySQL / mysql-connector-python
                 ↓
Flask phục vụ Frontend + API
                 ↓
GitHub
                 ↓
MySQL Cloud + Render
                 ↓
Website public
```

------------------------------------------------------------------------

## 👨‍💻 GHI CHÚ

NutriFit được xây dựng phục vụ mục đích học tập/đồ án và minh họa quy
trình xây dựng hệ thống web có frontend, backend, database, REST API và
thành phần AI.

Các chỉ số dinh dưỡng và gợi ý của ứng dụng mang tính hỗ trợ/tham khảo,
không thay thế tư vấn chuyên môn y tế hoặc dinh dưỡng.
