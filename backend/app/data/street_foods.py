"""Món ăn đường phố (TV4): kho 36 món, truy vấn, lọc và thuật toán gợi ý.

Dữ liệu khớp bảng StreetFoodDish trong create_database.sql.

Cột: title, price_vnd, calories, carbs_g, protein_g, fat_g, meal_type,
     protein_desc, carb_desc, soup_desc, veggie_desc
"""
from sqlalchemy import text

from app.extensions import db

STREET_FOODS = [
    ('Cơm tấm sườn bì chả', 45000, 620, 75, 32, 21, 'lunch', 'Sườn cốt lết nướng, bì heo, chả trứng hấp', 'Cơm tấm trắng thơm', 'Nước mắm chua ngọt, chén canh súp nóng', 'Đồ chua củ cải cà rốt, dưa leo'),
    ('Cơm gà xối mỡ đùi góc tư', 50000, 680, 82, 36, 24, 'lunch', 'Đùi gà chiên da giòn rụm', 'Cơm chiên cà chua hạt tơi', 'Chén nước súp thanh', 'Xà lách, cà chua, dưa leo'),
    ('Cơm sườn non ram mặn', 40000, 580, 72, 28, 20, 'lunch', 'Sườn non heo kho ram đậm đà', 'Cơm trắng dẻo', 'Canh rau ngót thịt bằm', 'Dưa leo, rau sống'),
    ('Cơm cá lóc kho tộ', 42000, 530, 70, 30, 14, 'lunch', 'Cá lóc đồng kho tiêu thơm nức', 'Cơm trắng', 'Canh chua cá bông điên điển', 'Rau muống luộc chấm nước cá'),
    ('Cơm thịt kho tàu trứng cút', 40000, 610, 70, 26, 25, 'lunch', 'Thịt ba rọi kho mềm rục, trứng cút', 'Cơm trắng nóng hổi', 'Canh bí đao tôm khô', 'Dưa giá, cải chua bóp xổi'),
    ('Cơm gà luộc xé phay Hội An', 45000, 510, 68, 33, 12, 'lunch', 'Thịt gà ta thả vườn luộc xé sợi', 'Cơm nấu nước luộc gà vàng ươm', 'Nước súp lòng gà', 'Hành tây ngâm chua, rau răm, gỏi bắp cải'),
    ('Cơm bò lúc lắc khoai tây', 55000, 640, 65, 34, 28, 'lunch', 'Thịt thăn bò áp chảo bơ tỏi mềm ngọt', 'Cơm chiên tỏi hoặc cơm trắng', 'Chén nước tương ớt cắt lát', 'Xà lách xoong, cà chua, khoai tây chiên'),
    ('Phở bò tái nạm truyền thống', 50000, 520, 65, 30, 15, 'all', 'Thịt bò tái mềm, nạm gầu giòn béo', 'Bánh phở mềm dai', 'Nước dùng hầm xương bò thanh trong thơm quế hồi', 'Rau quế, ngò gai, chanh ớt, giá trụng'),
    ('Phở gà ta lá chanh', 45000, 480, 64, 29, 12, 'all', 'Thịt gà ta da giòn thái miếng rắc lá chanh', 'Bánh phở mềm', 'Nước dùng gà hầm thanh ngọt', 'Hành hoa, rau mùi, quẩy giòn'),
    ('Bún bò Huế thập cẩm', 50000, 580, 66, 32, 20, 'all', 'Bắp bò hoa, giò heo, chả cua, huyết', 'Bún sợi to dai giòn', 'Nước dùng sả ớt mắm ruốc dậy mùi', 'Bắp chuối bào, giá đỗ, rau muống chẻ, chanh tươi'),
    ('Bún chả Hà Nội nướng than', 45000, 560, 68, 28, 19, 'lunch', 'Chả viên nướng xém cạnh, chả miếng ba chỉ', 'Bún lá tươi', 'Nước mắm chấm dấm tỏi ớt ấm nóng kèm đu đủ giòn', 'Xà lách, tía tô, kinh giới tươi ngon'),
    ('Hủ tiếu Nam Vang sườn tôm', 45000, 490, 62, 26, 15, 'all', 'Tôm thẻ tươi, thịt bằm, sườn non, tim cật, trứng cút', 'Hủ tiếu dai Nam Vang', 'Nước lèo xương ống hầm củ cải ngọt thanh', 'Cần tàu, hẹ lá, giá đỗ sống'),
    ('Bún riêu cua đồng bắp bò', 40000, 480, 60, 26, 16, 'all', 'Riêu cua đồng béo ngậy, bắp bò tái, đậu hũ chiên', 'Bún tươi', 'Nước dùng cà chua thanh mát vị dấm bỗng', 'Rau muống chẻ, hoa chuối, kinh giới'),
    ('Bún ốc chuối đậu Hà Nội', 45000, 470, 62, 24, 15, 'all', 'Ốc nhồi giòn sần sật, thịt ba chỉ, đậu hũ rán', 'Bún tươi sợi nhỏ', 'Nước ốc nấu chua cay nghệ vàng thơm lừng', 'Tía tô thái chỉ, rau thơm các loại'),
    ('Bánh canh ghẹ miền Tây', 55000, 510, 60, 28, 17, 'all', 'Thịt ghẹ xé tươi ngọt, chả cá thu', 'Sợi bánh canh bột lọc dai dẻo', 'Nước dùng sền sệt nấu gạch ghẹ đỏ au', 'Hành ngò, chanh ớt tiêu xay'),
    ('Mì Quảng tôm thịt trứng', 40000, 530, 65, 27, 18, 'lunch', 'Tôm rim đậm đà, thịt ba chỉ kho nghệ, trứng cút', 'Sợi mì Quảng vàng dẻo', 'Nước nhưỡng xăm xắp béo ngậy', 'Bánh tráng mè nướng giòn, bắp chuối, đậu phộng rang'),
    ('Bún cá rô đồng rau cải', 40000, 440, 58, 26, 11, 'dinner', 'Cá rô đồng chiên giòn rụm và thịt cá rim', 'Bún sợi nhỏ', 'Nước dùng xương cá hầm thanh ngọt', 'Rau cải xanh cay nồng, thì là'),
    ('Bún mắm miền Tây sặc sỡ', 55000, 610, 68, 34, 21, 'lunch', 'Tôm sú, mực tươi, heo quay giòn da, cá lóc phi lê', 'Bún tươi', 'Nước lèo nấu mắm cá linh cá sặc thơm nồng', 'Cà tím, bông súng, rau đắng, kèo nèo, bắp chuối'),
    ('Bánh canh cua chả cá', 45000, 490, 59, 27, 16, 'all', 'Thịt cua xé, chả cá chiên, giò heo', 'Bánh canh bột gạo mềm', 'Nước súp sền sệt nóng hổi', 'Ngò rí, tiêu sọ, quẩy'),
    ('Bún thịt nướng chả giò Sài Gòn', 40000, 530, 70, 25, 17, 'lunch', 'Thịt nạc dăm ướp sả nướng mè, chả giò chiên giòn', 'Bún tươi', 'Nước mắm chua ngọt tỏi ớt', 'Rau sống, xà lách, dưa leo, mỡ hành, đậu phộng'),
    ('Bánh mì chảo ốp la xíu mại pate', 35000, 490, 55, 22, 20, 'lunch', '2 trứng gà ốp la lòng đào, xíu mại sốt cà, pate béo', '1 ổ bánh mì đặc ruột giòn rụm', 'Nước sốt cà chua tiêu đen chấm bánh mì', 'Dưa leo, ngò gai'),
    ('Bánh mì kẹp thịt nguội pate', 25000, 420, 52, 18, 16, 'lunch', 'Chả lụa, giò thủ, thịt xá xíu, pate gan', 'Ổ bánh mì giòn tan', 'Nước sốt tương ớt đậm đà', 'Đồ chua, dưa leo, ớt sừng cay'),
    ('Bánh mì bò kho thơm lừng', 45000, 560, 63, 28, 21, 'all', 'Nạm bò hầm mềm gân, cà rốt ngọt', 'Ổ bánh mì nóng giòn', 'Nước sốt bò kho cay nồng hoa hồi quế chi', 'Rau quế, ngò gai, muối tiêu chanh'),
    ('Hủ tiếu khô xá xíu sườn non', 45000, 510, 68, 27, 14, 'all', 'Thịt xá xíu xắt lát mỏng, sườn non mềm ngọt', 'Sợi hủ tiếu dai trộn sốt hắc xì dầu', 'Chén canh súp tôm thịt hầm thanh', 'Hẹ lá, cần tây, giá đỗ'),
    ('Bún đậu mắm tôm thập cẩm', 50000, 590, 66, 31, 23, 'lunch', 'Đậu hũ rán vàng giòn, chả cốm chiên, thịt chân giò luộc', 'Bún lá ép miếng', 'Mắm tôm Thanh Hóa đánh sủi bọt tắc ớt', 'Dưa leo, kinh giới, tía tô tươi'),
    ('Mì trộn xá xíu lòng đào', 40000, 540, 72, 26, 17, 'lunch', 'Thịt xá xíu rim óng ánh, trứng lòng đào dẻo', 'Mì gói trụng trộn sốt chua ngọt đặc biệt', 'Chén nước súp hành lá', 'Cải thìa luộc, tóp mỡ giòn rụm'),
    ('Miến xào cua bể tay cầm', 60000, 510, 64, 28, 15, 'lunch', 'Thịt cua bể tươi bóc sẵn ngọt lịm', 'Sợi miến dong xào tơi mềm không dính', 'Nước tương tỏi ớt chấm kèm', 'Cà rốt, nấm mèo, cần tây, giá đỗ'),
    ('Bánh hỏi heo quay giòn bì', 45000, 550, 67, 24, 22, 'lunch', 'Thịt ba chỉ quay lớp da nổ giòn tan', 'Bánh hỏi thoa mỡ hành lá thơm phức', 'Nước mắm tỏi ớt chua ngọt', 'Rau thơm, xà lách, dưa leo cuốn bánh tráng'),
    ('Bánh xèo miền Tây giòn rụm', 40000, 520, 58, 22, 23, 'lunch', 'Tôm nõn, thịt ba rọi, giá đỗ, đậu xanh', 'Vỏ bánh xèo bột nghệ mỏng giòn rụm', 'Nước mắm chấm tỏi ớt cà rốt', 'Rau cải xanh, xà lách, lá lốt, đọt xoài non'),
    ('Cháo sườn sụn hạt sen', 35000, 390, 52, 22, 10, 'dinner', 'Sườn sụn giòn sần sật ninh nhừ, hạt sen bùi béo', 'Cháo gạo tẻ nấu sánh mịn nhuyễn', 'Tiêu bắc, hành hoa, quẩy nóng giòn', 'Gừng tươi thái chỉ giữ ấm bụng'),
    ('Cháo gà ta đậu xanh', 35000, 420, 54, 25, 11, 'dinner', 'Thịt gà xé sợi trộn tiêu muối ớt', 'Cháo đậu xanh nở búp ngọt bùi', 'Hành lá, tía tô, tiêu đen xay nhuyễn', 'Rau răm tươi cắt nhỏ'),
    ('Miến gà đồi nấu nấm hương', 45000, 430, 56, 27, 10, 'dinner', 'Thịt gà đồi luộc da giòn thịt săn chắc', 'Sợi miến dong trong suốt dai mềm', 'Nước dùng gà hầm nấm hương ngọt ngào', 'Hành lá, ngò gai, lá chanh non'),
    ('Bánh cuốn nóng thịt bằm mộc nhĩ', 35000, 410, 58, 18, 12, 'dinner', 'Thịt heo nạc bằm xào nấm mèo hành tây, chả lụa', 'Bánh tráng tay mỏng mướt tráng nóng', 'Nước mắm dấm ớt tỏi ấm nhẹ', 'Rau giá trụng, rau thơm, dưa leo xắt mỏng'),
    ('Cháo cá lóc rau đắng miền Tây', 40000, 380, 50, 24, 9, 'dinner', 'Phi lê cá lóc đồng hấp chín tới ngọt thịt', 'Cháo hoa nấu nở bung hạt', 'Nước mắm mặn ớt hiểm chấm cá', 'Đĩa rau đắng tươi mát, giá sống'),
    ('Cháo hàu sữa hạt sen', 45000, 410, 53, 23, 11, 'dinner', 'Hàu sữa tươi béo ngậy xào hành phi thơm phức', 'Cháo gạo sánh thơm hạt sen', 'Hành lá, ngò rí, tiêu xay mịn', 'Gừng sợi ấm bụng dễ tiêu'),
    ('Súp cua gà xé nấm tuyết', 35000, 320, 38, 22, 9, 'dinner', 'Thịt cua tươi, ức gà xé nhuyễn, nấm tuyết, trứng cút', 'Súp sánh mịn nấu từ nước dùng gà', 'Dầu mè, tiêu sọ, giấm tiều thơm lừng', 'Ngò rí tươi thái nhỏ'),
]


