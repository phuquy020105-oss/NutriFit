"""Offline recipe preparation; no database/provider access. Use --write explicitly."""
import argparse, copy, hashlib, json
from collections import Counter
from pathlib import Path
from seed_nutrition_catalog import load_seed, folded_name
BASE = Path(__file__).parent / "seeds/demo_catalog_rebuild_seed.json"
TARGET = BASE.parent / "nutrition_catalog.json"
MANIFEST = BASE.parent / "demo_catalog150_batch.json"


def prepare():
    base = load_seed(BASE)
    profiles = {}
    for dish in base["dishes"]:
        for item in dish["provenance"]["recipe"]["ingredients"]:
            profiles.setdefault(item["ingredient"], copy.deepcopy(item))
    # New rounded engineering assumptions, never represented as verified food-table data.
    extras = {
      "tilapia_raw":("Thịt cá diêu hồng sống bỏ xương","raw",20,0,3),
      "cabbage_raw":("Bắp cải sống","raw",1.5,5,.2),
      "pork_leg":("Thịt giò heo sống bỏ xương","raw",20,0,12),
      "rib_raw":("Thịt sườn heo sống bỏ xương","raw",19,0,18),
      "squid":("Mực sống làm sạch","raw",16.5,2,1.5),
      "liver":("Gan heo sống","raw",20,4,4),
      "offal":("Lòng heo đã làm sạch và luộc","cooked",18,2,10),
      "fish_fat_raw":("Thịt cá basa sống bỏ xương","raw",18,0,8),
      "pumpkin":("Bí đỏ bỏ vỏ hạt","raw",1,7,.2),
      "chayote":("Su su gọt vỏ","raw",1,4,.1),
      "green_bean":("Đậu que nhặt sạch","raw",2,7,.2),
      "sweet_leaves":("Rau lang nhặt sạch","raw",3,5,.3),
      "amaranth":("Rau dền nhặt sạch","raw",3,4,.3),
      "mustard":("Cải xanh nhặt sạch","raw",2,4,.2),
      "broccoli":("Bông cải xanh","raw",3,6,.3),
      "chives":("Hẹ","raw",2,5,.3),
      "celery":("Cần tây","raw",1,3,.2),
      "dill":("Thì là","raw",2,5,.3),
      "lotus_stem":("Ngó sen ăn được","raw",1,7,.1),
      "bamboo":("Măng đã luộc và bỏ nước luộc","cooked",2,5,.3),
      "seaweed":("Rong biển đã ngâm và rửa","ready",2,5,.5),
      "lot_leaf":("Lá lốt","raw",3,5,.5),
      "mung_dry":("Đậu xanh khô bỏ vỏ","raw",23,58,1.5),
      "mung_cooked":("Đậu xanh đã nấu","cooked",7,20,.5),
      "pea":("Đậu Hà Lan chín","cooked",5,13,.5),
      "tapioca":("Bột năng khô","ready",.2,88,.1),
      "rice_paper":("Bánh tráng gạo khô","ready",5,78,.5),
      "potato":("Khoai tây luộc","cooked",2,18,.1),
      "cassava":("Sắn đã bóc vỏ, ngâm và luộc kỹ","cooked",1,28,.3),
      "brown_rice":("Cơm gạo lứt chín","cooked",3,24,1),
      "mango":("Xoài chín bỏ vỏ hạt","raw_edible",1,15,.4),
      "jackfruit":("Mít bỏ hạt","raw_edible",1.5,23,.4),
      "pomelo":("Bưởi bóc vỏ","raw_edible",.8,9,.1),
      "longan":("Nhãn bóc vỏ bỏ hạt","raw_edible",1,15,.2),
      "lychee":("Vải bóc vỏ bỏ hạt","raw_edible",.8,16,.3),
      "rambutan":("Chôm chôm bóc vỏ bỏ hạt","raw_edible",.7,17,.2),
      "coconut_milk":("Nước cốt dừa","ready",2,4,20),
      "milk":("Sữa tươi không đường","ready",3.3,5,3.2),
      "condensed_milk":("Sữa đặc có đường","ready",8,55,8),
      "cane_juice":("Nước mía đã lọc","ready",.2,18,0),
      "coffee":("Cà phê đen đã pha không đường","ready",0,0,0),
      "tea":("Trà đã pha không đường","ready",0,0,0),
      "shrimp_paste":("Mắm tôm tham khảo","ready",10,3,1),
      "fermented_fish":("Mắm cá tham khảo đã nấu","ready",18,2,6),
      "annatto":("Dầu điều từ dầu hướng dương","ready",0,0,100),
    }
    for key,(name,state,p,c,f) in extras.items():
        profiles[key]={"ingredient":key,"name":name,"state":state,"macro_per_100g":{"protein":p,"carbs":c,"fat":f},"basis":"ROUNDED_ENGINEERING_ASSUMPTION_NOT_MEASURED"}
    # id, name, role, ingredients with grams, finished edible grams, servings, min/max serving grams.
    recipes = [
      ("vn_com_tam_suon_bi_cha","Cơm tấm sườn bì chả","MAIN",[("rice",180),("rib_raw",90),("pork",25),("egg",35),("glass_dry",5),("cucumber",40),("fish_sauce",10),("sugar",5),("oil",5)],370,1,220,650),
      ("vn_com_ga_luoc","Cơm gà luộc","MAIN",[("rice",180),("chicken_skin",100),("cucumber",50),("ginger",5),("scallion",5),("salt",1)],330,1,200,550),
      ("vn_com_ga_xoi_mo","Cơm gà xối mỡ","MAIN",[("rice",180),("chicken_raw",150),("oil",18),("cucumber",50),("soy_sauce",8),("sugar",3)],370,1,220,600),
      ("vn_com_chien_duong_chau","Cơm chiên Dương Châu","MAIN",[("rice",500),("egg",150),("pork",100),("shrimp",75),("carrot",80),("pea",50),("oil",25),("soy_sauce",15)],970,3,200,500),
      ("vn_com_chien_hai_san","Cơm chiên hải sản","MAIN",[("rice",500),("squid",180),("shrimp",100),("egg",100),("scallion",30),("oil",25),("soy_sauce",15)],900,3,180,500),
      ("vn_com_suon_nuong","Cơm sườn nướng","MAIN",[("rice",180),("rib_raw",130),("garlic",5),("sugar",8),("fish_sauce",8),("oil",5),("cucumber",50)],340,1,200,550),
      ("vn_com_bo_luc_lac","Cơm bò lúc lắc","MAIN",[("rice",180),("beef_raw",130),("onion",60),("tomato",40),("oil",8),("soy_sauce",8),("sugar",4)],370,1,220,600),
      ("vn_com_ca_kho","Cơm cá kho","MAIN",[("rice",180),("fish_raw",120),("fish_sauce",8),("sugar",5),("oil",5),("cabbage_cooked",100),("water",30)],390,1,240,600),
      ("vn_bun_cha","Bún chả","MAIN",[("noodles",180),("pork_raw",80),("pork_fat",50),("lettuce",50),("herb",15),("fish_sauce",15),("sugar",10),("lime",5),("garlic",5),("water",100)],490,1,300,750),
      ("vn_bun_mam","Bún mắm","MAIN",[("noodles",200),("fermented_fish",30),("shrimp",50),("squid",50),("pork",30),("eggplant",60),("lemongrass",10),("sugar",5),("water",300)],680,1,400,1000),
      ("vn_bun_ca","Bún cá","MAIN",[("noodles",200),("fish_raw",140),("tomato",80),("dill",10),("scallion",10),("fish_sauce",8),("oil",10),("water",300)],690,1,400,1000),
      ("vn_hu_tieu_nam_vang","Hủ tiếu Nam Vang","MAIN",[("noodles",180),("pork_raw",60),("shrimp",60),("liver",30),("sprouts",60),("chives",15),("garlic",5),("oil",5),("fish_sauce",10),("water",300)],680,1,400,1000),
      ("vn_chao_long","Cháo lòng","MAIN",[("rice_dry",60),("offal",120),("ginger",5),("scallion",10),("fish_sauce",10),("water",500)],630,1,350,950),
      ("vn_chao_ca","Cháo cá","MAIN",[("rice_dry",60),("fish_raw",120),("ginger",10),("dill",10),("fish_sauce",8),("oil",5),("water",500)],640,1,350,950),
      ("vn_banh_canh_cua","Bánh canh cua","MAIN",[("rice_dry",55),("tapioca",30),("crab",90),("shrimp",50),("annatto",8),("fish_sauce",8),("scallion",10),("water",500)],700,1,400,1050),
      ("vn_banh_canh_gio_heo","Bánh canh giò heo","MAIN",[("rice_dry",60),("tapioca",20),("pork_leg",100),("carrot",50),("scallion",10),("fish_sauce",10),("water",500)],650,1,400,1000),
      ("vn_banh_uot_cha_lua","Bánh ướt chả lụa","MAIN",[("rice_dry",70),("pork_raw",60),("tapioca",5),("sprouts",50),("shallot",10),("oil",5),("fish_sauce",15),("sugar",5),("water",250)],420,1,250,650),
      ("vn_banh_xeo","Bánh xèo","MAIN",[("rice_dry",80),("coconut_milk",40),("pork_raw",50),("shrimp",60),("sprouts",120),("lettuce",80),("herb",15),("oil",18),("fish_sauce",15),("sugar",8),("water",180)],620,2,180,500),
      ("vn_banh_khot","Bánh khọt","MAIN",[("rice_dry",80),("coconut_milk",30),("shrimp",100),("scallion",20),("oil",15),("lettuce",80),("herb",15),("fish_sauce",15),("sugar",8),("water",180)],510,2,150,400),
      ("vn_xoi_dau_xanh","Xôi đậu xanh","MAIN",[("sticky",200),("mung_cooked",80),("coconut_milk",20),("salt",1)],300,1,150,450),
      ("vn_xoi_man","Xôi mặn","MAIN",[("sticky",180),("pork",60),("egg",40),("peanut",15),("shallot",10),("oil",5),("soy_sauce",5)],310,1,180,500),
      ("vn_banh_mi_thit","Bánh mì thịt","MAIN",[("bread",90),("pork",60),("liver",15),("carrot",25),("cucumber",35),("herb",5),("oil",5),("soy_sauce",5)],230,1,130,400),
      ("vn_bun_dau_mam_tom","Bún đậu mắm tôm","MAIN",[("noodles",180),("tofu",120),("pork",60),("cucumber",70),("herb",20),("shrimp_paste",20),("sugar",8),("lime",10),("oil",15)],500,1,300,750),
      ("vn_suon_ram_man","Sườn ram mặn","PROTEIN",[("rib_raw",500),("fish_sauce",25),("sugar",20),("shallot",20),("garlic",10),("oil",10),("water",100)],550,4,70,220),
      ("vn_suon_xao_chua_ngot","Sườn xào chua ngọt","PROTEIN",[("rib_raw",500),("tomato",150),("onion",100),("pineapple",100),("sugar",25),("fish_sauce",20),("oil",15),("water",80)],850,4,100,320),
      ("vn_thit_ba_chi_luoc","Thịt ba chỉ luộc","PROTEIN",[("pork_fat",400),("ginger",10),("salt",3),("water",60)],360,3,60,180),
      ("vn_ga_kho_sa","Gà kho sả","PROTEIN",[("chicken_raw",500),("lemongrass",50),("shallot",30),("fish_sauce",20),("sugar",10),("oil",10),("water",100)],600,4,80,250),
      ("vn_ga_hap_hanh","Gà hấp hành","PROTEIN",[("chicken_raw",500),("scallion",100),("ginger",30),("salt",3),("water",50)],560,4,80,220),
      ("vn_bo_xao_hanh_tay","Bò xào hành tây","PROTEIN",[("beef_raw",400),("onion",250),("garlic",15),("soy_sauce",15),("oil",15)],610,4,80,250),
      ("vn_bo_xao_rau_muong","Bò xào rau muống","PROTEIN",[("beef_raw",300),("muong",400),("garlic",25),("oyster",15),("oil",15)],650,4,90,260),
      ("vn_bo_la_lot","Bò lá lốt","PROTEIN",[("beef_raw",350),("pork_fat",100),("lot_leaf",60),("lemongrass",15),("fish_sauce",15),("oil",10)],480,4,60,200),
      ("vn_ca_basa_kho_to","Cá basa kho tộ","PROTEIN",[("fish_fat_raw",500),("fish_sauce",25),("sugar",20),("shallot",20),("pepper",3),("oil",8),("water",120)],580,4,80,230),
      ("vn_ca_dieu_hong_chien","Cá diêu hồng chiên","PROTEIN",[("tilapia_raw",500),("oil",35),("salt",3),("garlic",10)],450,3,80,240),
      ("vn_ca_hap_gung","Cá hấp gừng","PROTEIN",[("fish_raw",500),("ginger",50),("scallion",40),("soy_sauce",20),("water",60)],560,4,80,220),
      ("vn_tom_rang_thit","Tôm rang thịt","PROTEIN",[("shrimp_raw",250),("pork_fat",250),("fish_sauce",20),("sugar",15),("shallot",20),("oil",10)],500,4,60,200),
      ("vn_muc_xao_can_tay","Mực xào cần tây","PROTEIN",[("squid",400),("celery",200),("onion",150),("garlic",15),("oil",15),("fish_sauce",15)],660,4,80,250),
      ("vn_cha_ca_thi_la","Chả cá thì là","PROTEIN",[("fish_raw",400),("pork_fat",50),("dill",30),("tapioca",20),("fish_sauce",15),("oil",20)],480,4,60,200),
      ("vn_cha_lua","Chả lụa","PROTEIN",[("pork_raw",300),("pork_fat",100),("tapioca",20),("fish_sauce",10),("water",70)],490,5,50,160),
      ("vn_dau_phu_chien","Đậu phụ chiên","PROTEIN",[("tofu",400),("oil",30),("salt",2)],390,3,60,220),
      ("vn_trung_hap_thit","Trứng hấp thịt","PROTEIN",[("egg",200),("pork_raw",150),("mushroom",50),("scallion",15),("fish_sauce",10),("water",60)],450,3,70,240),
      ("vn_heo_quay","Heo quay","PROTEIN",[("pork_fat",500),("salt",5),("sugar",8),("pepper",3),("garlic",10)],420,4,50,180),
      ("vn_cai_thia_xao_toi","Cải thìa xào tỏi","VEGGIE",[("bok_choy_raw",500),("garlic",25),("oil",15),("salt",3),("water",30)],490,4,70,240),
      ("vn_dau_que_xao","Đậu que xào","VEGGIE",[("green_bean",500),("garlic",15),("oil",15),("salt",3),("water",50)],500,4,70,240),
      ("vn_su_su_xao","Su su xào","VEGGIE",[("chayote",500),("garlic",15),("scallion",10),("oil",15),("salt",3)],470,4,70,230),
      ("vn_gia_xao_he","Giá xào hẹ","VEGGIE",[("sprouts",400),("chives",100),("garlic",10),("oil",12),("salt",3)],470,4,70,220),
      ("vn_rau_lang_luoc","Rau lang luộc","VEGGIE",[("sweet_leaves",500),("water",50),("salt",2)],460,4,60,230),
      ("vn_rau_den_luoc","Rau dền luộc","VEGGIE",[("amaranth",500),("water",50),("salt",2)],450,4,60,220),
      ("vn_cai_xanh_luoc","Cải xanh luộc","VEGGIE",[("mustard",500),("water",50),("salt",2)],470,4,70,240),
      ("vn_bong_cai_luoc","Bông cải luộc","VEGGIE",[("broccoli",500),("water",50),("salt",2)],490,4,70,250),
      ("vn_dua_cai_muoi","Dưa cải muối","VEGGIE",[("mustard",500),("scallion",50),("sugar",10),("salt",15),("water",100)],620,6,40,150),
      ("vn_dua_gia","Dưa giá","VEGGIE",[("sprouts",300),("carrot",100),("chives",50),("sugar",15),("salt",8),("lime",20),("water",100)],570,6,40,150),
      ("vn_goi_ngo_sen_tom_thit","Gỏi ngó sen tôm thịt","SIDE",[("lotus_stem",300),("shrimp",100),("pork",100),("carrot",80),("peanut",30),("herb",15),("fish_sauce",20),("sugar",20),("lime",20)],670,4,80,300),
      ("vn_goi_ga_bap_cai","Gỏi gà bắp cải","SIDE",[("chicken",200),("cabbage_raw",300),("carrot",80),("herb",20),("peanut",25),("fish_sauce",15),("sugar",15),("lime",20)],640,4,80,300),
      ("vn_canh_cai_thit_bam","Canh cải thịt băm","SOUP",[("mustard",300),("pork_raw",150),("scallion",10),("salt",3),("water",900)],1250,4,150,500),
      ("vn_canh_bi_do_thit_bam","Canh bí đỏ thịt băm","SOUP",[("pumpkin",400),("pork_raw",150),("scallion",15),("fish_sauce",10),("water",800)],1280,4,150,500),
      ("vn_canh_mong_toi_tom","Canh mồng tơi tôm","SOUP",[("malabar",300),("shrimp_raw",150),("salt",3),("water",900)],1250,4,150,480),
      ("vn_canh_rau_ngot","Canh rau ngót","SOUP",[("ngot",300),("salt",3),("water",900)],1150,4,130,450),
      ("vn_canh_kho_qua_nhoi_thit","Canh khổ qua nhồi thịt","SOUP",[("bitter",400),("pork_raw",200),("mushroom",30),("scallion",15),("soy_sauce",10),("water",1100)],1650,5,150,550),
      ("vn_canh_mang_ga","Canh măng gà","SOUP",[("bamboo",300),("chicken_raw",200),("scallion",15),("salt",3),("water",900)],1300,4,150,500),
      ("vn_canh_khoai_mon_suon","Canh khoai môn sườn","SOUP",[("taro",300),("rib_raw",200),("scallion",15),("salt",3),("water",900)],1300,4,150,500),
      ("vn_canh_rong_bien_dau_phu","Canh rong biển đậu phụ","SOUP",[("seaweed",100),("tofu",200),("ginger",10),("salt",3),("water",950)],1200,4,150,450),
      ("vn_canh_he_dau_phu","Canh hẹ đậu phụ","SOUP",[("chives",150),("tofu",250),("salt",3),("water",900)],1250,4,150,500),
      ("vn_bap_luoc","Bắp luộc","CARB",[("corn",200),("water",5)],200,1,80,350),
      ("vn_com_gao_lut","Cơm gạo lứt","CARB",[("brown_rice",200)],200,1,80,400),
      ("vn_khoai_tay_luoc","Khoai tây luộc","CARB",[("potato",200)],200,1,80,400),
      ("vn_san_luoc","Sắn luộc","CARB",[("cassava",180)],180,1,70,350),
      ("vn_xoai_chin","Xoài chín","DESSERT",[("mango",150)],150,1,60,300),
      ("vn_mit","Mít","DESSERT",[("jackfruit",120)],120,1,50,250),
      ("vn_buoi","Bưởi","DESSERT",[("pomelo",180)],180,1,80,350),
      ("vn_nhan","Nhãn","DESSERT",[("longan",100)],100,1,40,250),
      ("vn_vai","Vải","DESSERT",[("lychee",100)],100,1,40,250),
      ("vn_chom_chom","Chôm chôm","DESSERT",[("rambutan",120)],120,1,50,250),
      ("vn_che_dau_xanh","Chè đậu xanh","DESSERT",[("mung_dry",100),("sugar",60),("coconut_milk",80),("water",600)],800,4,100,350),
      ("vn_banh_chuoi_hap","Bánh chuối hấp","DESSERT",[("banana",400),("tapioca",100),("rice_dry",30),("sugar",60),("coconut_milk",100),("water",180)],820,8,50,180),
      ("vn_banh_da_lon","Bánh da lợn","DESSERT",[("tapioca",150),("rice_dry",50),("mung_cooked",150),("sugar",100),("coconut_milk",200),("water",200)],800,8,40,160),
      ("vn_banh_flan","Bánh flan","DESSERT",[("egg",200),("milk",500),("condensed_milk",100),("sugar",40)],780,8,50,180),
      ("vn_nuoc_dua","Nước dừa","DRINK",[("coconut_water",250)],250,1,150,500),
      ("vn_nuoc_mia","Nước mía","DRINK",[("cane_juice",200),("water",50)],250,1,120,500),
      ("vn_tra_da","Trà đá","DRINK",[("tea",250)],250,1,150,600),
      ("vn_ca_phe_den","Cà phê đen","DRINK",[("coffee",100),("water",50)],150,1,60,300),
      ("vn_ca_phe_sua_da","Cà phê sữa đá","DRINK",[("coffee",80),("condensed_milk",40),("water",80)],200,1,100,400),
    ]
    tags = {"beef_raw":["beef"],"brown_rice":["rice"],"tilapia_raw":["fish","seafood"],"cabbage_raw":["cabbage","vegetables"],"pork_leg":["pork"],"rib_raw":["pork"],"pork_raw":["pork"],"pork_fat":["pork"],"liver":["pork"],"offal":["pork"],
      "fish_fat_raw":["fish","seafood"],"fish_raw":["fish","seafood"],"squid":["squid","seafood"],
      "shrimp":["shrimp","seafood"],"shrimp_raw":["shrimp","seafood"],"crab":["crab","seafood"],
      "fish_sauce":["fish_sauce","fish","seafood"],"fermented_fish":["fermented_fish","fish","seafood"],"shrimp_paste":["shrimp_paste","shrimp","seafood"],
      "soy_sauce":["soy_sauce","soy","wheat"],"oyster":["oyster_sauce","seafood"],
      "rice_dry":["rice"],"sticky":["rice"],"noodles":["noodles","rice"],"bread":["wheat"],"glass_dry":["noodles","starch"],
      "tofu":["soy"],"milk":["milk"],"condensed_milk":["milk"],"coconut_milk":["coconut"],"coconut_water":["coconut"],
      "chicken_raw":["chicken"],"chicken_skin":["chicken"],"oil":["oil","sunflower"],"annatto":["oil","sunflower","annatto"],
      "cabbage_cooked":["cabbage","vegetables"],"bok_choy_raw":["bok_choy","vegetables"],"lot_leaf":["lot_leaf","vegetables"],
      "mung_dry":["mungbean","legumes"],"mung_cooked":["mungbean","legumes"],"pea":["pea","legumes"],
    }
    vegetables={"pumpkin","chayote","green_bean","sweet_leaves","amaranth","mustard","broccoli","chives","celery","dill","lotus_stem","bamboo","seaweed","onion","tomato","garlic","shallot","scallion","herb","cucumber","carrot","lettuce","sprouts","muong","ngot","malabar","bitter","mushroom"}
    rows=[]
    for ident,name,role,inputs,finished,servings,min_g,max_g in recipes:
        reference=round(finished/servings,1)
        details=[];ingredient_tags=set();total=dict(protein=0.,carbs=0.,fat=0.)
        for key,grams in inputs:
            profile=copy.deepcopy(profiles[key]);profile.update(edible_grams=grams,retained_grams=grams)
            group=tags.get(key,[key]);profile["tags"]=group;ingredient_tags.update(group)
            if key in vegetables:ingredient_tags.add("vegetables")
            details.append(profile)
            for macro in total:total[macro]+=grams*profile["macro_per_100g"][macro]/100
        mass=sum(g for _,g in inputs)
        if finished>mass or not min_g<=reference<=max_g:raise ValueError("Invalid recipe mass or portion: " + ident + f" input={mass}, finished={finished}, ref={reference}, range={min_g}-{max_g}")
        macro={k:round(v/finished*100,4) for k,v in total.items()}
        kcal=round(4*macro["protein"]+4*macro["carbs"]+9*macro["fat"],4);macro["fiber"]=None
        rows.append({"dish_id":ident,"name":name,"type":role,"group":role.lower(),"preparation_state":"raw_edible" if len(inputs)==1 and profiles[inputs[0][0]]["state"]=="raw_edible" else "ready" if role=="DRINK" else "cooked",
            "reference_grams":reference,"min_grams":min_g,"max_grams":max_g,"calories_per_100g":kcal,"macros_per_100g":macro,"ingredients":sorted(ingredient_tags),"meal_types":["breakfast","lunch","dinner"],"prep_minutes":5 if role=="DRINK" or len(inputs)==1 else 45 if role=="SOUP" else 30,
            "estimated":True,"active":True,"data_version":1,"provenance":{"source":"Ước lượng từ công thức tham khảo NutriFit","method":"sum(retained_edible_grams*assumed_macro_per100g/100)/assumed_finished_edible_grams*100; kcal=4P+4C+9F","confidence":"ENGINEERING_ESTIMATE_FOR_STUDENT_DEMO","ingredients_complete":True,
            "recipe":{"ingredients":details,"finished_edible_grams":finished,"servings":servings,"weight_basis":"ASSUMED_NOT_MEASURED","input_edible_grams":mass,"assumed_evaporation_or_discard_grams":round(mass-finished,2)},
            "limitations":["Rounded engineering ingredient estimates; no claim of food-table/laboratory verification.","Reference recipe only; edible meat excludes bones, fruit excludes peel/seeds, shellfish excludes shell.","Input state is declared; cooked stock is not raw weight. Finished yield and retained oil are assumed, not measured.","Water/ice is part of finished edible mass. Unsweetened tea/coffee trace macros are assumed negligible.","Fiber unknown. No sodium/allergy/cross-contamination certification; sauces refer to the declared reference recipe."]}})
    data=copy.deepcopy(base);data["format"]="nutrifit-vietnamese-demo-catalog150";data["dishes"]+=rows
    if len(data["dishes"])<150:raise ValueError("Insufficient real recipes")
    ids=[d["dish_id"] for d in data["dishes"]];names=[folded_name(d["name"]) for d in data["dishes"]]
    if len(ids)!=len(set(ids)) or len(names)!=len(set(names)):raise ValueError("Duplicate ID/name")
    # Normalized recipe signatures include ingredient identity, ratio and state, not just title.
    def signature(d):
        r=d["provenance"]["recipe"];return tuple(sorted((i["ingredient"],i["state"],round(i["retained_grams"]/r["finished_edible_grams"],5)) for i in r["ingredients"]))
    seen={}
    for d in data["dishes"]:
        sig=signature(d)
        if sig in seen:raise ValueError("Equivalent recipe: "+seen[sig]+" / "+d["dish_id"])
        seen[sig]=d["dish_id"]
    review={"before_count":77,"after_count":len(data["dishes"]),"legacy_count":63,"baseline_ids":[d["dish_id"] for d in base["dishes"]],"new_ids":[d["dish_id"] for d in rows],"new_by_role":dict(Counter(d["type"] for d in rows)),
        "not_added_equivalents":{"Thịt kho tàu":"vn_thit_kho_trung","Bún riêu":"vn_bun_rieu_cua","Bún thịt nướng":"vn_bun_thit_nuong","Miến gà":"breakfast_main_d4_o2","Bánh cuốn":"breakfast_main_d3_o1","Rau muống luộc":"vn_rau_muong_luoc","Khoai lang luộc/hấp":"sweet_potato"}}
    return data,review

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--write",action="store_true");args=parser.parse_args()
    data,review=prepare()
    if args.write:
        TARGET.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        MANIFEST.write_text(json.dumps(review,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"mode":"prepared" if args.write else "validate_only","total":review["after_count"],"added":len(review["new_ids"]),"by_role":review["new_by_role"],"database_writes":0}))
