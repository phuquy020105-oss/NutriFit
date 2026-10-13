"""Build curated Vietnamese recipe estimates for the NutriFit STUDENT PROJECT.

The dishes are named examples with plausible ingredient masses and engineering
macros, NOT a nutritional reference database. Re-check before clinical use.
Offline-only; NEVER touches MySQL. Output: setup/seeds/vietnamese_expansion_2026.json.
"""
import json
import hashlib
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'setup/seeds/vietnamese_expansion_2026.json'
BASE = ROOT / 'setup/seeds/nutrition_catalog.json'
# protein, carb, fat in grams per 100 g of assumed edible cooked/prepared ingredient
P = {
 'rice':('Cơm chín',2.7,28.2,.3),'brown_rice':('Cơm gạo lứt chín',2.7,23.5,.9),
 'glutinous':('Xôi chín',3,35,.6),'noodles':('Bún tươi',1.8,25,.2),
 'pho':('Bánh phở chín',2.2,22,.4),'mien':('Miến chín',.3,24,.1),
 'hu_tieu':('Hủ tiếu chín',2.0,24,.3),'mi':('Mì chín',4.2,27,2.2),
 'banh_canh':('Bánh canh chín',2,27,.3),'bread':('Bánh mì',9,50,3),
 'banh_trang':('Bánh tráng',5,71,.4),'flour':('Bột gạo',6,79,.8),
 'corn':('Bắp ngọt chín',3.2,19,1.2),'oat':('Yến mạch',12,59,7),
 'sweet_potato':('Khoai lang',1.6,20,.1),'potato':('Khoai tây',2,20,.1),
 'taro':('Khoai môn',1.5,25,.2),'cassava':('Khoai mì',1.4,38,.3),
 'pork':('Thịt heo nạc chín',25,0,8),'belly':('Ba chỉ chín',15,0,30),
 'ribs':('Sườn heo chín',20,0,19),'beef':('Thịt bò chín',26,0,10),
 'chicken':('Thịt gà chín',27,0,5),'duck':('Thịt vịt chín',24,0,14),
 'frog':('Thịt ếch chín',23,0,3),'eel':('Lươn chín',20,0,9),
 'fish':('Cá nạc chín',21,0,5),'catfish':('Cá da trơn chín',19,0,9),
 'tuna':('Cá ngừ chín',25,0,4),'salmon':('Cá hồi chín',23,0,12),
 'shrimp':('Tôm chín',22,0,2),'squid':('Mực chín',18,1,2),
 'crab':('Thịt cua chín',18,1,2),'clam':('Nghêu/hến chín',13,3,2),
 'oyster':('Hàu chín',9,5,3),'egg':('Trứng',13,1,11),
 'tofu':('Đậu phụ',10,3,5),'mung':('Đậu xanh nấu',7,19,.5),
 'peanut':('Lạc rang',25,15,49),'mushroom':('Nấm chín',3,4,.4),
 'cabbage':('Bắp cải',1.3,5,.1),'bok_choy':('Cải thìa',1.5,2.5,.2),
 'spinach':('Rau bina/cải bó xôi',2.7,3,.4),'mustard':('Cải xanh',2,3,.2),
 'watercress':('Cải xoong',2.3,2.5,.1),'ngot':('Rau ngót',4.2,3,.5),
 'malabar':('Mồng tơi',1.6,3,.2),'jute':('Rau đay',2,3,.2),
 'muong':('Rau muống',2.5,4,.2),'lettuce':('Xà lách',1.4,3,.2),
 'sprouts':('Giá đỗ',3,6,.2),'carrot':('Cà rốt',.8,9,.2),
 'cucumber':('Dưa leo',.7,3,.1),'tomato':('Cà chua',.9,4,.2),
 'onion':('Hành tây',1.1,9,.1),'scallion':('Hành lá',2,7,.2),
 'garlic':('Tỏi',6.4,33,.5),'ginger':('Gừng',1.8,18,.8),
 'lemongrass':('Sả',1.8,25,.5),'herbs':('Rau thơm',2.5,4,.2),
 'pumpkin':('Bí đỏ',1,7,.1),'gourd':('Bí xanh/bầu',.6,4,.1),
 'luffa':('Mướp',.7,4,.1),'bitter':('Khổ qua',1,4,.2),
 'eggplant':('Cà tím',1,6,.2),'broccoli':('Bông cải',2.8,7,.4),
 'green_bean':('Đậu que',2,7,.2),'chayote':('Su su',.8,4,.1),
 'lotus':('Ngó sen/củ sen',1.5,17,.1),'bamboo':('Măng',2.6,5,.3),
 'papaya':('Đu đủ',.5,11,.3),'mango':('Xoài',.8,15,.4),
 'banana':('Chuối',1.1,23,.3),'pineapple':('Dứa',.5,13,.1),
 'orange':('Cam',1,12,.1),'pomelo':('Bưởi',.8,10,.1),
 'avocado':('Bơ',2,9,15),'coconut':('Nước/cùi dừa',.5,5,1),
 'milk':('Sữa',3.3,5,3.3),'yogurt':('Sữa chua',3.5,5,3),
 'sugar':('Đường',0,100,0),'oil':('Dầu ăn',0,0,100),
 'fish_sauce':('Nước mắm',4,3,0),'soy_sauce':('Nước tương',6,5,.1),
 'shrimp_paste':('Mắm tôm',13,2,2),'chili':('Ớt',2,9,.4),
 'tamarind':('Me chua',1,15,.1),'sesame':('Mè/vừng',18,23,50),
 'salt':('Gia vị muối',0,0,0),'water':('Nước dùng/nước',0,0,0),
 'rice_flour':('Bột gạo hấp',2,28,.4),'tapioca':('Bột năng chín',.2,32,.1),
 'shallot':('Hành tím',1.2,17,.1), 'turmeric':('Nghệ',2,12,.7),
 'celery':('Cần tây',.7,3,.2),'seaweed':('Rong biển',2,5,.3),
 'chives':('Hẹ',3,4,.3), 'okra':('Đậu bắp',2,7,.2),
 'sau':('Quả sấu',.5,8,.1),'durian':('Sầu riêng',1.5,27,5.3),
 'jackfruit':('Mít',1.5,23,.5),
 'guava':('Ổi chín',2.5,14,1), 'lime':('Chanh',.7,9,.2),
 'galangal':('Riềng',1.0,15,.1), 'starfruit':('Khế',.9,7,.3),
 'banana_flower':('Bắp chuối bào',1.3,5,.3), 'amaranth':('Rau dền',2.1,4,.2),
 'sweet_leaves':('Rau lang',2.5,5,.4), 'kohlrabi':('Su hào',1.7,6,.1),
 'radish':('Củ cải trắng',.8,4,.1), 'snail':('Thịt ốc',16,2,1.5),
 'jellyfish':('Sứa',5,2,.4), 'scallop':('Sò điệp',17,4,1.0),
 'gac':('Thịt quả gấc',1.5,12,6), 'sour_leaf':('Lá giang',1.0,4,.2),
 'wheat_flour':('Bột mì đã hấp',8,55,1.5), 'banana_green':('Chuối xanh',1.2,27,.2),
 'red_bean':('Đậu đỏ chín',8.5,21,.5),
 'black_bean':('Đậu đen chín',8.8,23,.5), 'lotus_seed':('Hạt sen chín',4.9,18,.5),
}
# Recipe identifiers used as preference tags. These stay as canonical tags;
# tag expansion is supplied in meal_preferences for additional VN ingredients.
T = {'rice':'rice','brown_rice':'rice','glutinous':'rice','noodles':'noodles','pho':'noodles',
 'mien':'noodles','hu_tieu':'noodles','mi':'wheat','banh_canh':'noodles',
 'bread':'wheat','banh_trang':'rice','flour':'rice','corn':'corn','oat':'oats',
 'sweet_potato':'sweet_potato','potato':'potato','taro':'taro','cassava':'cassava',
 'pork':'pork','belly':'pork','ribs':'pork','beef':'beef','chicken':'chicken','duck':'duck',
 'frog':'frog','eel':'eel','fish':'fish','catfish':'fish','tuna':'fish','salmon':'fish',
 'shrimp':'shrimp','squid':'squid','crab':'crab','clam':'clam','oyster':'oyster',
 'egg':'egg','tofu':'soy','mung':'mungbean','peanut':'peanut','mushroom':'mushroom',
 'cabbage':'cabbage','bok_choy':'bok_choy','spinach':'spinach','mustard':'mustard',
 'watercress':'watercress','ngot':'ngot','malabar':'malabar','jute':'jute','muong':'muong',
 'lettuce':'lettuce','sprouts':'sprouts','carrot':'carrot','cucumber':'cucumber',
 'tomato':'tomato','onion':'onion','scallion':'scallion','garlic':'garlic',
 'ginger':'ginger','lemongrass':'lemongrass','herbs':'herb','pumpkin':'pumpkin',
 'gourd':'gourd','luffa':'luffa','bitter':'bitter','eggplant':'eggplant','broccoli':'broccoli',
 'green_bean':'green_bean','chayote':'chayote','lotus':'lotus_stem',
 'bamboo':'bamboo','papaya':'papaya','mango':'mango','banana':'banana',
 'pineapple':'pineapple','orange':'orange','pomelo':'pomelo','avocado':'avocado',
 'coconut':'coconut','milk':'milk','yogurt':'milk','sugar':'sugar','oil':'oil',
 'fish_sauce':'fish_sauce','soy_sauce':'soy_sauce','shrimp_paste':'shrimp_paste',
 'chili':'chili','tamarind':'tamarind','sesame':'sesame','salt':'salt',
 'water':None,'rice_flour':'rice','tapioca':'tapioca',
 'shallot':'shallot','turmeric':'turmeric','celery':'celery','seaweed':'seaweed','chives':'chives',
 'okra':'okra','sau':'sau','durian':'durian','jackfruit':'jackfruit',
 'guava':'guava','lime':'lime','galangal':'galangal','starfruit':'starfruit',
 'banana_flower':'banana_flower','amaranth':'amaranth','sweet_leaves':'sweet_leaves',
 'kohlrabi':'kohlrabi','radish':'radish','snail':'snail','jellyfish':'jellyfish',
 'scallop':'scallop','gac':'gac','sour_leaf':'sour_leaf','wheat_flour':'wheat',
 'banana_green':'banana','red_bean':'red_bean','black_bean':'black_bean','lotus_seed':'lotus_seed'}
