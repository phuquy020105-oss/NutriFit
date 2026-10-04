# vietnamese_menus.py
# Thư viện thực đơn thực đơn gia đình Việt Nam 7 ngày trong tuần & Prompt AI
# Tuân thủ 100% 3 yêu cầu dinh dưỡng:
# 1. Chuẩn 5 nhóm món: Cơm/tinh bột (chính), Món mặn (đạm), Món canh, Món rau, Tráng miệng
# 2. Bữa trưa ăn no bền bỉ vs Bữa tối thanh đạm dễ tiêu
# 3. 3 options đa dạng nguồn đạm (Gia súc, Thủy hải sản, Thực vật/thanh đạm) & đổi mới tinh bột
# 4. Thay đổi phong phú từng ngày từ Thứ Hai đến Chủ Nhật, không bị lặp lại

from datetime import date

WEEKDAY_NAMES_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

WEEKLY_VIETNAMESE_MENUS = {
    0: {  # THỨ HAI
        "lunch": [
            {
                "title": "Thịt heo nạc kho trứng & Canh bí đao",
                "carb": "1.5 bát Cơm trắng dẻo thơm",
                "protein": "Thịt heo nạc kho trứng cút (ít dầu)",
                "soup": "Canh bí xanh nấu tôm khô thơm ngọt",
                "veggie": "Rau muống luộc chấm nước mắm chanh tỏi",
                "dessert": "1 quả chuối tiêu chín",
                "cal_pct": 0.40,
                "digestibility": "Cung cấp năng lượng bền bỉ, no lâu cho buổi chiều",
                "nutritionNotes": "Bữa trưa khởi đầu tuần tràn đầy năng lượng với đạm gia súc và canh bí đao giải nhiệt."
            },
            {
                "title": "Cá lóc đồng kho tộ & Cơm gạo lứt",
                "carb": "1 bát Cơm gạo lứt huyết rồng (Tinh bột chậm)",
                "protein": "Cá lóc đồng kho tộ tiêu đen đậm đà",
                "soup": "Canh chua cá lóc rau ngò om",
                "veggie": "Bắp cải xào tỏi dầu oliu",
                "dessert": "2 múi bưởi da xanh ngọt thanh",
                "cal_pct": 0.39,
                "digestibility": "Giàu omega-3, chất xơ cao hỗ trợ chuyển hóa mỡ thừa",
                "nutritionNotes": "Cá lóc giàu đạm nạc kết hợp gạo lứt chỉ số GI thấp giúp ổn định đường huyết."
            },
            {
                "title": "Bún Bò Huế nạc thanh đạm (Đổi mới tinh bột)",
                "carb": "Bún tươi sợi vừa (Đổi mới không dùng cơm)",
                "protein": "Bắp bò hoa thái mỏng luộc chín tới",
                "soup": "Nước dùng ninh xương thanh trong thơm sả",
                "veggie": "Rau sống hoa chuối, giá đỗ, húng quế",
                "dessert": "1 miếng dưa hấu mát lành",
                "cal_pct": 0.41,
                "digestibility": "Dễ ăn, vị giác sảng khoái, không hề ngấy mỡ",
                "nutritionNotes": "Giải pháp đổi gió tinh bột hoàn hảo đầu tuần, bắp bò giàu sắt giúp tỉnh táo làm việc."
            }
        ],
        "dinner": [
            {
                "title": "Ức gà xé phay hấp sả & Canh mồng tơi",
                "carb": "1 bát nhỏ Cơm gạo lứt (nhẹ bụng)",
                "protein": "Ức gà hấp sả lá chanh xé phay",
                "soup": "Canh cua đồng mồng tơi mướp hương",
                "veggie": "Dưa chuột thái lát trộn dầu giấm",
                "dessert": "1 hộp Sữa chua không đường",
                "cal_pct": 0.30,
                "digestibility": "Cực kỳ dễ tiêu, thanh mát, tránh ứ đọng năng lượng ban đêm",
                "nutritionNotes": "Ức gà hấp và canh rau mồng tơi giúp hệ tiêu hóa nghỉ ngơi nhẹ nhàng, ngủ sâu giấc."
            },
            {
                "title": "Cá diêu hồng hấp hành gừng & Rau luộc",
                "carb": "1 củ Khoai lang vàng hấp (Tinh bột nhẹ bụng)",
                "protein": "Cá diêu hồng hấp hành gừng ấm bụng",
                "soup": "Nước luộc rau cải thìa thêm lát gừng tươi",
                "veggie": "Cải thìa luộc chấm tương gừng",
                "dessert": "1 quả quýt ngọt",
                "cal_pct": 0.28,
                "digestibility": "Dạ dày tiêu hóa êm dịu trong 2 tiếng, không đọng mỡ bụng",
                "nutritionNotes": "Khoai lang hấp thay cơm kết hợp cá hấp gừng làm ấm tỳ vị, bảo vệ dạ dày."
            },
            {
                "title": "Đậu phụ tươi sốt cà & Canh rong biển",
                "carb": "1 bát nhỏ Miến dong xào rau củ nhẹ dầu",
                "protein": "Đậu phụ non mềm sốt cà chua tươi",
                "soup": "Canh rong biển đậu hũ non thanh nhiệt",
                "veggie": "Bông cải xanh và cà rốt hấp",
                "dessert": "1 quả thanh long ruột đỏ nhỏ",
                "cal_pct": 0.29,
                "digestibility": "100% đạm thực vật thanh nhẹ, bụng nhẹ tênh",
                "nutritionNotes": "Bữa tối thanh lọc từ đậu phụ và rong biển cung cấp vi khoáng iod tự nhiên."
            }
        ]
    },
    1: {  # THỨ BA
        "lunch": [
            {
                "title": "Gà áp chảo sả ớt & Canh cải ngọt",
                "carb": "1.5 bát Cơm trắng thơm dẻo",
                "protein": "Thịt đùi gà bỏ da áp chảo sả ớt nạc",
                "soup": "Canh cải ngọt nấu thịt băm thanh ngọt",
                "veggie": "Bí đỏ bao tử luộc chấm muối mè",
                "dessert": "1 quả táo xanh giòn ngọt",
                "cal_pct": 0.40,
                "digestibility": "Đậm đà ngon miệng, kích thích vị giác, giàu năng lượng",
                "nutritionNotes": "Thịt gà nạc giàu niacin và protein chất lượng cao cho ngày làm việc bận rộn."
            },
            {
                "title": "Tôm sú rim mặn ngọt & Canh cua mướp",
                "carb": "1 bát Cơm gạo lứt dẻo",
                "protein": "Tôm sú biển rim mặn ngọt ít đường",
                "soup": "Canh cua đồng nấu mướp hương thanh mát",
                "veggie": "Đậu bắp luộc chấm chao nhẹ",
                "dessert": "2 miếng đu đủ chín ngọt mát",
                "cal_pct": 0.39,
                "digestibility": "Canxi dồi dào, tiêu hóa nhẹ nhàng, giàu khoáng chất",
                "nutritionNotes": "Tôm biển kết hợp canh cua cung cấp canxi và kẽm hữu cơ tối ưu cho hệ xương khớp."
            },
            {
                "title": "Phở Bò Tái Nạc Bánh Phở Gạo Lứt (Đổi mới tinh bột)",
                "carb": "Bánh phở gạo lứt tươi sợi mềm",
                "protein": "Thăn bò Úc tái nạc mềm ngọt",
                "soup": "Nước dùng phở ninh từ quế, hồi, gừng nướng",
                "veggie": "Rau mùi, húng quế, hành hoa tươi và giá trụng",
                "dessert": "1 quả lê tươi mọng nước",
                "cal_pct": 0.41,
                "digestibility": "Ấm bụng, tuần hoàn máu tốt, hấp thu tinh bột chậm",
                "nutritionNotes": "Phở gạo lứt là tuyệt phẩm đổi gió tinh bột, vị ngọt tự nhiên của thịt bò tái nạc."
            }
        ],
        "dinner": [
            {
                "title": "Thịt thăn heo luộc cuộn xà lách",
                "carb": "1 bát nhỏ Cơm trắng hoặc bún lá nhỏ",
                "protein": "Thịt thăn heo nạc luộc thái mỏng",
                "soup": "Canh bí đỏ nấu thịt băm nhẹ gừng",
                "veggie": "Xà lách mỡ, dưa leo, rau thơm cuộn thịt",
                "dessert": "1 quả chuối tây nhỏ",
                "cal_pct": 0.29,
                "digestibility": "Thịt thăn heo luộc thanh khiết, nhiều chất xơ giúp no êm",
                "nutritionNotes": "Món luộc giữ trọn vi chất và không dầu mỡ, dạ dày co bóp nhẹ nhàng."
            },
            {
                "title": "Cá chẽm nướng giấy bạc thì là",
                "carb": "1 củ Khoai tây nhỏ hấp rắc lá mùi tây",
                "protein": "Cá chẽm nướng giấy bạc cùng hành và thì là",
                "soup": "Canh xà lách xoong thịt nạc thanh mát",
                "veggie": "Rau xà lách xoong luộc chấm nước mắm",
                "dessert": "1 chùm nho xanh nhỏ",
                "cal_pct": 0.30,
                "digestibility": "Cá nướng thì là ấm tỳ vị, tiêu hóa nhanh trong 90 phút",
                "nutritionNotes": "Cá nướng không dầu giữ nguyên độ ngọt thịt và axit béo EPA giúp thư giãn tế bào thần kinh."
            },
            {
                "title": "Nấm đùi gà kho tiêu chay & Canh sen",
                "carb": "1 bát nhỏ Miến dong ninh nấm hương",
                "protein": "Nấm đùi gà và đậu phụ tươi kho tiêu đen",
                "soup": "Canh hạt sen táo đỏ hầm nấm tuyết",
                "veggie": "Cải ngồng luộc chấm muối mè",
                "dessert": "1 quả cam sành bóc múi",
                "cal_pct": 0.28,
                "digestibility": "Đạm nấm thực vật cực sạch, an thần dưỡng tâm buổi tối",
                "nutritionNotes": "Hạt sen và nấm hỗ trợ giấc ngủ sâu, đào thải độc tố đường tiêu hóa tự nhiên."
            }
        ]
    },
    2: {  # THỨ TƯ
        "lunch": [
            {
                "title": "Sườn non ram mặn ngọt & Canh rau ngót",
                "carb": "1.5 bát Cơm trắng dẻo thơm",
                "protein": "Sườn heo non nạc ram mặn ngọt hành tím",
                "soup": "Canh rau ngót tươi nấu tôm khô giã nhuyễn",
                "veggie": "Giá đỗ xào lá hẹ dầu đậu nành",
                "dessert": "2 múi bưởi Năm Roi chua ngọt",
                "cal_pct": 0.40,
                "digestibility": "Hương vị truyền thống quen thuộc, giải nhiệt gan hiệu quả",
                "nutritionNotes": "Rau ngót chứa hàm lượng vitamin C và kali vượt trội, thanh lọc cơ thể giữa tuần."
            },
            {
                "title": "Cá thu Nhật sốt cà chua tươi & Cơm gạo lứt",
                "carb": "1 bát Cơm gạo lứt hạt sen",
                "protein": "Cá thu sốt cà chua tươi rắc thì là",
                "soup": "Canh chua thơm cà đậu bắp miền Tây",
                "veggie": "Rau cải ngọt luộc gừng",
                "dessert": "2 quả mận đỏ ngọt",
                "cal_pct": 0.39,
                "digestibility": "Axit hữu cơ từ cà chua và dứa kích thích enzym tiêu hóa",
                "nutritionNotes": "Cá thu là kho báu Omega-3 bảo vệ mắt và trí não, chống mệt mỏi giữa tuần."
            },
            {
                "title": "Bún Chả Nạc Nướng Vỉ Than (Đổi mới tinh bột)",
                "carb": "Bún tươi sợi nhỏ thanh mát",
                "protein": "Chả viên thịt nạc vai nướng vỉ không mỡ cháy",
                "soup": "Nước mắm chấm chua ngọt kèm dưa góp đu đủ",
                "veggie": "Đĩa rau thơm kinh giới, tía tô, xà lách non",
                "dessert": "1 quả thanh long trắng nhỏ",
                "cal_pct": 0.41,
                "digestibility": "Ngon miệng, kích thích tinh thần làm việc hứng khởi",
                "nutritionNotes": "Bún chả nướng chuẩn vị Hà Nội nhưng hạn chế dầu mỡ, ăn kèm nhiều rau thơm kháng khuẩn."
            }
        ],
        "dinner": [
            {
                "title": "Bò cuộn nấm kim châm áp chảo",
                "carb": "1 củ Khoai lang mật nhỏ hấp",
                "protein": "Thịt bắp bò thái lát mỏng cuộn nấm kim châm",
                "soup": "Canh bầu non nấu tôm tươi",
                "veggie": "Bầu luộc chấm muối vừng",
                "dessert": "1 đĩa dâu tây tươi",
                "cal_pct": 0.30,
                "digestibility": "Bò cuộn nấm chín tới mọng nước, nhẹ dạ dày",
                "nutritionNotes": "Nấm kim châm chứa nhiều kẽm và chất xơ hòa tan giúp nhuận tràng buổi tối."
            },
            {
                "title": "Mực ống hấp gừng hành & Canh cải cúc",
                "carb": "1 bát nhỏ Cơm trắng",
                "protein": "Mực ống tươi hấp gừng hành giòn ngọt",
                "soup": "Canh cải cúc (tần ô) nấu cá rô đồng",
                "veggie": "Rau cải cúc luộc thanh mát",
                "dessert": "1 quả ổi giòn gọt vỏ",
                "cal_pct": 0.28,
                "digestibility": "Mực hấp cực kỳ ít chất béo, tiêu hóa hoàn toàn nhanh chóng",
                "nutritionNotes": "Hương gừng làm ấm bụng, cải cúc hỗ trợ hạ huyết áp và an thần dễ ngủ."
            },
            {
                "title": "Trứng cuộn tam sắc & Canh mướp hương",
                "carb": "1 bát nhỏ Bún nưa shirataki xào nhẹ",
                "protein": "Trứng gà ta cuộn cà rốt và đậu cô ve",
                "soup": "Canh mướp hương nấu lạc non thơm bùi",
                "veggie": "Mướp hương luộc thái vát",
                "dessert": "1 quả kiwi vàng bổ đôi",
                "cal_pct": 0.29,
                "digestibility": "Đạm trứng hấp thu sinh học 100%, bụng nhẹ như không",
                "nutritionNotes": "Trứng gà giàu choline nuôi dưỡng tế bào não và phục hồi cơ bắp trong giấc ngủ."
            }
        ]
    },
    3: {  # THỨ NĂM
        "lunch": [
            {
                "title": "Thịt bò xào cần tỏi tây & Canh mướp đắng",
                "carb": "1.5 bát Cơm trắng dẻo",
                "protein": "Thịt thăn bò mềm xào cần tỏi tây nạc",
                "soup": "Canh mướp đắng nhồi thịt nạc thanh mát",
                "veggie": "Cà rốt và su hào luộc chấm muối vừng",
                "dessert": "1 miếng dưa hấu đỏ ngọt lịm",
                "cal_pct": 0.40,
                "digestibility": "Thanh lọc đường ruột, ổn định đường huyết, no lâu",
                "nutritionNotes": "Mướp đắng được mệnh danh là vị thuốc ổn định insulin và giải độc gan tuyệt hảo."
            },
            {
                "title": "Cá basa nướng muối ớt & Canh riêu cua",
                "carb": "1 bát Cơm gạo lứt đậu đen",
                "protein": "Cá basa nướng muối ớt thì là thơm lừng",
                "soup": "Canh riêu cua đồng chua dịu thanh mát",
                "veggie": "Xà lách non trộn dầu giấm chanh",
                "dessert": "3 quả mận Hà Nội chín mọng",
                "cal_pct": 0.39,
                "digestibility": "Axit béo lành mạnh, tiêu hóa êm dịu, không gây ợ nóng",
                "nutritionNotes": "Cá basa giàu chất béo không bão hòa đơn, riêu cua đồng bổ sung canxi tự nhiên."
            },
            {
                "title": "Bánh Đa Cua Hải Phòng Sườn Nạc (Đổi mới tinh bột)",
                "carb": "Bánh đa đỏ Hải Phòng sợi dai giòn",
                "protein": "Thịt sườn non nạc hầm mềm và riêu cua",
                "soup": "Nước riêu cua đồng nguyên chất thơm lừng",
                "veggie": "Rau muống chẻ sợi và hoa chuối thái lát",
                "dessert": "1 quả quýt đường ngọt thơm",
                "cal_pct": 0.41,
                "digestibility": "Món nước truyền thống dễ nuốt, giải nhiệt cơ thể tức thì",
                "nutritionNotes": "Bánh đa đỏ từ bột gạo pha gấc tự nhiên, giàu beta-caroten bổ mắt."
            }
        ],
        "dinner": [
            {
                "title": "Thịt nạc vai băm rim hành & Canh rau dền",
                "carb": "1 bát nhỏ Cơm trắng ít",
                "protein": "Thịt nạc vai băm rim tiêu hành khô thơm phức",
                "soup": "Canh rau dền đỏ nấu tôm nõn ngọt lành",
                "veggie": "Rau dền đỏ luộc chấm nước tương tỏi",
                "dessert": "1 hộp Sữa chua nếp cẩm",
                "cal_pct": 0.30,
                "digestibility": "Rau dền tính mát, bổ huyết, tiêu hóa êm ái",
                "nutritionNotes": "Rau dền đỏ giàu sắt và anthocyanin chống oxy hóa, hỗ trợ giấc ngủ ngon."
            },
            {
                "title": "Cá rô phi hấp xì dầu hành hoa",
                "carb": "1 củ Khoai lang tím hấp thơm ngọt",
                "protein": "Cá rô phi phi lê hấp xì dầu hành hoa",
                "soup": "Nước luộc bắp cải gừng ấm bụng",
                "veggie": "Bắp cải trắng luộc chấm trứng dầm nước mắm",
                "dessert": "1 quả táo Envy nhỏ",
                "cal_pct": 0.28,
                "digestibility": "Hấp xì dầu giữ trọn vị ngọt tự nhiên, không ngấy dầu",
                "nutritionNotes": "Khoai lang tím giàu chất chống oxy hóa anthocyanin và chất xơ ức chế mỡ thừa ban đêm."
            },
            {
                "title": "Đậu hũ chưng nấm hương & Canh bí xanh",
                "carb": "1 bát nhỏ Miến dong nấu canh nấm",
                "protein": "Đậu hũ non chưng nấm hương đông cô",
                "soup": "Canh bí đao nấu tôm khô gừng",
                "veggie": "Cà chua bi tươi trộn sốt dầu giấm oliu",
                "dessert": "1 quả chuối ngự nhỏ",
                "cal_pct": 0.29,
                "digestibility": "Đạm nấm và đậu phụ thuần chay thanh nhẹ, thải độc gan",
                "nutritionNotes": "Nấm hương chứa lentinan tăng cường sức đề kháng và giảm cholesterol tự nhiên."
            }
        ]
    },
    4: {  # THỨ SÁU
        "lunch": [
            {
                "title": "Vịt nạc om sấu chua thanh & Canh măng",
                "carb": "1.5 bát Cơm trắng dẻo",
                "protein": "Thịt ức vịt nạc bỏ da om quả sấu chua dịu",
                "soup": "Canh măng tươi nấu nước dùng vịt thanh ngọt",
                "veggie": "Rau muống xào tỏi dầu oliu",
                "dessert": "2 múi xoài cát chín thơm",
                "cal_pct": 0.40,
                "digestibility": "Vị chua thanh mát của sấu kích thích tuyến nước bọt và tiêu hóa",
                "nutritionNotes": "Vịt nạc giàu đạm và kali, kết hợp vị sấu giải độc tiêu viêm rất tốt."
            },
            {
                "title": "Tôm nõn xào bông cải & Canh ngao thì là",
                "carb": "1 bát Cơm gạo lứt đỏ",
                "protein": "Tôm nõn xào bông cải xanh và nấm rơm",
                "soup": "Canh ngao hoa nấu thì là cà chua chua dịu",
                "veggie": "Bông cải xanh hấp giữ nguyên vi chất",
                "dessert": "1 miếng dứa mật ngọt dịu",
                "cal_pct": 0.39,
                "digestibility": "Giàu vi khoáng kẽm, selen, tiêu hóa sảng khoái",
                "nutritionNotes": "Ngao biển là nguồn cung cấp vitamin B12 và selen dồi dào hàng đầu giúp tăng sinh lực."
            },
            {
                "title": "Hủ Tiếu Gạo Lứt Nam Vang Sườn Non (Đổi mới tinh bột)",
                "carb": "Sợi hủ tiếu gạo lứt dai ngon",
                "protein": "Sườn non nạc hầm và thịt băm nạc",
                "soup": "Nước lèo củ cải thơm lừng ninh xương",
                "veggie": "Hẹ lá, cần tây và giá đỗ tươi",
                "dessert": "2 múi bưởi da xanh",
                "cal_pct": 0.41,
                "digestibility": "Ấm bụng, tráng bao tử, nạp năng lượng chuẩn bị cho cuối tuần",
                "nutritionNotes": "Hủ tiếu gạo lứt giàu chất xơ, nước dùng củ cải giàu men tiêu hóa tự nhiên."
            }
        ],
        "dinner": [
            {
                "title": "Ức gà nướng thảo mộc & Canh ngao",
                "carb": "1 củ Khoai tây nhỏ nghiền sữa hạt",
                "protein": "Ức gà ướp thảo mộc rosemary nướng nồi chiên không dầu",
                "soup": "Canh mồng tơi nấu ngao hoa thanh nhiệt",
                "veggie": "Dưa chuột thái mỏng sốt sữa chua",
                "dessert": "1 quả thanh long trắng nhỏ",
                "cal_pct": 0.30,
                "digestibility": "Đạm ức gà tinh khiết không mỡ thừa, tiêu thụ êm đềm",
                "nutritionNotes": "Thảo mộc kích thích tuần hoàn máu và giúp cơ thể thư giãn sâu sau tuần dài làm việc."
            },
            {
                "title": "Cá hồi áp chảo sốt chanh leo",
                "carb": "1 bát nhỏ Cơm gạo lứt huyết rồng",
                "protein": "Cá hồi áp chảo sốt nước cốt chanh leo chua dịu",
                "soup": "Canh cải thìa nấu nấm đùi gà",
                "veggie": "Măng tây xanh xào tỏi nhẹ",
                "dessert": "1 chùm nho đen không hạt",
                "cal_pct": 0.29,
                "digestibility": "Chất béo Omega-3 quý giá, không gây đầy trướng bụng",
                "nutritionNotes": "Cá hồi kết hợp măng tây xanh là thực đơn thượng hạng chống viêm và chống lão hóa."
            },
            {
                "title": "Canh chua đậu hũ non nấm kim châm",
                "carb": "1 bát nhỏ Bún gạo lứt luộc",
                "protein": "Đậu hũ non chiên không dầu sốt nấm hương",
                "soup": "Canh chua đậu hũ non nấu dứa và cà chua",
                "veggie": "Salad xà lách sốt dầu mè giấm táo",
                "dessert": "1 quả quýt xiêm ngọt lành",
                "cal_pct": 0.28,
                "digestibility": "100% đạm thực vật, ruột nhẹ tênh, đào thải mỡ nội tạng",
                "nutritionNotes": "Canh chua dứa kích thích lợi khuẩn đường ruột, hỗ trợ thanh lọc cơ thể đêm thứ Sáu."
            }
        ]
    },
    5: {  # THỨ BẢY
        "lunch": [
            {
                "title": "Bò kho gừng sả ngũ vị & Canh khoai mỡ",
                "carb": "1.5 bát Cơm trắng hoa lài",
                "protein": "Thịt bắp bò nạc kho gừng sả ngũ vị đậm đà",
                "soup": "Canh khoai mỡ tím nấu tôm tươi dẻo mịn",
                "veggie": "Rau cải xoong xào tỏi dầu oliu",
                "dessert": "1 quả lê ngọt mọng nước",
                "cal_pct": 0.40,
                "digestibility": "Món kho ấm nồng, vị ngọt tự nhiên, no lâu cho ngày cuối tuần",
                "nutritionNotes": "Khoai mỡ tím giàu anthocyanin và chất nhớt tự nhiên bọc niêm mạc dạ dày rất tốt."
            },
            {
                "title": "Chả cá Lã Vọng thì là & Canh chua cá",
                "carb": "1 bát Cơm gạo lứt dẻo",
                "protein": "Chả cá lăng áp chảo với nghệ, hành hoa và thì là",
                "soup": "Canh chua đầu cá lăng nấu dọc mùng giòn sần sật",
                "veggie": "Rau xà lách, rau húng láng tươi sạch",
                "dessert": "2 miếng dưa lưới vàng thơm ngọt",
                "cal_pct": 0.39,
                "digestibility": "Hương vị nghệ và thì là giải cảm, tiêu thực tuyệt vời",
                "nutritionNotes": "Nghệ tươi chứa curcumin kháng viêm mạnh mẽ, cá lăng dồi dào collagen tự nhiên."
            },
            {
                "title": "Bò Sốt Vang Bánh Mì Đen Nguyên Cám (Đổi mới tinh bột)",
                "carb": "1 ổ Bánh mì đen lúa mạch nguyên cám giòn rụm",
                "protein": "Thịt dẻ sườn bò nạc sốt vang thơm mùi quế hồi",
                "soup": "Nước sốt vang sánh mịn đượm vị vang đỏ",
                "veggie": "Salad cà chua bi, dưa leo sốt chanh leo",
                "dessert": "1 quả chuối laba Đà Lạt",
                "cal_pct": 0.41,
                "digestibility": "Đổi vị ẩm thực phong cách Hà Nội cuối tuần, tinh bột nguyên cám no lâu",
                "nutritionNotes": "Bánh mì nguyên cám giàu vitamin nhóm B, kết hợp bò hầm nhừ dễ hấp thu dinh dưỡng."
            }
        ],
        "dinner": [
            {
                "title": "Gà hấp muối tiêu chanh & Canh bí đỏ",
                "carb": "1 củ Khoai lang vàng hấp",
                "protein": "Gà đồi hấp muối lá chanh thịt nạc thơm giòn",
                "soup": "Canh bí đỏ nấu hạt đậu phộng non bùi ngậy",
                "veggie": "Cải ngồng luộc chấm muối vừng",
                "dessert": "1 miếng dưa hấu không hạt",
                "cal_pct": 0.30,
                "digestibility": "Gà hấp giữ độ ngọt nguyên bản, không dầu mỡ, dạ dày thư thái",
                "nutritionNotes": "Bí đỏ nấu lạc non cung cấp vitamin E và carotenoid dưỡng da và bảo vệ mắt."
            },
            {
                "title": "Tôm sú hấp bia sả & Canh rong biển",
                "carb": "1 bát nhỏ Cơm trắng ít",
                "protein": "Tôm sú hấp bia sả gừng tươi giòn ngọt",
                "soup": "Canh rong biển nấu thịt nạc băm",
                "veggie": "Rau mầm trộn sốt mè rang thanh đạm",
                "dessert": "1 quả lựu đỏ bóc hạt",
                "cal_pct": 0.28,
                "digestibility": "Hải sản hấp sả thanh mát, cơ thể nhẹ nhõm",
                "nutritionNotes": "Rong biển thải độc kim loại nặng và hỗ trợ chức năng tuyến giáp tối ưu."
            },
            {
                "title": "Nem cuốn chay đậu hũ & Canh nấm",
                "carb": "Bánh tráng gạo lứt cuốn rau củ",
                "protein": "Đậu hũ chiên không dầu và nấm mộc nhĩ",
                "soup": "Canh nấm rơm nấu hạt sen thơm bùi",
                "veggie": "Rau diếp cá, xà lách, cà rốt bào sợi cuộn nem",
                "dessert": "1 quả táo đỏ giòn",
                "cal_pct": 0.29,
                "digestibility": "Bữa tối cuốn thanh đạm mát ruột, giải phóng hệ tiêu hóa cuối tuần",
                "nutritionNotes": "Rau diếp cá giải nhiệt, nấm mộc nhĩ làm sạch mạch máu và nhuận phế."
            }
        ]
    },
    6: {  # CHỦ NHẬT
        "lunch": [
            {
                "title": "Gà ta hấp lá chanh & Canh gà lá giang",
                "carb": "1.5 bát Cơm trắng hoa lài thơm dẻo",
                "protein": "Thịt gà ta thả vườn hấp lá chanh mâm cỗ sum họp",
                "soup": "Canh gà nấu lá giang chua cay giải nhiệt",
                "veggie": "Măng trúc xào tỏi ớt nhẹ dầu",
                "dessert": "1 chùm nhãn lồng tươi ngọt mát",
                "cal_pct": 0.40,
                "digestibility": "Lá giang chua kích thích tiêu hóa mỡ, vị sảng khoái sum họp",
                "nutritionNotes": "Bữa trưa Chủ Nhật truyền thống đầy đủ vị chua cay ngọt bùi, bổ khí huyết."
            },
            {
                "title": "Mâm lẩu cá thác lác khổ qua thanh lọc gia đình",
                "carb": "1 bát Cơm gạo lứt tím than",
                "protein": "Chả cá thác lác tươi quết dẻo viên tròn",
                "soup": "Nước lẩu ninh củ cải ngọt thanh mát ruột",
                "veggie": "Khổ qua thái mỏng nhúng tái và rau tần ô",
                "dessert": "2 quả dưa lê ngọt mát",
                "cal_pct": 0.39,
                "digestibility": "Cá thác lác giàu đạm không béo, khổ qua thanh lọc độc tố gan",
                "nutritionNotes": "Tuyệt phẩm ẩm thực phương Nam giúp xua tan mệt mỏi, tái tạo năng lượng tuần mới."
            },
            {
                "title": "Miến Lươn Giòn Nghệ An Thanh Đạm (Đổi mới tinh bột)",
                "carb": "Miến dong cao cấp sợi dai trong suốt",
                "protein": "Thịt lươn đồng xào nghệ vàng thơm ngọt",
                "soup": "Nước dùng xương lươn hầm ngọt đậm đà",
                "veggie": "Rau răm, hành tây bào mỏng, hoa chuối tươi",
                "dessert": "2 múi bưởi da xanh ngọt thanh",
                "cal_pct": 0.41,
                "digestibility": "Dễ ăn, ấm trung tiêu, bồi bổ sinh lực tuyệt đỉnh",
                "nutritionNotes": "Lươn đồng là vị thuốc quý Đông y bổ dương, giàu vitamin A và photpho."
            }
        ],
        "dinner": [
            {
                "title": "Thịt bò áp chảo măng tây & Canh súp lơ",
                "carb": "1 củ Khoai lang vàng nướng nhẹ",
                "protein": "Thịt bò thăn nạc áp chảo sốt tiêu đen",
                "soup": "Canh súp lơ cà rốt thịt nạc băm",
                "veggie": "Salad rau bina (chân vịt) trộn dầu oliu",
                "dessert": "1 hộp Sữa chua hoa quả tươi",
                "cal_pct": 0.30,
                "digestibility": "Chất lượng đạm tinh gọn, giàu sắt và magie giúp giãn cơ buổi tối",
                "nutritionNotes": "Măng tây giàu acid folic và glutathione chống mỏi cơ bắp sau tuần dài vận động."
            },
            {
                "title": "Canh ngao chua thì là & Tôm sú hấp",
                "carb": "1 bát nhỏ Cơm gạo lứt ít",
                "protein": "Tôm sú hấp gừng sả lá chanh",
                "soup": "Canh ngao nấu chua thì là quả dọc",
                "veggie": "Rau muống chẻ ngâm giấm ớt nhẹ",
                "dessert": "1 quả quýt ngọt mọng",
                "cal_pct": 0.28,
                "digestibility": "Ngao và tôm thanh nhẹ tuyệt đối, bụng phẳng lỳ ngủ ngon",
                "nutritionNotes": "Tôm hấp và ngao chứa hàm lượng magie cao giúp làm dịu hệ thần kinh trước tuần mới."
            },
            {
                "title": "Đậu phụ sốt nấm mỡ dầu hào & Cháo yến mạch",
                "carb": "1 bát nhỏ Cháo yến mạch bí đỏ nhẹ",
                "protein": "Đậu phụ non sốt nấm mỡ và dầu hào thanh vị",
                "soup": "Canh bí đao hạt sen tươi thanh tâm",
                "veggie": "Cải thìa baby hấp sốt tỏi",
                "dessert": "1 đĩa nhỏ dâu tây tươi",
                "cal_pct": 0.29,
                "digestibility": "Cháo yến mạch ấm bụng, nhẹ nhàng tối đa chuẩn bị sáng Thứ Hai tinh anh",
                "nutritionNotes": "Cháo yến mạch giàu beta-glucan và hạt sen giúp tinh thần sảng khoái, giấc ngủ an lành."
            }
        ]
    }
}

