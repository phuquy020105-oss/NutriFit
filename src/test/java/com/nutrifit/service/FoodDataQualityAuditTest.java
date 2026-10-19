package com.nutrifit.service;

import com.nutrifit.dto.*;
import com.nutrifit.model.MealEntry;
import com.nutrifit.util.JsonLite;
import java.math.BigDecimal;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Offline evidence audit. Missing source facts never become zero or an old estimate. */
class FoodDataQualityAuditTest {
    static final Path STAGING = Path.of("database/staging/food-quality-v1");
    static final List<String> KEYS = List.of("calories_per_100g", "protein_per_100g",
            "carbs_per_100g", "fat_per_100g", "fiber_per_100g");
    static final BigDecimal ONE = new BigDecimal("1.00");
    final NutritionCalculator calculator = new NutritionCalculator();

    @SuppressWarnings("unchecked")
    static Map<String,Object> object(Object value) { return (Map<String,Object>) value; }
    @SuppressWarnings("unchecked")
    static List<Map<String,Object>> rows(Object value) { return (List<Map<String,Object>>) value; }
    static Map<String,Object> read(Path path) throws Exception {
        return object(JsonLite.parse(Files.readString(path)));
    }
    static Map<String,Map<String,Object>> evidence() throws Exception {
        Map<String,Map<String,Object>> result = new LinkedHashMap<>();
        for (var row : rows(read(STAGING.resolve("food-provenance.json")).get("foods"))) {
            assertNull(result.put((String) row.get("food_ref"), row), "Duplicate source food reference");
        }
        return result;
    }
    static NutritionFacts sourceFacts(Map<String,Object> food) {
        var nutrients = object(food.get("nutrients"));
        List<BigDecimal> values = new ArrayList<>();
        for (String key : KEYS) {
            var row = object(nutrients.get(key));
            assertEquals(row.get("value") == null, "MISSING".equals(row.get("status")));
            if (row.get("value") == null) return null;
            values.add(new BigDecimal((String) row.get("value")));
        }
        return new NutritionFacts(values.get(0), values.get(1), values.get(2), values.get(3), values.get(4));
    }
    static Map<String,Object> facts(NutritionFacts n) {
        var result = new LinkedHashMap<String,Object>();
        var values = List.of(n.caloriesKcal(), n.proteinG(), n.carbsG(), n.fatG(), n.fiberG());
        for (int i=0; i<KEYS.size(); i++) result.put(KEYS.get(i).replace("_per_100g", ""), values.get(i).toPlainString());
        return result;
    }
    static String encode(Object value) {
        if (value == null) return "null";
        if (value instanceof String s) return JsonLite.quote(s);
        if (value instanceof Map<?,?> map) return "{" + String.join(",", map.entrySet().stream()
                .map(e -> JsonLite.quote(e.getKey().toString()) + ":" + encode(e.getValue())).toList()) + "}";
        if (value instanceof Collection<?> list) return "[" + String.join(",", list.stream().map(FoodDataQualityAuditTest::encode).toList()) + "]";
        return value.toString();
    }