# Culinary recipe grammages are rounded project assumptions, not measurements.
ROWS=[]
def add(group, lines):
    for line in lines.strip().splitlines():
        if not line.strip() or line.strip().startswith('#'):continue
        if '|' not in line:raise ValueError('Missing | in ' + line)
        name, recipe = line.strip().split('|', 1)
        parts=[]
        for entry in recipe.split(','):
            key, grams = entry.strip().split(':')
            assert key in P,(name,key)
            grams=float(grams)
            assert grams>0
            parts.append((key,grams))
        ROWS.append((group,name.strip(),parts))

# Main one-dish meals, including regional breakfast foods. For the current
# planner MAIN contributes to the breakfast composition; lunch/dinner use
# CARB+PROTEIN+VEGGIE/SOUP and can still log these complete foods separately.
add('MAIN', '''
Bánh mì xíu mại|bread:85,pork:85,tomato:50,cucumber:35,herbs:15
Bánh mì bò kho|bread:90,beef:110,carrot:55,water:170
Bánh mì chả cá|bread:85,fish:90,cucumber:45,herbs:15,oil:5
Bánh mì pa tê|bread:90,pork:55,belly:25,cucumber:40
Bánh mì ốp la|bread:85,egg:105,cucumber:35,oil:5
Bánh mì heo quay|bread:95,belly:95,cucumber:45,herbs:20
Bánh mì thịt nướng|bread:90,pork:110,cucumber:45,herbs:20
Bánh mì nem nướng|bread:85,pork:105,cucumber:40,herbs:15
Bánh mì gà xé|bread:95,chicken:95,cucumber:45,herbs:15
Bánh mì chay đậu phụ|bread:90,tofu:105,cucumber:55,soy_sauce:8
Phở bò tái|pho:200,beef:100,scallion:12,herbs:20,water:300
Phở bò viên|pho:200,beef:95,scallion:12,herbs:20,water:310
Phở sốt vang|pho:190,beef:120,carrot:45,water:250
Phở xào bò|pho:200,beef:100,bok_choy:70,oil:9
Phở cuốn thịt bò|pho:150,beef:105,lettuce:55,herbs:25
Bún bò Nam Bộ|noodles:190,beef:120,lettuce:50,peanut:15,herbs:25
Bún măng vịt|noodles:190,duck:115,bamboo:75,water:250
Bún ngan|noodles:190,duck:110,scallion:18,water:280
Bún ốc|noodles:180,snail:95,tomato:70,water:290
Bún sứa Nha Trang|noodles:170,jellyfish:85,fish:50,sprouts:50,water:310
Bún cá rô đồng|noodles:185,fish:110,ngot:45,water:280
Bún cá Châu Đốc|noodles:185,fish:110,herbs:35,water:290
Bún chả cá Đà Nẵng|noodles:185,fish:125,tomato:55,water:280
Bún suông|noodles:180,shrimp:120,tomato:55,water:300
Bún giò heo|noodles:175,ribs:125,scallion:15,water:320
Bún tôm Hải Phòng|noodles:185,shrimp:110,ngot:45,water:290
Miến lươn|mien:175,eel:115,scallion:20,water:290
Miến ngan|mien:185,duck:120,herbs:20,water:280
Miến xào cua|mien:190,crab:105,carrot:40,oil:8
Hủ tiếu bò kho|hu_tieu:185,beef:125,carrot:65,water:260
Hủ tiếu khô thịt băm|hu_tieu:190,pork:100,sprouts:55,scallion:20,oil:7
Hủ tiếu sa tế bò|hu_tieu:190,beef:120,peanut:13,water:270
Hủ tiếu mực|hu_tieu:190,squid:125,sprouts:55,water:280
Mì Quảng tôm thịt|mi:190,shrimp:80,pork:65,herbs:45,water:115
Mì Quảng ếch|mi:190,frog:130,herbs:45,water:115
Mì Quảng cá lóc|mi:185,fish:130,herbs:45,water:115
Cao lầu Hội An|mi:190,pork:120,lettuce:50,herbs:25
Mì hoành thánh|mi:175,pork:105,egg:45,water:280
Mì gà tần|mi:175,chicken:125,mushroom:65,water:300
Cháo tôm|rice:65,shrimp:95,scallion:15,water:250
Cháo sườn|rice:65,ribs:110,scallion:15,water:260
Cháo vịt|rice:70,duck:100,ginger:8,water:250
Cháo nghêu|rice:70,clam:125,scallion:15,water:260
Cháo hàu|rice:70,oyster:115,scallion:12,water:260
Cháo đậu xanh|rice:80,mung:90,water:260
Cháo ếch|rice:70,frog:110,ginger:10,water:260
Xôi xéo|glutinous:210,mung:75,scallion:12,oil:10
Xôi gấc|glutinous:210,gac:35,sugar:10
Xôi lạc|glutinous:205,peanut:42,coconut:25
Xôi bắp|glutinous:160,corn:90,mung:40
Xôi đậu đen|glutinous:170,black_bean:95,coconut:20
Xôi thịt kho|glutinous:190,pork:100,egg:50
Bánh bèo Huế|rice_flour:180,shrimp:55,scallion:15,oil:6
Bánh nậm Huế|rice_flour:160,shrimp:65,pork:35
Bánh bột lọc tôm thịt|tapioca:150,shrimp:85,pork:35
Bánh giò thịt|rice_flour:150,pork:110,mushroom:30
Bánh đúc nóng|rice_flour:180,pork:90,mushroom:50
Bánh đúc mặn|rice_flour:170,shrimp:60,pork:45
Bánh hỏi thịt nướng|noodles:170,pork:130,herbs:40
Bánh hỏi lòng heo|noodles:165,pork:130,herbs:45
Bánh căn trứng|rice_flour:170,egg:105,scallion:15
Bánh tằm bì|noodles:180,pork:115,coconut:35,lettuce:40
Bánh cống Sóc Trăng|rice_flour:150,shrimp:105,mung:55,oil:10
Bánh giá Gò Công|rice_flour:155,shrimp:100,sprouts:75,oil:9
Bánh đa cua Hải Phòng|noodles:180,crab:115,ngot:50,water:250
Bún kèn Phú Quốc|noodles:185,fish:115,coconut:65,herbs:35
Bún thang Hà Nội|noodles:180,chicken:70,egg:50,pork:35,water:280
Bún ốc nguội|noodles:180,snail:120,tomato:30,water:180
Cơm hến Huế|rice:185,clam:115,peanut:20,herbs:35
Cơm âm phủ Huế|rice:170,pork:65,shrimp:45,egg:50,cucumber:60
Cơm gà Hội An|rice:185,chicken:130,papaya:40,herbs:20
''')

