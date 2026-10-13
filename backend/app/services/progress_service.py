"""Thống kê 7 ngày gần nhất (TV4) cho biểu đồ của TV2."""
from datetime import date, timedelta

from sqlalchemy import text

from app.extensions import db
from app.services.workout_service import get_goal, parse_date

WEEKDAY_LABELS = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]


def build_week(rows, end_date, days=7):
    """rows: iterable (ngày, số buổi, tổng phút, tổng calo). Ngày không tập trả về 0 để đủ `days` cột."""
    by_day = {}
    for d, sessions, minutes, kcal in rows:
        by_day[parse_date(d)] = (int(sessions or 0), int(minutes or 0), float(kcal or 0))

    result = []
    for i in range(days - 1, -1, -1):
        day = end_date - timedelta(days=i)
        sessions, minutes, kcal = by_day.get(day, (0, 0, 0.0))
        result.append({"date": day.isoformat(), "label": WEEKDAY_LABELS[day.weekday()],
                       "sessions": sessions, "minutes": minutes, "calories": round(kcal, 1)})
    return result


def _pct(value, target):
    return min(100, round(value * 100 / target)) if target else 0


def weekly_stats(user_id, end_date=None, days=7):
    end_date = end_date or date.today()
    start = end_date - timedelta(days=days - 1)
    rows = db.session.execute(text(
        "SELECT LoggedDate, COUNT(*), SUM(DurationMinutes), SUM(CaloriesBurned) "
        "FROM WorkoutLogs WHERE UserId = :uid AND LoggedDate BETWEEN :s AND :e "
        "GROUP BY LoggedDate"
    ), {"uid": user_id, "s": start.isoformat(), "e": end_date.isoformat()}).fetchall()

    week = build_week(rows, end_date, days)
    totals = {
        "sessions": sum(d["sessions"] for d in week),
        "minutes": sum(d["minutes"] for d in week),
        "calories": round(sum(d["calories"] for d in week), 1),
        "active_days": sum(1 for d in week if d["sessions"] > 0),
    }
    goal = get_goal(user_id)
    goal_progress = {
        **goal,
        "sessions_pct": _pct(totals["sessions"], goal["weekly_sessions_target"]),
        "calories_pct": _pct(totals["calories"], goal["weekly_calories_target"]),
    }
    return {"from": start.isoformat(), "to": end_date.isoformat(),
            "days": week, "totals": totals, "goal": goal_progress}