VALID_MEAL_TYPES = ("all", "breakfast", "lunch", "dinner")


def _row_to_dish(r):
    return {
        "id": r.DishId, "title": r.Title, "price_vnd": int(r.PriceVnd),
        "calories": float(r.Calories), "carbs_g": float(r.CarbsGrams),
        "protein_g": float(r.ProteinGrams), "fat_g": float(r.FatGrams),
        "meal_type": r.MealType, "protein_desc": r.ProteinDesc, "carb_desc": r.CarbDesc,
        "soup_desc": r.SoupDesc, "veggie_desc": r.VeggieDesc,
    }


def list_dishes(meal_type=None, max_price=None, max_kcal=None, keyword=None):
    rows = db.session.execute(text(
        "SELECT DishId, Title, PriceVnd, Calories, CarbsGrams, ProteinGrams, FatGrams, MealType, "
        "ProteinDesc, CarbDesc, SoupDesc, VeggieDesc FROM StreetFoodDish ORDER BY DishId"
    )).fetchall()
    dishes = [_row_to_dish(r) for r in rows]

    if meal_type and meal_type != "all":
        dishes = [d for d in dishes if d["meal_type"] in (meal_type, "all")]
    if max_price is not None:
        dishes = [d for d in dishes if d["price_vnd"] <= max_price]
    if max_kcal is not None:
        dishes = [d for d in dishes if d["calories"] <= max_kcal]
    if keyword:
        k = keyword.strip().lower()
        dishes = [d for d in dishes if k in d["title"].lower()]
    return dishes