add('PROTEIN', '''
Gà rang muối|chicken:170,garlic:8,oil:8,salt:1
Gà nướng mật ong|chicken:165,sugar:10,garlic:6,oil:5
Gà nướng lá chanh|chicken:175,herbs:15,oil:6
Gà om nấm|chicken:145,mushroom:105,ginger:7,water:75
Gà xào sả ớt|chicken:155,lemongrass:25,chili:8,oil:8
Gà hấp muối|chicken:170,lemongrass:15,ginger:10
Gà xào hạt điều|chicken:130,peanut:32,onion:50,oil:8
Gà lá giang|chicken:155,sour_leaf:55,water:100
Gà chiên nước mắm|chicken:165,fish_sauce:12,sugar:8,oil:12
Gà xé phay|chicken:140,cabbage:95,onion:35,herbs:20
Vịt quay mật ong|duck:160,sugar:12,ginger:10
Vịt om sấu|duck:145,sau:25,ginger:10,water:100
Vịt luộc gừng|duck:175,ginger:15,scallion:12
Vịt nướng chao|duck:160,tofu:30,soy_sauce:12,oil:7
Vịt kho gừng|duck:165,ginger:18,fish_sauce:10
Ếch xào sả ớt|frog:170,lemongrass:25,chili:7,oil:8
Ếch kho tộ|frog:175,fish_sauce:12,shallot:15,oil:6
Ếch chiên nước mắm|frog:170,fish_sauce:12,garlic:8,oil:12
Thịt viên sốt cà chua|pork:160,tomato:110,onion:35,oil:7
Thịt băm rang cháy cạnh|pork:170,shallot:18,fish_sauce:10,oil:8
Thịt nạc rim mắm|pork:165,fish_sauce:12,sugar:10
Thịt kho nước dừa|belly:135,coconut:100,fish_sauce:10
Thịt kho củ cải|pork:155,gourd:105,fish_sauce:9,water:55
Heo xào sả ớt|pork:160,lemongrass:25,chili:8,oil:8
Heo xào nấm|pork:145,mushroom:105,onion:30,oil:7
Sườn nướng ngũ vị|ribs:170,garlic:10,sugar:9,oil:6
Sườn hấp đậu đen|ribs:150,black_bean:80,garlic:8
Sườn rim me|ribs:165,tamarind:32,sugar:10,oil:7
Chả lá lốt thịt heo|pork:170,herbs:25,shallot:15,oil:8
Nem nướng Nha Trang|pork:170,garlic:10,sugar:8,oil:8
Giò thủ|belly:100,pork:90,mushroom:25
Chả quế|pork:155,garlic:10,oil:5
Bò kho gừng|beef:165,ginger:20,fish_sauce:10
Bò xào cần tây|beef:135,celery:95,onion:50,oil:8
Bò xào bông cải|beef:135,broccoli:120,oil:8
Bò cuốn lá lốt|beef:145,pork:35,herbs:30,oil:7
Bò kho sả|beef:160,lemongrass:25,carrot:50,water:50
Bò sốt tiêu đen|beef:155,onion:75,oil:8
Bò nhúng giấm|beef:140,lettuce:90,herbs:30,water:80
Cá trắm kho riềng|fish:175,galangal:16,fish_sauce:12
Cá trắm kho nghệ|fish:170,turmeric:15,fish_sauce:12
Cá rô đồng kho tộ|fish:165,fish_sauce:15,oil:6
Cá kèo kho rau răm|catfish:165,herbs:20,fish_sauce:12
Cá ngừ kho thơm|tuna:160,pineapple:85,tomato:40,fish_sauce:10
Cá thu sốt cà chua|fish:165,tomato:110,onion:30,oil:7
Cá cơm kho tiêu|fish:165,fish_sauce:13,oil:6
Cá bống kho tiêu|fish:165,fish_sauce:12,oil:6
Cá nục hấp|fish:180,ginger:12,scallion:15
Cá chép om dưa|fish:160,cabbage:90,tomato:60,water:75
Cá diêu hồng hấp xì dầu|fish:180,soy_sauce:15,ginger:15
Cá lóc nướng trui|fish:180,herbs:40,cucumber:60
Cá trê nướng riềng|catfish:175,galangal:18,oil:5
Cá basa chiên sả|catfish:165,lemongrass:25,oil:14
Cá bạc má kho cà|fish:165,tomato:95,fish_sauce:12
Cá hồi kho tiêu|salmon:160,fish_sauce:10,oil:5
Tôm rang me|shrimp:165,tamarind:35,sugar:10,oil:8
Tôm hấp sả|shrimp:185,lemongrass:25,ginger:10
Tôm chiên bột|shrimp:140,rice_flour:70,oil:14
Tôm xào bông cải|shrimp:145,broccoli:135,oil:8
Tôm sốt bơ tỏi|shrimp:175,garlic:12,oil:16
Mực hấp gừng|squid:185,ginger:20,scallion:20
Mực nướng sa tế|squid:180,chili:15,lemongrass:20,oil:9
Mực rim me|squid:175,tamarind:35,sugar:10,oil:7
Mực xào dứa|squid:145,pineapple:105,onion:40,oil:8
Nghêu hấp sả|clam:190,lemongrass:25,ginger:12,water:60
Sò điệp nướng mỡ hành|scallop:155,scallion:30,oil:15,peanut:10
Cua rang me|crab:175,tamarind:40,sugar:10,oil:10
Ghẹ hấp gừng|crab:190,ginger:20,lemongrass:12
Đậu phụ chiên sả ớt|tofu:185,lemongrass:20,chili:8,oil:13
Đậu phụ hấp nấm|tofu:175,mushroom:115,ginger:8
Đậu phụ om chuối xanh|tofu:165,banana_green:75,herbs:20,water:75
Đậu phụ kho sả|tofu:170,lemongrass:25,soy_sauce:12,oil:6
Trứng cuộn thịt|egg:125,pork:80,scallion:15,oil:6
Trứng sốt cà chua|egg:145,tomato:110,oil:8
Trứng kho thịt|egg:100,pork:115,fish_sauce:12
Trứng đúc thịt|egg:130,pork:95,scallion:12,oil:9
Trứng chiên nấm|egg:140,mushroom:90,oil:8
Trứng hấp đậu phụ|egg:115,tofu:125,scallion:12
''')

