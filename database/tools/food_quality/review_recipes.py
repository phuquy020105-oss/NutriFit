"""Document edible-state, served-mass design and per-recipe staging qualification; no kitchen measurements invented."""
from collections import Counter
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from build_provenance import ROOT, STAGING, KEYS

NON_SOUP_LARGE={"R044","R048","R050","R054","R057","R060"}
LARGE_NOTES={
 "R044":"350g cooked sweet potato +160g chicken +270g raw salad +30g peanuts;15g added dressing water. Large solid meal, not a soup-water explanation; needs practical serving review. No grams reduced without evidence.",
 "R047":"280g cooked rice served separately;200g added water consumed in lotus/mung/chicken soup. The836g total includes both rice and soup;636g excluding added water is NOT dry matter. Keep whole meal distinct from one bowl of soup.",
 "R048":"300g rice +160g cooked beef +330g cooked vegetables;20g sauce water. High vegetable and solid-food volume, not hidden broth. Needs practical plate review before release.",
 "R050":"300g rice +150g corn +150g tofu +100g egg +120g broccoli. Multiple starch/protein sides; only15g seasoning/oil. Needs practical serving review; not corrected merely to fit calories.",
 "R053":"200g rice separate from soup with220g cooked cabbage,140g tofu,100g boiled egg and200g retained added water. The871g is a full rice-plus-soup meal, not871g of dry solids.",
 "R054":"250g brown rice +130g chicken +120g mung +120g lotus +150g broccoli;20g sauce water. Several solid sides; needs practical plate/legume-volume review.",
 "R057":"220g rice +220g tofu +150g cooked mushrooms +180g green beans;30g retained sauce water. Large cooked-food meal; actual pan-water loss must be compensated or recalc final weights, not assumed zero.",
 "R060":"260g rice +150g beef +160g lotus +200g broccoli;20g sauce water. Large solid meal; cooked weights specified but practical plate size needs review.",
}

def build():
    catalog=json.loads((STAGING/"catalog-C-exploratory.json").read_text(encoding="utf-8"))
    foods={f["ref"]:f for f in catalog["foods"]}
    designs=json.loads((STAGING/"new-recipe-designs.json").read_text(encoding="utf-8"))
    reviews=[]
    for recipe in designs["recipes"]:
        ref=recipe["ref"]
        ingredients=recipe["ingredients"]
        mass=sum((Decimal(i["quantity_grams"]) for i in ingredients),Decimal(0))
        water=sum((Decimal(i["quantity_grams"]) for i in ingredients if i["food_ref"]=="F071"),Decimal(0))
        ready=sum((Decimal(i["quantity_grams"]) for i in ingredients if foods[i["food_ref"]].get("state")=="CHÍN"),Decimal(0))
        # Design target, not a measurement or a guessed evaporation/yield factor.
        review=dict(recipe_ref=ref,name=recipe["name"],meal_type=recipe["meal_type"],servings="1.00",
            quantity_changes=[],input_mass_basis="All ingredient grams are edible weights in the declared state, not purchased gross weights",
            listed_input_mass_g=format(mass,".2f"),separately_added_water_to_be_consumed_g=format(water,".2f"),
            mass_excluding_added_water_g=format(mass-water,".2f"),already_cooked_ingredient_mass_g=format(ready,".2f"),
            final_served_mass_design_target_g=format(mass,".2f"),final_served_mass_measured_g=None,
            evaporation_measured_g=None,drained_discard_mass_measured_g=None,kitchen_measured=False,
            mass_target_method="Retain every listed edible ingredient/sauce; use preweighed cooked foods; top up water after gentle reheating to the specified target. Dry-rice porridge retains the separately specified water. Targets are recipe design assumptions, not measured cooking yields.",
            yield_retention_method="No extra generic raw-to-cooked factor on source-cooked foods; no invented retention coefficients. Raw cereal is cooked with retained liquid. This is a component calculation with disclosed uncertainty from reheating/cooking, not an assay.",
            oil_method="Listed oil is the intended edible amount consumed with all sauce, not frying-bath input. No deep frying. If oil/sauce is left in the pan the delivered portion differs and must be weighed/recalculated.",
            portion_review_status="PENDING_PRACTICAL_PLATE_REVIEW" if ref in NON_SOUP_LARGE else "STAGING_DESIGN_REVIEWED_WITH_DISCLOSED_ASSUMPTIONS",
            note=LARGE_NOTES.get(ref,"Single meal design with explicit component weights; no automatic servings scaling. Not individualized dietary advice or proof of a measured serving."),
            image_is_illustrative_not_portion_evidence=True,
            nutritional_method_qualified_for_staging=ref not in NON_SOUP_LARGE,
            production_change_approved=False,
            ingredient_state_manifest=[dict(food_ref=i["food_ref"],quantity_grams=i["quantity_grams"],state=foods[i["food_ref"]].get("state"),name=foods[i["food_ref"]]["name"]) for i in ingredients])
        reviews.append(review)
    if Counter(r["meal_type"] for r in reviews)!=dict(BREAKFAST=10,LUNCH=10,DINNER=10):raise ValueError("Meal counts")
    output=dict(status="STAGING_DESIGN_REVIEW_NOT_PRODUCTION_APPROVAL",method_source="https://www.fao.org/4/y4705e/y4705e23.htm",
        catalog_sha256=hashlib.sha256((STAGING/"catalog-C-exploratory.json").read_bytes()).hexdigest(),
        new_recipes=30,staging_method_qualified=sum(r["nutritional_method_qualified_for_staging"] for r in reviews),
        pending_practical_plate_review=sorted(NON_SOUP_LARGE),measured_servings=0,
        invalid_rule_rejected="Mass greater than800g is not automatically wrong: soups R047/R053 include retained water and rice side; non-soup dishes need separate practical assessment.",recipes=reviews)
    (STAGING/"recipe-portion-review.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    print("30recipe mass/state reviews;24staging method-qualified;6large non-soup reviews pending;0production approvals")

if __name__=="__main__": build()