def score_dish(dish, budget, max_kcal):
    """Điểm 0-100 = 40% đạm + 40% độ vừa calo + 20% độ rẻ.

    - Đạm: tỷ lệ calo đến từ protein (protein_g x 4 / calories), đạt tối đa ở 30%.
    - Vừa calo: tốt nhất khi dùng 70%-100% calo tối đa của bữa; thấp hơn thì giảm dần.
    - Rẻ: càng rẻ so với ngân sách càng điểm cao (nhẹ).
    """
    protein_share = dish["protein_g"] * 4 / dish["calories"] if dish["calories"] else 0
    protein_score = min(1.0, protein_share / 0.30)

    ratio = dish["calories"] / max_kcal
    kcal_score = 1.0 if ratio >= 0.7 else ratio / 0.7

    price_score = 1.0 - 0.5 * (dish["price_vnd"] / budget)

    return round(100 * (0.4 * protein_score + 0.4 * kcal_score + 0.2 * price_score), 1), protein_share


def rank_dishes(dishes, budget, max_kcal, meal_type="all", limit=5):
    """Lọc theo bữa, ngân sách, calo rồi xếp hạng. Thuần Python nên dễ test."""
    ranked = []
    for d in dishes:
        if meal_type != "all" and d["meal_type"] not in (meal_type, "all"):
            continue
        if d["price_vnd"] > budget or d["calories"] > max_kcal:
            continue
        score, protein_share = score_dish(d, budget, max_kcal)
        reasons = []
        if protein_share >= 0.25:
            reasons.append("Giàu đạm")
        if d["calories"] <= max_kcal * 0.85:
            reasons.append("Còn dư calo cho bữa phụ")
        if d["price_vnd"] <= budget * 0.7:
            reasons.append("Giá tiết kiệm")
        ranked.append({**d, "score": score, "reasons": reasons})

    ranked.sort(key=lambda x: (-x["score"], x["price_vnd"]))
    return ranked[:limit]