add('VEGGIE', '''
Su hào xào cà rốt|kohlrabi:130,carrot:105,oil:7
Su hào luộc|kohlrabi:230,water:10
Củ cải trắng luộc|radish:220,water:10
Củ cải kho nước tương|radish:205,soy_sauce:12,oil:5
Bắp cải xào cà chua|cabbage:175,tomato:90,oil:7
Bắp cải trộn giấm|cabbage:170,carrot:50,sugar:7
Cải bó xôi xào tỏi|spinach:190,garlic:12,oil:7
Cải bó xôi luộc|spinach:200,water:10
Cải xoong xào tỏi|watercress:185,garlic:12,oil:8
Cải xoong luộc|watercress:200,water:10
Cải thìa sốt dầu hào|bok_choy:200,soy_sauce:12,oil:8
Rau dền xào tỏi|amaranth:180,garlic:12,oil:7
Rau lang xào tỏi|sweet_leaves:190,garlic:12,oil:8
Bí xanh luộc|gourd:220,water:10
Bí xanh xào tỏi|gourd:195,garlic:12,oil:7
Bí đỏ hấp|pumpkin:220,water:10
Bí đỏ xào tỏi|pumpkin:190,garlic:12,oil:7
Mướp xào giá đỗ|luffa:130,sprouts:105,oil:7
Mướp xào trứng|luffa:165,egg:85,oil:7
Khổ qua xào thịt bò|bitter:135,beef:100,oil:7
Dưa chuột trộn chua ngọt|cucumber:220,sugar:10,chili:4
Dưa chuột chấm muối|cucumber:230,salt:1
Cà chua trộn hành|tomato:190,onion:65,oil:4
Cà chua xào trứng|tomato:175,egg:100,oil:8
Cà tím xào tỏi|eggplant:190,garlic:12,oil:9
Cà tím kho đậu phụ|eggplant:130,tofu:115,soy_sauce:12,oil:6
Bầu xào tỏi|gourd:200,garlic:12,oil:7
Bầu luộc|gourd:225,water:10
Rau muống xào chao|muong:190,tofu:45,oil:9
Rau muống trộn chua ngọt|muong:200,sugar:8,chili:5
Đậu que xào tỏi|green_bean:195,garlic:12,oil:7
Đậu cô ve luộc|green_bean:210,water:10
Bông cải xào nấm|broccoli:145,mushroom:105,oil:7
Bông cải xào tỏi|broccoli:195,garlic:11,oil:7
Nấm rơm xào tỏi|mushroom:225,garlic:10,oil:8
Nấm đùi gà kho tiêu|mushroom:220,soy_sauce:12,oil:7
Nấm kim châm xào|mushroom:220,scallion:20,oil:7
Nấm đông cô xào rau củ|mushroom:140,carrot:70,broccoli:60,oil:8
Ngó sen trộn chua ngọt|lotus:185,carrot:45,sugar:9
Bắp chuối trộn rau răm|banana_flower:180,herbs:25,carrot:40
Gỏi xoài xanh|mango:190,carrot:55,chili:6,peanut:15
Gỏi củ hủ dừa|lotus:150,carrot:85,herbs:25
Dưa bắp cải muối|cabbage:220,salt:3
Dưa leo muối chua|cucumber:220,salt:3
Cải chua xào tỏi|mustard:190,garlic:12,oil:7
Xà lách trộn dầu giấm|lettuce:160,cucumber:70,tomato:45,oil:6
Rau củ luộc thập cẩm|broccoli:80,carrot:75,gourd:85,water:10
Rau cải xào nấm|mustard:145,mushroom:110,oil:8
Bắp non xào nấm|corn:125,mushroom:115,oil:7
Đậu bắp luộc|okra:220,water:10
Đậu bắp xào tỏi|okra:200,garlic:11,oil:7
Khoai tây xào cà rốt|potato:150,carrot:90,oil:8
Măng xào tỏi|bamboo:210,garlic:13,oil:8
Măng xào nấm|bamboo:150,mushroom:90,oil:8
Củ sen xào thập cẩm|lotus:150,carrot:70,green_bean:55,oil:8
''')

