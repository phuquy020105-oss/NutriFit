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
        Map<String,Object> json=(Map<String,Object>)JsonLite.parse(Files.readString(Path.of("database/seed/vietnamese_catalog.json")));
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
                lines.add(new IngredientNutritionLine(Long.parseLong(ref.substring(1)),new BigDecimal((String)i.get("quantity_grams")),foods.get(ref)));
            }
            result.add(new RecipeNutritionInput(Long.parseLong(((String)r.get("ref")).substring(1)),(String)r.get("name"),
                    MealEntry.MealType.valueOf((String)r.get("meal_type")),new BigDecimal((String)r.get("base_servings")),lines));
        }
        return result;
    }
    private static BigDecimal d(Map<String,String> n,String key){return new BigDecimal(n.get(key));}
}
