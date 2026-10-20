package com.nutrifit.service;

import com.nutrifit.dto.*;
import com.nutrifit.model.MealEntry;
import com.nutrifit.util.JsonLite;
import java.math.BigDecimal;
import java.nio.file.*;
import java.util.*;

/** Loads the committed catalogue verbatim; no invented nutrients or database connection. */
final class RealCatalog {
    @SuppressWarnings("unchecked")
    static List<RecipeNutritionInput> load() throws Exception {
        return load(Path.of("database/seed/catalog.json"));
    }
    @SuppressWarnings("unchecked")
    static List<RecipeNutritionInput> load(Path path) throws Exception {
        Map<String,Object> json=(Map<String,Object>)JsonLite.parse(Files.readString(path));
        Map<String,NutritionFacts> foods=new HashMap<>();
        for(var item:(List<Map<String,Object>>)json.get("foods")) {
            Map<String,String> n=(Map<String,String>)item.get("nutrients");
            foods.put((String)item.get("ref"),new NutritionFacts(d(n,"calories_per_100g"),d(n,"protein_per_100g"),
                    d(n,"carbs_per_100g"),d(n,"fat_per_100g"),d(n,"fiber_per_100g")));
        }
        List<RecipeNutritionInput> result=new ArrayList<>();
        for(var r:(List<Map<String,Object>>)json.get("recipes")) {
            List<IngredientNutritionLine> lines=new ArrayList<>();
            for(var i:(List<Map<String,Object>>)r.get("ingredients")) {
                String ref=(String)i.get("food_ref");
                lines.add(new IngredientNutritionLine(foodFixtureId(ref),new BigDecimal((String)i.get("quantity_grams")),foods.get(ref)));
            }
            result.add(new RecipeNutritionInput(Long.parseLong(((String)r.get("ref")).substring(1)),(String)r.get("name"),
                    MealEntry.MealType.valueOf((String)r.get("meal_type")),new BigDecimal((String)r.get("base_servings")),lines,(String)r.get("image_url")));
        }
        return result;
    }
    // Stable in-memory fixture keys only; actual JDBC migrations resolve generated IDs by checked names.
    private static long foodFixtureId(String ref) {
        if (!ref.matches("[FN][0-9]{3}")) throw new IllegalArgumentException("Unknown test catalog reference");
        return (ref.charAt(0)=='N'?10000:0)+Long.parseLong(ref.substring(1));
    }
    private static BigDecimal d(Map<String,String> n,String key){return new BigDecimal(n.get(key));}
}
