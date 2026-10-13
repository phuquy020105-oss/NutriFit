"""Bài tập bổ sung (TV4). create_database.sql đã seed 7 bài chuẩn; file này thêm 11 bài
để đủ 18 bài như bản cũ. Lượng calo tính cho khoảng 60-65 kg ở thời lượng ghi kèm."""

# (category_id, workout_name, duration_minutes, calories_burned)
# Nhóm: 1 Cardio, 2 Gym, 3 Thể thao, 4 Yoga & Giãn cơ, 5 Tự chọn
EXTRA_WORKOUTS = [
    (1, 'Đạp xe đường dài', 45, 330),
    (1, 'Đi bộ nhanh', 40, 160),
    (1, 'HIIT tại nhà', 20, 240),
    (1, 'Leo cầu thang', 15, 150),
    (2, 'Tập lưng & tay trước (Gym)', 45, 250),
    (2, 'Tập vai & bụng (Core)', 35, 200),
    (2, 'Hít đất & plank tại nhà', 20, 140),
    (3, 'Cầu lông', 60, 380),
    (3, 'Bóng chuyền', 60, 300),
    (4, 'Yoga Vinyasa năng động', 45, 200),
    (4, 'Giãn cơ trước khi ngủ', 15, 50),
]


def seed_extra_workouts():
    """Thêm các bài còn thiếu (so khớp theo tên, chạy nhiều lần không bị trùng). Trả về số bài đã thêm."""
    from sqlalchemy import text
    from app.extensions import db

    added = 0
    for cat_id, name, minutes, kcal in EXTRA_WORKOUTS:
        exists = db.session.execute(
            text("SELECT 1 FROM Workouts WHERE WorkoutName = :n AND IsCustom = 0"), {"n": name}
        ).first()
        if exists:
            continue
        db.session.execute(
            text("INSERT INTO Workouts (CategoryId, WorkoutName, DurationMinutes, CaloriesBurned, IsCustom) "
                 "VALUES (:c, :n, :d, :k, 0)"),
            {"c": cat_id, "n": name, "d": minutes, "k": kcal},
        )
        added += 1
    db.session.commit()
    return added
