# Premium Quick Food Logging — contract cho Frontend

Backend: `http://127.0.0.1:5000`. Tất cả request dùng cookie từ đăng nhập hiện có,
`credentials: "include"`; không dùng `X-User-Id`, token tự tạo hoặc trạng thái
Premium trong localStorage làm bằng chứng quyền truy cập.

Ba endpoint dưới đây chỉ dành cho Premium còn hạn. Nhật ký thông thường
`POST /api/nutrition/intake` vẫn dùng được cho FREE như trước.

## 1. Search → người dùng chọn Dish ID

`GET /api/nutrition/quick-food/search?q=cơm%20trắng&limit=10`

`q`: 1–120 ký tự sau khi gom khoảng trắng; `limit`: 1–20 (mặc định 10).
Tìm không phân biệt hoa/thường, hỗ trợ có dấu/không dấu và đ/Đ.
Khớp chính xác đứng trước prefix/substring. Không fuzzy/AI, không tự chọn món,
kể cả chỉ có một kết quả. Tên trùng vẫn trả từng Dish ID để người dùng chọn.

Ví dụ dữ liệu `rice` trong catalog hiện có:

```json
{
  "success": true,
  "data": {
    "query": "cơm trắng", "total": 1, "returned": 1, "requires_selection": true,
    "results": [{
      "dish_id": "rice", "name": "Cơm trắng", "match": "exact",
      "reference_grams": 180.0, "grams": 180.0, "used_reference_grams": true,
      "totals": {"calories": 227.3, "protein": 4.9, "carbs": 50.8, "fat": 0.5, "fiber": 0.7},
      "source": "database", "estimated": true, "fiber_complete": true
    }]
  }
}
```

`total` là số kết quả trước limit; không có món phù hợp trả HTTP 404,
`FOOD_NOT_FOUND`. Chỉ tìm trong dữ liệu active và hợp lệ của MySQL.

## 2. Preview — không ghi dữ liệu

`POST /api/nutrition/quick-food/preview`

```json
{"dish_id": "rice", "grams": 200}
```

Bỏ `grams` hoặc gửi `null`: dùng `reference_grams`. Gram thực tế phải là số
1–2.000 g, tối đa hai chữ số thập phân sau làm tròn, theo giới hạn Food Intake
hiện có; không dùng giới hạn min/max của khẩu phần gợi ý để cấm ghi lượng đã ăn.

```json
{
  "success": true,
  "data": {
    "dish_id": "rice", "name": "Cơm trắng", "reference_grams": 180.0,
    "grams": 200.0, "used_reference_grams": false,
    "totals": {"calories": 252.6, "protein": 5.4, "carbs": 56.4, "fat": 0.6, "fiber": 0.8},
    "source": "database", "estimated": true, "fiber_complete": true
  }
}
```

## 3. Confirm — chỉ ghi sau khi xác nhận đã ăn

`POST /api/nutrition/quick-food/confirm`

```json
{
  "dish_id": "rice", "grams": 200,
  "mealType": "snack", "consumedAt": "2026-10-11T15:30:00+07:00",
  "confirmed": true, "requestId": "a1122334-5566-7788-9900-aabbccddeeff"
}
```

`mealType` mặc định `snack`; nhận `breakfast/lunch/dinner/snack`.
`consumedAt` tùy chọn: ISO datetime có timezone; bỏ trống dùng thời điểm Backend.
`grams` tùy chọn như preview. Frontend nên gửi gram đã hiển thị trong preview.
Không gửi tên thay cho Dish ID, kcal, macro hoặc thông tin Premium.

Response giữ format Food Intake hiện có:

```json
{
  "success": true, "created": true,
  "data": {
    "id": 42, "version": 1, "date": "2026-10-11",
    "consumedAtUtc": "2026-10-11 08:30:00", "mealType": "snack",
    "items": [{"dish_id": "rice", "name": "Cơm trắng", "grams": 200.0}],
    "totals": {"calories": 252.6, "protein": 5.4, "carbs": 56.4, "fat": 0.6, "fiber": 0.8},
    "source": "catalog", "estimated": true, "fiber_complete": true
  }
}
```