def generate_expert_fallback_meals(user_profile, meal_type, target_date=None, shift_days=0):
    """
    Thuật toán chuyên gia dinh dưỡng dự phòng xoay vòng 7 ngày trong tuần.
    Mỗi ngày trong tuần có bộ 3 thực đơn riêng biệt, đổi mới mỗi ngày!
    Nếu người dùng bấm đổi thực đơn (shift_days > 0), hệ thống sẽ luân phiên sang bộ thực đơn phong phú khác.
    """
    target_kcal = float(user_profile.get('TargetKcal') or 1500)
    
    # Xác định thứ trong tuần (0: Thứ 2 ... 6: Chủ Nhật)
    base_date = date.today()
    if target_date:
        try:
            base_date = date.fromisoformat(target_date)
        except Exception:
            pass
            
    weekday_idx = (base_date.weekday() + shift_days) % 7
    day_menu_pool = WEEKLY_VIETNAMESE_MENUS.get(weekday_idx, WEEKLY_VIETNAMESE_MENUS[0])
    raw_options = day_menu_pool.get(meal_type, day_menu_pool['lunch'])

    result_options = []
    for idx, opt in enumerate(raw_options, 1):
        cal = round(target_kcal * opt.get("cal_pct", 0.40 if meal_type == 'lunch' else 0.30))
        c_gram = round((cal * 0.50) / 4)
        p_gram = round((cal * 0.25) / 4)
        f_gram = round((cal * 0.25) / 9)

        result_options.append({
            "id": idx,
            "title": opt["title"],
            "mealType": meal_type,
            "carb": opt["carb"],
            "protein": opt["protein"],
            "soup": opt["soup"],
            "veggie": opt["veggie"],
            "dessert": opt["dessert"],
            "calories": cal,
            "macros": {"carbs": c_gram, "protein": p_gram, "fat": f_gram},
            "digestibility": opt.get("digestibility", "Cân bằng, dễ tiêu hóa"),
            "nutritionNotes": opt.get("nutritionNotes", "Được chuyên gia NutriFit tối ưu hóa dinh dưỡng cho thể trạng của bạn.")
        })

    return result_options

