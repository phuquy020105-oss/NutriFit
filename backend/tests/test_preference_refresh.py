"""V4 preference/refresh regression: current seed, SQLite memory, blocked AI."""
import copy
import json
import unittest
from unittest.mock import patch
from sqlalchemy import text
import test_catalog158 as base
from app.extensions import db
from app.services.meal_preferences import v4_preferences, validate_preferences, ingredients, violates
from app.services.meal_planner_v4 import (MealPlannerV4, candidate_pool, score,
    dish_bundle_signature, preference_rank, select_fallback_bundle)
from app.services.food_catalog_service import catalog_by_id, catalog_dishes, totals
from app.repositories.meal_repository import MealRepository
from app.services.module_errors import ModuleError


class PreferenceRefreshTests(unittest.TestCase):
    setUp = base.ExpandedCatalogTests.setUp
    tearDown = base.ExpandedCatalogTests.tearDown
    login_headers = base.ExpandedCatalogTests.login_headers
    generate = base.ExpandedCatalogTests.generate
    v4 = base.ExpandedCatalogTests.v4
    daily = base.ExpandedCatalogTests.daily
    choose = base.ExpandedCatalogTests.choose

    def test_names_aliases_case_spaces_and_duplicates(self):
        pairs = [("  GÀ ", "chicken"), ("ga", "chicken"), ("heo", "pork"),
            ("THỊT LỢN", "pork"), ("bò", "beef"), ("ca", "fish"),
            ("trứng", "egg"), ("đậu phộng", "peanut"), ("toi", "garlic"), ("cà chua", "tomato")]
        for name, expected in pairs:
            self.assertEqual(v4_preferences({"avoid":[name]},"lunch"), {"avoid":[expected]})
        self.assertEqual(v4_preferences({"avoid":["gà","ga","heo"]},"lunch")["avoid"],["chicken","pork"])
        self.assertNotIn("fish", ingredients({"ingredients":["tomato"]}))

    def test_unknown_ingredient_rejected_without_any_save(self):
        before = db.session.execute(text("SELECT COUNT(*) FROM MealSuggestions")).scalar()
        response = self.v4(preferences={"avoid":["abcxyz123"]})
        self.assertEqual(response.status_code,400)
        self.assertEqual(response.json["code"],"UNSUPPORTED_PREFERENCE")
        self.assertIn("abcxyz123",response.json["message"])
        self.assertEqual(db.session.execute(text("SELECT COUNT(*) FROM MealSuggestions")).scalar(),before)

    def test_soft_scores_on_equal_nutritional_candidates(self):
        original=next(d for d in catalog_dishes("lunch") if d["type"]=="PROTEIN")
        rows=[]
        for i,tag in enumerate(("chicken","pork","beef","egg")):
            d=copy.deepcopy(original);d.update(dish_id="controlled_"+str(i),ingredients=[tag]);rows.append(d)
        baseline=[score(d,"maintain",{}) for d in rows]
        self.assertEqual(len(set(baseline)),1)
        self.assertLess(score(rows[1],"maintain",{"dislikes":["pork"]}),baseline[1])
        self.assertGreater(score(rows[2],"maintain",{"prefer":["beef"]}),baseline[2])
        self.assertLess(score(rows[2],"maintain",{"dislikes":["beef"],"prefer":["beef"]}),baseline[2])
        with patch("app.services.meal_planner_v4.catalog_dishes",return_value=rows):
            for prefs in ({"dislikes":["pork"]},{"prefer":["beef"]},{"avoid":["chicken"],"dislikes":["pork"],"prefer":["beef"]}):
                pool=candidate_pool(prefs,"lunch","maintain","same")
                self.assertIn("controlled_1",[d["dish_id"] for d in pool])
                self.assertIn("controlled_2",[d["dish_id"] for d in pool])
                self.assertEqual(len(pool),3 if prefs.get("avoid") else 4)

    def test_declared_broth_hard_avoid_not_display_name(self):
        dish=copy.deepcopy(next(iter(catalog_by_id().values())))
        dish.update(name="Món rau không có tên thịt",ingredients=["chicken","tomato"])
        self.assertTrue(violates(dish,{"avoid":["chicken"]}))
        dish["ingredients"]=["tomato"]
        self.assertFalse(violates(dish,{"avoid":["fish"]}))

    def test_time_preferences_ignored_in_v4_but_legacy_contract_kept(self):
        self.assertEqual(v4_preferences({"preferEasy":True,"maxPrepMinutes":1,"avoid":["ga"]},"dinner"),{"avoid":["chicken"]})
        self.assertEqual(validate_preferences({"preferEasy":True,"maxPrepMinutes":20},"breakfast"),{"preferEasy":True,"maxPrepMinutes":20})
        kwargs=dict(target=700,macro_targets={"protein":43.8,"carbs":78.8,"fat":23.3})
        pool=candidate_pool({},"breakfast","maintain","time-compat",**kwargs)
        old=candidate_pool({"preferEasy":True,"maxPrepMinutes":1},"breakfast","maintain","time-compat",**kwargs)
        self.assertEqual(pool,old)

    def test_real_generate_refresh_changed_dishes_reload_and_intake_unchanged(self):
        prefs={"avoid":["gà"],"dislikes":["heo"],"prefer":["bò"]}
        before=self.daily();first=self.v4(preferences=prefs)
        self.assertEqual(first.status_code,200,first.json);meal=first.json["data"]
        self.assertEqual(self.v4(preferences=prefs).json["data"]["revision"],meal["revision"])
        refreshed=self.v4(forceRefresh=True,revision=meal["revision"],preferences=prefs)
        self.assertEqual(refreshed.status_code,200,refreshed.json)
        next_meal=refreshed.json["data"]
        self.assertNotEqual(dish_bundle_signature(meal["options"]),dish_bundle_signature(next_meal["options"]))
        self.assertTrue(refreshed.json["meta"]["changed"])
        for option in next_meal["options"]:
            self.assertEqual(totals(option["recipe"]["components"])["calories"],option["calories"])
            for part in option["recipe"]["components"]:
                self.assertFalse(violates(catalog_by_id()[part["dish_id"]],{"avoid":["chicken"]}))
        loaded=self.client.get("/api/meals/today",headers=self.headers).json["todayMeals"]["lunch"]
        self.assertEqual(loaded["revision"],next_meal["revision"])
        self.assertEqual(self.daily()["consumed"],before["consumed"])
        self.assertEqual(self.daily()["targets"],before["targets"])
        self.assertEqual(self.v4(forceRefresh=True,revision=meal["revision"],preferences=prefs).json["code"],"STALE_MEAL")

    def test_no_alternative_keeps_revision_and_saved_options(self):
        dishes=catalog_dishes("lunch")
        # Exactly three primaries and one required partner of each role.
        pool=[next(d for d in dishes if d["type"]==r) for r in ("CARB","VEGGIE")]
        pool += [d for d in dishes if d["type"]=="PROTEIN"][:3]
        with patch("app.services.meal_planner_v4.candidate_pool",return_value=pool):
            first=self.v4();self.assertEqual(first.status_code,200,first.json);meal=first.json["data"]
            again=self.v4(forceRefresh=True,revision=meal["revision"])
        self.assertEqual(again.status_code,200,again.json)
        self.assertEqual(again.json["meta"]["refresh_status"],"no_alternative")
        self.assertFalse(again.json["meta"]["changed"])
        self.assertEqual(again.json["data"],meal)
        self.assertEqual(db.session.execute(text("SELECT COUNT(*) FROM MealOption")).scalar(),3)

    def test_no_candidates_keeps_old_plan_and_does_not_relax_avoid(self):
        meal=self.v4().json["data"]
        with patch("app.services.meal_planner_v4.candidate_pool",return_value=[]):
            response=self.v4(forceRefresh=True,revision=meal["revision"],preferences={"avoid":["gà"]})
        self.assertEqual(response.status_code,422)
        self.assertEqual(response.json["code"],"INSUFFICIENT_MENUS")
        self.assertEqual(self.client.get("/api/meals/today",headers=self.headers).json["todayMeals"]["lunch"],meal)

    def test_conflicting_fields_never_override_avoid(self):
        response=self.v4(preferences={"avoid":["bò"],"dislikes":["bò"],"prefer":["bò"]})
        self.assertEqual(response.status_code,200,response.json)
        for option in response.json["data"]["options"]:
            for part in option["recipe"]["components"]:
                self.assertFalse(violates(catalog_by_id()[part["dish_id"]],{"avoid":["beef"]}))

    def test_reference_ingredient_mode_is_opt_in_and_never_ignores_declared_fish(self):
        import json
        from pathlib import Path
        source = Path(__file__).resolve().parents[2] / 'setup/seeds/vietnamese_expansion_2026.json'
        dishes = json.loads(source.read_text(encoding='utf-8'))['dishes']
        group = [d for d in dishes if d['type'] == 'PROTEIN' and 'lunch' in d['meal_types']]
        strict = v4_preferences({'avoid':['cá']}, 'lunch')
        reference = v4_preferences({'avoid':['cá'], 'ingredientMode':'reference'}, 'lunch')
        self.assertTrue(all(violates(d, strict) for d in group))
        self.assertGreaterEqual(sum(not violates(d, reference) for d in group), 15)
        self.assertTrue(all(violates(d, reference) for d in group if 'fish' in ingredients(d)))
        with self.assertRaises(Exception):
            validate_preferences({'ingredientMode':'unsafe'}, 'lunch')

    def test_catalog_only_generate_does_not_contact_gemini(self):
        with patch.object(self.app.extensions['nutrifit_gemini'], 'compose',
                          side_effect=AssertionError('Catalog-only must not contact Gemini')):
            response = self.v4(catalogOnly=True)
        self.assertEqual(response.status_code, 200, response.get_json())
        self.assertEqual(response.get_json()['meta']['source'], 'fallback')

    def test_apply_preferences_validation_is_quick_and_rejects_unknown_names(self):
        ok = self.client.post('/api/meals/validate-preferences', headers=self.headers, json={
            'mealType':'lunch','preferences':{'avoid':['cá'],'ingredientMode':'reference'}})
        self.assertEqual(ok.status_code, 200, ok.get_json())
        self.assertEqual(ok.get_json()['preferences']['avoid'], ['fish'])
        bad = self.client.post('/api/meals/validate-preferences', headers=self.headers, json={
            'mealType':'lunch','preferences':{'avoid':['món không có trong kho']}})
        self.assertEqual(bad.status_code, 400)

    def test_selected_plan_guard_unchanged(self):
        meal=self.v4().json["data"];picked=self.choose(meal,1).json["data"]
        response=self.v4(forceRefresh=True,revision=picked["revision"],preferences={"avoid":["gà"]})
        self.assertEqual(response.json["code"],"MEAL_DECIDED")

    def test_final_soft_selection_uses_actual_catalog_ingredients(self):
        options=[];catalog={}
        for i,tag in enumerate(("pork","beef","chicken","egg")):
            ident="equal_"+str(i);catalog[ident]={"ingredients":[tag]}
            options.append({"calories":700,"recipe":{"components":[{"dish_id":ident,"type":"PROTEIN","grams":100}],
                "calorie_adjustment":{"objective":{"total":.1},"worst_macro_error":0}}})
        chosen=select_fallback_bundle(options,"lunch",700,{"dislikes":["pork"]},catalog=catalog)
        self.assertNotIn("equal_0",[o["recipe"]["components"][0]["dish_id"] for o in chosen])
        chosen=select_fallback_bundle(options,"lunch",700,{"prefer":["beef"]},catalog=catalog)
        self.assertIn("equal_1",[o["recipe"]["components"][0]["dish_id"] for o in chosen])

    def test_repeated_provider_uses_genuine_new_fallback_and_truthful_source(self):
        with patch("app.services.meal_planner_v4.candidate_pool",return_value=catalog_dishes("lunch")):
            first=self.v4();self.assertEqual(first.status_code,200,first.json);meal=first.json["data"]
            raw={"choices":[{"title":o["title"],"reason":"Đề xuất thử nghiệm", "components":[{k:p[k] for k in ("type","dish_id","grams")} for p in o["recipe"]["components"]]} for o in meal["options"]]}
            with patch.object(self.app.extensions["nutrifit_gemini"],"compose",return_value=raw):
                response=self.v4(forceRefresh=True,revision=meal["revision"])
        self.assertEqual(response.status_code,200,response.json)
        self.assertEqual(response.json["meta"]["source"],"fallback")
        self.assertEqual(response.json["meta"]["fallback_reason"],"repeated_composition")
        self.assertNotEqual(dish_bundle_signature(response.json["data"]["options"]),dish_bundle_signature(meal["options"]))

    def test_saved_old_time_settings_do_not_block_cache_or_component_replacement(self):
        generated=self.v4("breakfast");self.assertEqual(generated.status_code,200,generated.json)
        meal=generated.json["data"];option=meal["options"][0];recipe=copy.deepcopy(option["recipe"])
        recipe["preferences"]={"preferEasy":True,"maxPrepMinutes":1}
        db.session.execute(text("UPDATE NutritionMealDetails SET RecipeJson=:recipe WHERE OptionId=:id"),{"recipe":json.dumps(recipe,ensure_ascii=False),"id":option["optionId"]});db.session.commit()
        loaded=self.client.get("/api/meals/today",headers=self.headers).json["todayMeals"]["breakfast"]
        cached=self.v4("breakfast");self.assertEqual(cached.status_code,200,cached.json)
        self.assertTrue(cached.json["meta"]["cached"])
        body={"mealType":"breakfast","optionId":option["optionId"],"componentType":"MAIN","revision":loaded["revision"]}
        suggestions=self.client.post("/api/meals/component-suggestions",headers=self.headers,json=body)
        self.assertEqual(suggestions.status_code,200,suggestions.json)
        dish=suggestions.json["data"]["choices"][0]
        replaced=self.client.post("/api/meals/replace-component",headers=self.headers,json={**body,"dishId":dish["dish_id"],"grams":dish["reference_grams"]})
        self.assertEqual(replaced.status_code,200,replaced.json)
        self.assertEqual(replaced.json["data"]["options"][0]["recipe"]["preferences"],{})
