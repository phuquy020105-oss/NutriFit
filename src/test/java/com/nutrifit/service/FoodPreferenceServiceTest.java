package com.nutrifit.service;

import com.nutrifit.config.FeatureCatalog;
import com.nutrifit.dao.*;
import com.nutrifit.model.*;
import java.lang.reflect.Proxy;
import java.sql.*;
import java.time.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class FoodPreferenceServiceTest {
    @Test void freeAndExpiredCannotSaveOrDeleteEvenWithDirectServiceCalls() {
        Fixture f = new Fixture();
        for (FoodPreference.PreferenceType type : FoodPreference.PreferenceType.values()) {
            assertThrows(SecurityException.class, () -> f.service.setPreference(42, 7, type));
        }
        assertThrows(SecurityException.class, () -> f.service.removePreference(42, 7));
        assertEquals(0,f.writes);
        assertEquals(0,f.foodChecks);
    }
    @Test void premiumCanLikeDislikeChangeAndDeleteOnlyOwnPreferences() throws Exception {
        Fixture f = new Fixture(); f.premium=true;
        f.service.setPreference(42,7,FoodPreference.PreferenceType.LIKE);
        f.service.setPreference(42,7,FoodPreference.PreferenceType.DISLIKE);
        f.service.removePreference(42,7);
        assertEquals(List.of("42:7:LIKE","42:7:DISLIKE","42:7:delete"),f.operations);
    }
    @Test void invalidInputAndInactiveIngredientDoNotWrite() {
        Fixture f = new Fixture(); f.premium=true; f.active=false;
        assertThrows(IllegalArgumentException.class, () -> f.service.setPreference(42,7,FoodPreference.PreferenceType.LIKE));
        assertThrows(IllegalArgumentException.class, () -> f.service.setPreference(42,0,FoodPreference.PreferenceType.LIKE));
        assertThrows(SecurityException.class, () -> f.service.removePreference(0,7));
        assertEquals(0,f.writes);
    }
    @Test void catalogPremiumFeaturesOnlyDescribePreferenceManagementAndPersonalization() {
        for (FeatureCode code : List.of(FeatureCode.NUTRITION_PREFERENCE_EDIT,FeatureCode.NUTRITION_PREFERENCE_RECOMMEND)) {
            assertEquals("PREMIUM",FeatureCatalog.describe(code,false).requiredTier());
            assertFalse(FeatureCatalog.describe(code,false).unlocked());
            assertTrue(FeatureCatalog.describe(code,true).unlocked());
        }
    }
    private static class Fixture {
        boolean premium, active=true; int writes,foodChecks;
        final List<String> operations=new ArrayList<>();
        final Connection connection=(Connection) Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class<?>[]{Connection.class},(p,m,a)-> {
                    if (m.getName().equals("close")) return null;
                    throw new AssertionError("Unexpected JDBC: "+m.getName());
                });
        final FoodPreferenceDAO dao=new FoodPreferenceDAO() {
            @Override public boolean isActiveFood(Connection c,long food){foodChecks++;return active;}
            @Override public void upsert(Connection c,long user,long food,FoodPreference.PreferenceType type){
                writes++;operations.add(user+":"+food+":"+type);
            }
            @Override public void delete(Connection c,long user,long food){writes++;operations.add(user+":"+food+":delete");}
        };
        final NutritionUserReadDAO users=new NutritionUserReadDAO(){
            @Override public boolean hasPremiumAccess(Connection c,long user,LocalDateTime now){assertEquals(42,user);return premium;}
        };
        final FoodPreferenceService service=new FoodPreferenceService(dao,new FoodCatalogDAO(),users,
                ()->connection,MealRecommendationServiceTest.CLOCK);
    }
}
