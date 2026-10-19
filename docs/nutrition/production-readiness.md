# Production readiness — educational60release2026-10-20

Tiêu chuẩn hiện hành do chủ dự án chấp nhận MATCHED/CALCULATED/ESTIMATED có căn cứ cho đồ án, không đòi VERIFIED hoặc kiểm nghiệm phòng thí nghiệm. Xem [bàn giao](demo60-release.md) và [manifest](../../database/staging/food-quality-v1/release/final-manifest.json).

Technicaldata/portions/assets/benchmark/tests/transaction/idempotency/restore gates đã có bằng chứng thực thi. Manifest đánh dấu PRODUCTION_READY chỉ sau finalize kiểm tra đủ bằng chứng. **Productionwrite vẫn CHƯA được phép** cho đến khi chủ dự án phê duyệt đúng SHA256 manifest một lần. Không chạy import chỉ vì code đãpush hoặc Renderhealthy.

47missing trong source-only audit không được tuyên bố đã đo/VERIFIED; release dùng ước tính riêng và giữ audit/provenance gốc. Bảng users/subscription/payment/mealentries không nằm trong DML migration. Catalogbackup+24DDL đãrestorelocal, không phảifulluserdata backup. Recovery sau có phát sinh nhật ký mới cần kế hoạch riêng, không restore chồngDBproduction.

Giới hạn: chưa chạy authenticatedE2E production, chưa go-live60data, một số mục tiêu cao chưa có tổ hợp gần năng lượng với3suấtchuẩn; hiển thị số thực và cảnh báo, không tự tăng/giảm suất.