Ví dụ confirm lược bớt các field snapshot từng món; `id` là minh họa.
Backend tính lại từ catalog khi ghi lần đầu; preview không khóa dữ liệu.
Response đã lưu là dữ liệu cuối cùng nếu catalog đổi giữa preview và confirm.

HTTP 201 + `created=true` cho lần đầu; retry cùng payload/requestId trả HTTP 200,
`created=false`, cùng nhật ký/snapshot, kể cả reference hoặc catalog đã đổi.
Giữ nguyên payload và requestId khi timeout; không tạo UUID mới cho lần retry.
Một requestId chỉ đại diện một lần ghi; UUID mới là lần ăn mới, không tự chống
hai lần nhập riêng biệt. RequestId dài 16–64 ký tự `[A-Za-z0-9_-]`.

Sau thành công: gọi `GET /api/nutrition/daily?date=<data.date>` để cập nhật
consumed/remaining/logs. `/api/nutrition/summary` vẫn là planned, không phải đã ăn.
Sửa/xóa dùng endpoint cũ với `version`:

- `POST /api/nutrition/intake/{id}/update`: `confirmed`, `mealType`,
  `consumedAt`, `items: [{dish_id, grams}]`, `version`.
- `POST /api/nutrition/intake/{id}/delete`: `{version}`.

Sửa/xóa nhật ký thuộc tài khoản vẫn được phép khi Premium hết hạn.

## Error contract

```json
{"success": false, "code": "PREMIUM_REQUIRED", "message": "Chức năng này cần Premium còn hiệu lực."}
```

| HTTP | Code | Xử lý Frontend |
|---|---|---|
| 401 | AUTH_REQUIRED | Yêu cầu đăng nhập lại |
| 403 | PREMIUM_REQUIRED | FREE, hết hạn hoặc không có thời hạn; hiện nâng cấp |
| 403 | FORBIDDEN | Sai user ID hoặc origin không được phép |
| 503 | PREMIUM_UNAVAILABLE | Chưa có schema quyền Premium hoặc không đọc được; không cho confirm |
| 404 | FOOD_NOT_FOUND | Không có món active/hợp lệ; yêu cầu chọn lại |
| 400 | INVALID_INPUT | Tên/ID/gram/JSON/field không hợp lệ |
| 400 | CONFIRMATION_REQUIRED | Chưa xác nhận đã ăn |
| 409 | IDEMPOTENCY_CONFLICT | Cùng requestId với nội dung khác |
| 409 | INTAKE_DELETED | Retry một nhật ký đã xóa |
| 409 | STALE_INTAKE | Version cũ khi sửa/xóa; tải lại nhật ký |
| 503 | DATABASE_ERROR / FOOD_CATALOG_MIGRATION_REQUIRED / V4_MIGRATION_REQUIRED | Hiện lỗi và cho thử lại an toàn |

Search, preview và confirm đều kiểm tra quyền hiện tại từ DB theo contract Quý:
`SubscriptionStatus == PREMIUM` và `PremiumExpiresAt > UTC now`.
Không cache quyền trong cookie. Hết hạn cả retry confirm cũng bị từ chối;
có thể đọc nhật ký/daily bằng API cũ để kiểm tra lần ghi trước.

## Trạng thái tích hợp

Nhánh hiện tại chưa có các cột Premium của Quý. Adapter fail closed bằng
`PREMIUM_UNAVAILABLE`; không migration, không tự cấp Premium. Backend được
kiểm thử bằng SQLite in-memory có schema quyền giả lập theo contract Quý.
Payment webhook/xác thực thanh toán do Quý phụ trách; không triển khai trong MVP.
Không gọi Gemini, không sửa Frontend, Profile hoặc TargetKcal.

## Kiểm thử Backend

Từ thư mục `backend`, dùng môi trường hiện có:

```powershell
..\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_quick_food.py" -v
..\.venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_*.py"
```

Fixtures dùng SQLite in-memory, mock mail/Gemini; cột Premium chỉ thêm vào DB
test, không sửa models/schema ứng dụng. Lần kiểm chứng MVP: 26 tests mới nằm
trong 270/270 tests PASS (gồm 10 tests DRAFT hiện có); full suite còn được chặn
`pymysql.connect` và kết nối socket ra ngoài trong bộ nhớ. Python syntax và
whitespace đạt. Chưa chạy confirm trên MySQL thật hoặc kiểm thử Frontend.