add('SOUP', '''
Canh chua tôm|shrimp:90,pineapple:60,tomato:65,herbs:15,water:260
Canh chua cá bông lau|catfish:110,pineapple:60,tomato:60,water:270
Canh chua cá diêu hồng|fish:100,pineapple:60,tomato:65,water:270
Canh chua nghêu|clam:110,pineapple:60,tomato:55,water:260
Canh bầu nấu hến|clam:105,gourd:110,water:260
Canh bí đỏ nấu tôm|shrimp:85,pumpkin:160,water:260
Canh cua rau đay|crab:95,jute:115,water:290
Canh cua mồng tơi mướp|crab:85,malabar:90,luffa:95,water:280
Canh ngao nấu dứa|clam:115,pineapple:95,tomato:45,water:260
Canh nghêu mồng tơi|clam:115,malabar:110,water:280
Canh cá nấu măng chua|fish:105,bamboo:115,tomato:55,water:265
Canh sấu thịt băm|pork:85,sau:30,herbs:20,water:310
Canh hến nấu khế|clam:105,starfruit:50,tomato:45,water:300
Canh cải cúc thịt băm|pork:95,mustard:110,water:290
Canh cải bó xôi thịt nạc|pork:95,spinach:110,water:290
Canh củ cải hầm xương|ribs:110,gourd:145,water:280
Canh khoai tây cà rốt|potato:115,carrot:110,water:290
Canh bí đao tôm khô|shrimp:55,gourd:165,water:290
Canh đu đủ hầm xương|ribs:100,papaya:145,water:280
Canh rau đay mướp|jute:110,luffa:120,water:290
Canh rau muống nấu sấu|muong:130,sau:25,water:310
Canh bắp cải cà chua|cabbage:110,tomato:95,water:295
Canh hành cà chua|tomato:130,scallion:35,water:315
Canh nấm đậu phụ|mushroom:110,tofu:100,water:290
Canh nấm kim châm thịt bò|mushroom:110,beef:100,water:285
Canh măng vịt|bamboo:115,duck:110,water:290
Canh lá giang gà|sour_leaf:70,chicken:110,water:300
Canh lá giang cá|sour_leaf:70,fish:115,water:300
Canh củ sen sườn|lotus:130,ribs:105,water:290
Canh hạt sen gà|lotus_seed:115,chicken:100,water:290
Canh nấm rơm thịt bằm|mushroom:140,pork:85,water:290
Canh khổ qua cá thác lác|bitter:140,fish:95,water:280
Canh rong biển thịt bằm|seaweed:60,pork:80,tofu:60,water:300
Canh bầu thịt băm|gourd:150,pork:85,water:300
Canh súp lơ thịt bằm|broccoli:115,pork:85,water:300
''')