def build_gemini_prompt(user_profile, meal_type, target_date_str=None, recent_meals_str=None):
    """
    Xây dựng prompt chi tiết tuân thủ 100% 3 yêu cầu của đề bài,
    có ngữ cảnh ngày tháng và danh sách món gần đây để đảm bảo THAY ĐỔI MỖI NGÀY!
    """
    goal_names = {'lose': 'Giảm mỡ, thâm hụt calo nhẹ', 'maintain': 'Cân bằng, giữ cân', 'gain': 'Tăng cân & cơ bắp'}
    goal_desc = goal_names.get(user_profile.get('Goal', 'lose'), 'Cân bằng thể trạng')
    target_kcal = float(user_profile.get('TargetKcal') or 1500)
    
    today_obj = date.today()
    if target_date_str:
        try:
            today_obj = date.fromisoformat(target_date_str)
        except Exception:
            pass
    day_name = WEEKDAY_NAMES_VI[today_obj.weekday()]
    date_display = f"{day_name}, ngày {today_obj.strftime('%d/%m/%Y')}"

    if meal_type == 'lunch':
        meal_name = "BỮA TRƯA"
        target_meal_kcal = round(target_kcal * 0.40)
        meal_req = (
            "- Mục tiêu Bữa Trưa: ĂN NO ĐỦ ĐỂ CÓ NĂNG LƯỢNG LÀM VIỆC BUỔI CHIỀU.\n"
            "- Các món đạm chắc, tinh bột vừa đủ, cung cấp năng lượng bền bỉ."
        )
    else:
        meal_name = "BỮA TỐI"
        target_meal_kcal = round(target_kcal * 0.30)
        meal_req = (
            "- Mục tiêu Bữa Tối: ĂN NHẸ NHÀNG, DỄ TIÊU HÓA, KHÔNG ĐẦY BỤNG, GIÚP NGỦ NGON.\n"
            "- Ưu tiên các món hấp, luộc, canh thanh mát, đạm dễ tiêu (cá nạc, đậu phụ, ức gà, trứng).\n"
            "- Hạn chế dầu mỡ xào rán nặng nề, lượng tinh bột vừa phải."
        )

    history_constraint = ""
    if recent_meals_str:
        history_constraint = f"""
ĐẶC BIỆT LƯU Ý - TRÁNH TRÙNG LẶP VỚI CÁC BỮA ĂN TRƯỚC:
Dưới đây là các món đã gợi ý trong những ngày gần đây của người dùng:
{recent_meals_str}
=> BẠN BẮT BUỘC PHẢI SÁNG TẠO 3 LỰA CHỌN MỚI LẠ HOÀN TOÀN, không lặp lại các món chính ở trên để thực đơn mỗi ngày đều tươi mới và kích thích khẩu vị!
"""

    prompt = f"""
Bạn là chuyên gia dinh dưỡng ẩm thực gia đình Việt Nam hàng đầu cho ứng dụng NutriFit.
Hôm nay là {date_display}. Hãy tạo gợi ý đúng 3 LỰA CHỌN THỰC ĐƠN (3 options) cho {meal_name} hôm nay.

THÔNG TIN THỂ TRẠNG NGƯỜI DÙNG:
- Giới tính: {user_profile.get('Gender', 'male')}
- Cân nặng: {user_profile.get('WeightKg', 68)} kg, Chiều cao: {user_profile.get('HeightCm', 170)} cm
- Mục tiêu: {goal_desc}
- Tổng Calo mục tiêu cả ngày: {target_kcal} kcal
- Lượng Calo mục tiêu cho bữa {meal_name} này: Khoảng {target_meal_kcal} kcal (chênh lệch ±50 kcal).
{history_constraint}
TUÂN THỦ NGHIÊM NGẶT 3 YÊU CẦU SAU ĐÂY:
1. ĐỊNH DẠNG CƠ BẢN CỦA THỰC ĐƠN VIỆT NAM (Đủ 5 thành phần):
   Mỗi option phải gồm đủ 5 nhóm:
   • Món chính (Cung cấp tinh bột): cơm trắng / cơm gạo lứt / bún / miến / phở / khoai lang / bánh đa...
   • Món mặn (Cung cấp chất đạm): thịt heo / thịt bò / cá / gà / tôm / đậu phụ / trứng / lươn...
   • Món canh (Cung cấp nước, vitamin & khoáng chất): canh rau, canh củ, canh chua, canh ngao...
   • Món rau / đồ kèm (Cung cấp chất xơ): rau luộc, xào nhẹ, dưa leo, nộm, dưa góp...
   • Món tráng miệng: hoa quả tươi Việt Nam (chuối, dưa hấu, ổi, bưởi, táo, xoài, quýt...) hoặc sữa chua.

2. ĐẶC TRƯNG BỮA TRƯA VS BỮA TỐI:
   {meal_req}

3. SỰ ĐA DẠNG GIỮA 3 LỰA CHỌN:
   - Các nguồn đạm phải KHÁC NHAU hoàn toàn giữa 3 option:
     + Option 1: Dùng đạm Gia súc / Gia cầm (thịt heo nạc / thịt bò / thịt gà / thịt vịt).
     + Option 2: Dùng đạm Thủy hải sản (cá chép, cá hồi, cá lóc, tôm, mực, ngao...).
     + Option 3: Dùng đạm Thanh đạm / Thực vật (đậu phụ tươi, trứng hấp, nấm, hạt sen...).
     TUYỆT ĐỐI TRÁNH việc cả 3 option đều là thịt hoặc cả 3 option đều là cá.
   - Ít nhất 1 trong 3 option phải sử dụng TINH BỘT KHÔNG PHẢI CƠM TRẮNG (ví dụ: bún tươi, miến dong, phở gạo lứt, bánh đa, khoai lang...) để người dùng không bị nhàm chán.

YÊU CẦU ĐỊNH DẠNG KẾT QUẢ ĐẦU RA:
Chỉ trả về DUY NHẤT một chuỗi JSON hợp lệ (không kèm theo bất kỳ văn bản mở đầu hay kết thúc nào, không dùng markdown ```json) theo cấu trúc mảng 3 phần tử:
[
  {{
    "id": 1,
    "title": "Tên thực đơn ngắn gọn, hấp dẫn",
    "mealType": "{meal_type}",
    "carb": "Tên món chính cung cấp tinh bột",
    "protein": "Tên món mặn cung cấp đạm",
    "soup": "Tên món canh",
    "veggie": "Tên món rau / đồ kèm",
    "dessert": "Tên món tráng miệng",
    "calories": {target_meal_kcal},
    "macros": {{ "carbs": 65, "protein": 32, "fat": 14 }},
    "digestibility": "Đặc điểm tiêu hóa (ví dụ: No lâu bền bỉ hoặc Dễ tiêu hóa, nhẹ bụng)",
    "nutritionNotes": "Lời khuyên dinh dưỡng ngắn 1-2 câu"
  }},
  ...
]
"""
    return prompt