def recommend(budget, max_kcal, meal_type="all", limit=5):
    """Trả về (kết_quả, lỗi)."""
    try:
        budget, max_kcal, limit = int(budget), float(max_kcal), int(limit)
    except (TypeError, ValueError):
        return None, "Ngân sách, calo tối đa hoặc limit không hợp lệ."
    if budget <= 0 or max_kcal <= 0:
        return None, "Ngân sách và calo tối đa phải lớn hơn 0."
    if meal_type not in VALID_MEAL_TYPES:
        return None, "meal_type phải là all, breakfast, lunch hoặc dinner."
    limit = max(1, min(limit, 20))

    items = rank_dishes(list_dishes(), budget, max_kcal, meal_type, limit)
    return {"budget": budget, "max_kcal": max_kcal, "meal_type": meal_type,
            "count": len(items), "items": items}, None



def seed_street_foods_if_empty():
    """Nạp STREET_FOODS vào bảng StreetFoodDish nếu bảng đang trống. Trả về số dòng đã thêm."""
    count = db.session.execute(text("SELECT COUNT(*) FROM StreetFoodDish")).scalar()
    if count:
        return 0
    sql = text(
        "INSERT INTO StreetFoodDish (Title, PriceVnd, Calories, CarbsGrams, ProteinGrams, FatGrams, "
        "MealType, ProteinDesc, CarbDesc, SoupDesc, VeggieDesc) VALUES "
        "(:t, :p, :c, :cb, :pr, :f, :m, :pd, :cd, :sd, :vd)"
    )
    for r in STREET_FOODS:
        db.session.execute(sql, dict(t=r[0], p=r[1], c=r[2], cb=r[3], pr=r[4], f=r[5],
                                     m=r[6], pd=r[7], cd=r[8], sd=r[9], vd=r[10]))
    db.session.commit()
    return len(STREET_FOODS)