add('CARB', '''
Cơm gạo lứt trộn gạo trắng|brown_rice:110,rice:90
Cơm hạt sen|rice:175,lotus_seed:65
Cơm ngũ cốc đậu xanh|rice:135,brown_rice:70,mung:55
Cơm bắp|rice:160,corn:85
Khoai lang nướng|sweet_potato:240
Khoai môn luộc|taro:215,water:10
Khoai tây hấp|potato:230,water:10
Bánh mì nguyên cám|bread:95
Bánh mì lúa mạch|bread:95
Bánh đa chín|noodles:210
Nui chín|mi:190
Cháo trắng|rice:65,water:260
Yến mạch nấu nước|oat:55,water:230
Bánh bao chay|wheat_flour:100,sugar:8,water:60
Khoai mì hấp|cassava:230,water:10
Bánh mì hấp|bread:120,water:35
''')

add('DESSERT', '''
Bánh ít lá gai|glutinous:120,mung:55,sugar:18,coconut:15
Bánh in đậu xanh|mung:95,sugar:25,flour:35
Bánh cốm Hà Nội|glutinous:90,mung:55,sugar:20
Bánh đậu xanh Hải Dương|mung:90,sugar:30,oil:10
Bánh bò hấp|rice_flour:130,sugar:22,coconut:30
Bánh tai yến|rice_flour:130,sugar:25,oil:13
Chè đậu đỏ|red_bean:135,sugar:26,coconut:40,water:85
Chè đậu đen|black_bean:135,sugar:25,coconut:35,water:90
Chè trôi nước|glutinous:120,mung:55,sugar:32,ginger:6
Chè khúc bạch|milk:135,yogurt:90,sugar:28,lotus_seed:30
Chè bưởi|pomelo:100,mung:70,sugar:30,coconut:40
Chè bắp|corn:135,sugar:27,coconut:48,water:55
Sương sáo nước đường|water:165,sugar:23,coconut:25
Sâm bổ lượng|lotus_seed:65,red_bean:60,sugar:23,water:150
Rau câu dừa|coconut:160,sugar:25,water:65
Chè thập cẩm|mung:65,red_bean:65,black_bean:65,sugar:24,coconut:45
Chè hạt sen long nhãn|lotus_seed:115,sugar:25,water:145
Xôi xoài cốt dừa|glutinous:145,mango:110,coconut:35,sugar:15
Chuối nếp nướng|banana:125,glutinous:110,coconut:35,sugar:15
Bánh cam nhân đậu|flour:95,mung:65,sugar:18,oil:12
Bánh khoai mì nướng|cassava:145,coconut:60,sugar:25,egg:45
Khoai lang kén|sweet_potato:145,flour:35,sugar:13,oil:12
Bánh tiêu|flour:110,sugar:18,sesame:8,oil:12
''')