    @Test void auditAllOriginalRecipesUsingTheProductionCalculator() throws Exception {
        var canonical = read(Path.of("database/seed/vietnamese_catalog.json"));
        var provenance = evidence();
        String catalogHash = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                .digest(Files.readAllBytes(Path.of("database/seed/vietnamese_catalog.json"))));
        assertEquals(catalogHash, read(STAGING.resolve("food-provenance.json")).get("canonical_sha256"),
                "Stale evidence cannot be applied to a different catalog");
        assertEquals(82, provenance.size());
        var baseline = RealCatalog.load();
        assertEquals(30, baseline.size());
        List<Map<String,Object>> audit = new ArrayList<>();
        int links = 0, complete = 0;
        for (var recipe : rows(canonical.get("recipes"))) {
            String ref = (String) recipe.get("ref");
            long id = Long.parseLong(ref.substring(1));
            var beforeInput = baseline.stream().filter(r -> r.recipeId() == id).findFirst().orElseThrow();
            var before = calculator.calculate(beforeInput, ONE);
            List<IngredientNutritionLine> corrected = new ArrayList<>();
            List<String> missing = new ArrayList<>();
            List<Map<String,Object>> ingredientAudit = new ArrayList<>();
            BigDecimal grams = BigDecimal.ZERO;
            for (var ingredient : rows(recipe.get("ingredients"))) {
                String foodRef = (String) ingredient.get("food_ref");
                var food = provenance.get(foodRef);
                assertNotNull(food, "Every ingredient must have a provenance entry");
                BigDecimal quantity = new BigDecimal((String) ingredient.get("quantity_grams"));
                assertTrue(quantity.signum() > 0);
                grams = grams.add(quantity);
                var source = sourceFacts(food);
                if (source == null) missing.add(foodRef);
                else corrected.add(new IngredientNutritionLine(Long.parseLong(foodRef.substring(1)), quantity, source));
                var item = new LinkedHashMap<String,Object>();
                item.put("food_ref", foodRef); item.put("state", food.get("state"));
                item.put("grams_before", quantity.toPlainString()); item.put("grams_proposed", null);
                item.put("source_complete", source != null); item.put("source", food.get("source"));
                item.put("gram_change_reason", "No measured yield/retained oil or replacement evidence; retain current grams");
                ingredientAudit.add(item);
                links++;
            }
            var row = new LinkedHashMap<String,Object>();
            row.put("recipe_ref", ref); row.put("name", recipe.get("name"));
            row.put("meal_type", recipe.get("meal_type")); row.put("base_servings", recipe.get("base_servings"));
            row.put("listed_ingredient_grams", grams.toPlainString()); row.put("measured_final_portion_grams", null);
            row.put("before", facts(before));
            row.put("source_complete", missing.isEmpty()); row.put("missing_food_refs", missing);
            if (missing.isEmpty()) {
                var input = new RecipeNutritionInput(id, (String) recipe.get("name"),
                        MealEntry.MealType.valueOf((String) recipe.get("meal_type")),
                        new BigDecimal((String) recipe.get("base_servings")), corrected);
                var after = calculator.calculate(input, ONE);
                row.put("source_comparison", facts(after));
                var delta = new NutritionFacts(after.caloriesKcal().subtract(before.caloriesKcal()).abs(),
                        after.proteinG().subtract(before.proteinG()).abs(), after.carbsG().subtract(before.carbsG()).abs(),
                        after.fatG().subtract(before.fatG()).abs(), after.fiberG().subtract(before.fiberG()).abs());
                row.put("absolute_difference", facts(delta));
                complete++;
            } else {
                row.put("source_comparison", null); row.put("absolute_difference", null);
            }
            row.put("ingredients", ingredientAudit);
            row.put("cooking_instructions", recipe.get("instructions"));
            row.put("yield_or_retention_applied", false);
            row.put("production_change_approved", false);
            row.put("quality", missing.isEmpty() ? "SOURCE_COMPARISON_ONLY_PREPARATION_UNVERIFIED" : "INCOMPLETE_SOURCE_DO_NOT_MIGRATE");
            audit.add(row);
        }
        assertEquals(383, links);
        assertEquals(30, audit.size());
        var output = new LinkedHashMap<String,Object>();
        output.put("status", "STAGING_ONLY_NO_DATABASE_CONNECTION");
        output.put("canonical_sha256", catalogHash);
        output.put("provenance_sha256", HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                .digest(Files.readAllBytes(STAGING.resolve("food-provenance.json")))));
        output.put("recipe_count", audit.size()); output.put("ingredient_count", links);
        output.put("source_complete_recipe_count", complete); output.put("recipes", audit);
        Path target = Path.of("target/food-quality"); Files.createDirectories(target);
        Files.writeString(target.resolve("recipe-audit.json"), encode(output) + "\n");
    }

    @Test void sourceBasedRiceAndDriedFungusRegressionKeepsEdibleStateAndFiber() throws Exception {
        var foods = evidence();
        var recipe = new RecipeNutritionInput(1L, "Offline source calculation", MealEntry.MealType.LUNCH, ONE,
                List.of(new IngredientNutritionLine(1L, new BigDecimal("100"), sourceFacts(foods.get("F001"))),
                        new IngredientNutritionLine(59L, new BigDecimal("2"), sourceFacts(foods.get("F059")))));
        var result = calculator.calculate(recipe, ONE);
        assertEquals(new BigDecimal("135.680"), result.caloriesKcal());
        assertEquals(new BigDecimal("2.875"), result.proteinG());
        assertEquals(new BigDecimal("27.828"), result.carbsG());
        assertEquals(new BigDecimal("0.295"), result.fatG());
        assertEquals(new BigDecimal("1.802"), result.fiberG());
    }

    @Test void exploratoryExpansionCannotBeMistakenForProductionApproval() throws Exception {
        var original=read(Path.of("database/seed/vietnamese_catalog.json"));
        var expanded=read(STAGING.resolve("catalog-C-exploratory.json"));
        assertEquals(Boolean.FALSE,object(expanded.get("quality_gate")).get("production_write_permitted"));
        var foods=rows(expanded.get("foods")); var recipes=rows(expanded.get("recipes"));
        assertEquals(100,foods.size()); assertEquals(60,recipes.size());
        assertEquals(607,recipes.stream().mapToInt(r->rows(r.get("ingredients")).size()).sum());
        var baseline=rows(original.get("recipes"));
        for(int i=0;i<30;i++) {
            var old=baseline.get(i); var kept=recipes.get(i);
            for(String key:List.of("ref","name","meal_type","base_servings","instructions","ingredients"))
                assertEquals(old.get(key),kept.get(key),"Original recipe contract/grams must remain intact");
            assertNotNull(kept.get("image_url"));
        }
        for(var recipe:recipes.subList(30,60)) {
            assertEquals("1.00",recipe.get("base_servings"));
            assertEquals(Boolean.FALSE,recipe.get("production_change_approved"));
            assertNull(recipe.get("image_url"),"Unavailable image uses honest fallback, never another dish photo");
        }
        for(var type:MealEntry.MealType.values()) assertEquals(20,recipes.stream()
                .filter(r->type.name().equals(r.get("meal_type"))).count());
        assertEquals(60,RealCatalog.load(STAGING.resolve("catalog-C-exploratory.json")).size());
    }

    @Test void expandedDesignNutritionUsesOneServingAndReportsLargePortionReview() throws Exception {
        var all=RealCatalog.load(STAGING.resolve("catalog-C-exploratory.json"));
        List<Map<String,Object>> output=new ArrayList<>();
        for(var recipe:all.subList(30,60)) {
            var n=calculator.calculate(recipe,ONE);
            assertTrue(n.caloriesKcal().signum()>0);
            assertEquals(3,n.caloriesKcal().scale());
            BigDecimal grams=recipe.ingredients().stream().map(IngredientNutritionLine::quantityGrams)
                    .reduce(BigDecimal.ZERO,BigDecimal::add);
            var row=new LinkedHashMap<String,Object>();
            row.put("recipe_ref",String.format(Locale.ROOT,"R%03d",recipe.recipeId()));
            row.put("name",recipe.name());row.put("meal_type",recipe.mealType().name());
            row.put("servings","1.00");row.put("listed_ingredient_grams",grams.toPlainString());
            row.put("nutrition",facts(n));row.put("large_portion_review",grams.compareTo(new BigDecimal("800"))>0);
            row.put("production_change_approved",false);output.add(row);
        }
        assertEquals(30,output.size());
        Path out=Path.of("target/food-quality");Files.createDirectories(out);
        Files.writeString(out.resolve("new-recipe-nutrition.json"),encode(output)+"\n");
    }

    @Test void incompleteSourcesCannotBePassedToTheCalculatorAsOldEstimates() throws Exception {
        var foods = evidence();
        assertNull(sourceFacts(foods.get("F025")), "USDA shrimp record lacks fiber; must not invent a zero");
        assertNull(sourceFacts(foods.get("F058")), "INMU resolves culantro identity but still lacks carbs/fiber");
        assertNull(sourceFacts(foods.get("F011")), "A fat-rich crossbred fillet cannot silently replace lean boiled tenderloin");
    }
    @Test void newlySourcedBellyIsActuallyBoiledAndMissingFactsStillStayMissing() throws Exception {
        var foods=evidence();
        var belly=foods.get("F018");
        assertEquals("974",object(belly.get("source")).get("record_id"));
        assertEquals("Pork, belly, boiled",object(belly.get("source")).get("description"));
        assertEquals(new BigDecimal("428"),sourceFacts(belly).caloriesKcal());
        assertEquals(new BigDecimal("38.20"),sourceFacts(belly).fatG());
        assertFalse((Boolean)belly.get("production_change_approved"));
        assertNull(sourceFacts(foods.get("F025")),"Unrelated shrimp fiber must not be mixed into USDA record");
    }

}
