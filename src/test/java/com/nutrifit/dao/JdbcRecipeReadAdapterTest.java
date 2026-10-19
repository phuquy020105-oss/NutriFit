package com.nutrifit.dao;

import com.nutrifit.dto.*;
import java.lang.reflect.Proxy;
import java.math.BigDecimal;
import java.sql.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class JdbcRecipeReadAdapterTest {
    Connection connection(boolean active){
        Map<String,Object> row=new HashMap<>(Map.of("recipe_id",7L,"name","Phở bò","meal_type","BREAKFAST","base_servings",new BigDecimal("1.00"),"image_url","/assets/images/recipes/pho-bo.webp","food_id",9L,"food_active",active,"quantity_grams",new BigDecimal("125.00")));
        for(String key:List.of("calories","protein","carbs","fat","fiber"))row.put(key+"_per_100g",new BigDecimal(key.equals("calories")?"200.000":"4.000"));
        return (Connection)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{Connection.class},(p,m,a)->{
            assertEquals("prepareStatement",m.getName());assertTrue(((String)a[0]).contains("r.image_url"));
            return Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{PreparedStatement.class},(p2,m2,a2)->switch(m2.getName()){
                case "setLong","close" -> null;
                case "executeQuery" -> {
                    int[] cursor={-1};
                    yield Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ResultSet.class},(p3,m3,a3)->switch(m3.getName()){
                        case "next" -> ++cursor[0]==0;
                        case "getLong" -> row.get((String)a3[0]);
                        case "getString" -> row.get((String)a3[0]);
                        case "getBigDecimal" -> row.get((String)a3[0]);
                        case "getBoolean" -> row.get((String)a3[0]);
                        case "wasNull" -> false;
                        case "close" -> null;
                        default -> throw new AssertionError(m3.getName());
                    });
                }
                default -> throw new AssertionError(m2.getName());
            });
        });
    }
    @Test void bothReadPathsCarryImageWithoutChangingNutrition()throws Exception{
        var adapter=new JdbcRecipeReadAdapter();
        var input=adapter.findNutritionInput(connection(true),7).orElseThrow();
        var candidate=adapter.listCandidates(connection(true)).getFirst();
        assertEquals("/assets/images/recipes/pho-bo.webp",input.imageUrl());assertEquals(input.imageUrl(),candidate.imageUrl());
        assertEquals(new BigDecimal("250.000"),candidate.perServing().caloriesKcal());
        assertEquals(new BigDecimal("5.000"),candidate.perServing().fiberG());
    }
    @Test void imagesNeverMakeInactiveFoodEligible()throws Exception{
        var adapter=new JdbcRecipeReadAdapter();
        assertTrue(adapter.findNutritionInput(connection(false),7).isEmpty());
        assertTrue(adapter.listCandidates(connection(false)).isEmpty());
    }
}