add('DRINK', '''
Nước ép ổi không đường|water:60,guava:170
Nước cam vắt|orange:230,water:20
Sinh tố bơ|avocado:115,milk:130,sugar:15,water:40
Sinh tố xoài|mango:180,milk:120,sugar:10
Sinh tố chuối|banana:140,milk:145,yogurt:50
Sữa bắp|corn:110,milk:140,water:75,sugar:12
Trà sen|water:250,lotus_seed:10
Nước chanh|lime:70,water:240,sugar:12
Trà tắc|lime:45,water:250,sugar:10
Nước đậu đen rang|black_bean:45,water:260
Nước sâm thảo mộc|water:280,sugar:10
Nước ép dứa|pineapple:210,water:55
Sinh tố đu đủ|papaya:175,milk:130,sugar:10
''')

def fold(text):
    raw=unicodedata.normalize('NFD',text.casefold().replace('đ','d'))
    return re.sub(r'\s+',' ', ''.join(c for c in raw if not unicodedata.combining(c))).strip()

def id_for(name):
    return 'vnext_'+re.sub('[^a-z0-9]+','_',fold(name)).strip('_')

def build():
    prior=json.loads(BASE.read_text(encoding='utf-8'))['dishes']
    forbidden_names={fold(d['name']) for d in prior}
    forbidden_ids={d['dish_id'] for d in prior}
    names=set(); ids=set(); dishes=[]
    limits={'MAIN':(400,210,800),'PROTEIN':(170,75,390),'VEGGIE':(220,80,450),'SOUP':(400,150,750),
            'CARB':(210,75,460),'DESSERT':(180,50,350),'DRINK':(260,100,650)}
    meal_map={'MAIN':['breakfast','lunch','dinner'], 'PROTEIN':['lunch','dinner'], 'VEGGIE':['lunch','dinner'],
              'SOUP':['lunch','dinner'], 'CARB':['breakfast','lunch','dinner'],
              'DESSERT':['breakfast','lunch','dinner'], 'DRINK':['breakfast','lunch','dinner']}
    for role,name,recipe in ROWS:
        identifier=id_for(name)
        if len(identifier)>64:raise ValueError('Long ID: '+identifier)
        if fold(name) in forbidden_names: raise ValueError('Existing catalog name: '+name)
        if identifier in forbidden_ids or identifier in ids or fold(name) in names: raise ValueError('Duplicate: '+name)
        names.add(fold(name));ids.add(identifier)
        grams=sum(g for _,g in recipe)
        # grams in recipe are the assumed finished edible mass of one serving.
        # Unless cooked mass is measured, differences caused by evaporation remain unknown.
        p=sum(P[key][1]*g/100 for key,g in recipe)*100/grams
        c=sum(P[key][2]*g/100 for key,g in recipe)*100/grams
        f=sum(P[key][3]*g/100 for key,g in recipe)*100/grams
        kcal=4*p+4*c+9*f
        reference=round(grams,1)
        if not 1<=grams<=1600:raise ValueError('Bad portion '+name)
        tags=sorted({T[k] for k,g in recipe if T[k] is not None})
        estimate={
           'source':'Ước tính kỹ thuật từ công thức khẩu phần tham khảo của NutriFit; không phải dữ liệu phòng xét nghiệm',
           'method':'Cộng protein/carbohydrate/lipid theo khối lượng nguyên liệu chín giả định; tính kcal = 4P + 4C + 9F',
           'confidence':'STUDENT_PROJECT_ROUNDED_ASSUMPTION',
           'serving_estimated_grams':reference,
           'recipe':{'ingredients':[{'key':key,'name':P[key][0],'retained_edible_grams':g,
                                    'assumed_macros_per_100g':{'protein':P[key][1], 'carbs':P[key][2], 'fat':P[key][3]}}
                                   for key,g in recipe],
                     'finished_edible_grams':reference,'servings':1,
                     'mass_basis':'ASSUMED_FINISHED_MASS_NOT_MEASURED'},
           'limitations':['Giá trị dinh dưỡng chỉ là ước tính cho một công thức giả định; không dùng cho chỉ định y khoa.',
                          'Dầu ăn, nước dùng, công thức vùng miền và trọng lượng sau nấu có thể khác đáng kể.',
                          'Danh sách nguyên liệu chưa chứng minh an toàn dị ứng hoặc không nhiễm chéo.',
                          'Chưa có số liệu chất xơ đáng tin cậy.']}
        dish={'dish_id':identifier,'name':name,'type':role,'group':role.lower(),'preparation_state':'ready',
              'reference_grams':reference,'min_grams':round(max(20,reference*.45),1),
              'max_grams':round(min(1600,reference*1.9),1),
              'calories_per_100g':round(kcal,3),
              'macros_per_100g':{'protein':round(p,3),'carbs':round(c,3),'fat':round(f,3),'fiber':None},
              'ingredients':tags,'meal_types':meal_map[role],'prep_minutes':{'MAIN':35,'PROTEIN':30,'VEGGIE':15,'SOUP':25,'CARB':20,'DESSERT':40,'DRINK':10}[role],
              'estimated':True,'active':True,'data_version':1,'provenance':estimate}
        dishes.append(dish)
    out={'format':'nutrifit-vietnamese-expanded-estimated-recipes-2026',
         'dataset':'NutriFit curated regional dishes — engineering estimate for student project only',
         'version':1,'dishes':dishes,'legacy_menus':[],
         'disclaimer':'Energy and macros are engineering estimates, not certified nutritional facts. Allergies must be assessed independently.'}
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'new_dishes':len(dishes),'role_counts':dict(Counter(d['type'] for d in dishes)),
                      'baseline_unique':len(prior),'expected_if_base_only':len(prior)+len(dishes),
                      'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()},ensure_ascii=False,indent=2))
if __name__=='__main__':build()
