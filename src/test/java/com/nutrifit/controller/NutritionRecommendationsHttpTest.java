package com.nutrifit.controller;

import com.nutrifit.dto.*;
import com.nutrifit.model.*;
import com.nutrifit.service.*;
import com.nutrifit.util.Csrf;
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import java.io.*;
import java.lang.reflect.Proxy;
import java.math.BigDecimal;
import java.time.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** HTTP/session doubles only. No login endpoint, real account, network or database. */
class NutritionRecommendationsHttpTest {
    @Test void freeGetIsPreviewOnlyAndRepeatedSaveIsIdempotentWithinSession() throws Exception {
        Fixture f=new Fixture();
        f.servlet.doGet(f.request,f.response);
        assertEquals(0,f.writes);
        f.params.put("csrfToken",Csrf.token(f.request));f.params.put("action","save");
        var draft=(MealRecommendationsServlet.Draft)f.sessionValues.get(MealRecommendationsServlet.DRAFT);
        f.params.put("suggestionToken",draft.token);
        f.params.put("userId","999");f.params.put("recipeId","999");f.params.put("premium","true");
        for(var type:MealEntry.MealType.values())f.params.put("servings_"+type,"1.25");
        f.servlet.doPost(f.request,f.response);f.servlet.doPost(f.request,f.response);
        assertEquals(1,f.writes);
        assertEquals(42,f.savedUser);
        assertEquals(new BigDecimal("1.25"),f.amounts.get(MealEntry.MealType.DINNER));
        assertTrue(draft.saved);
    }
    @Test void portionPreviewReturnsAllMacrosAndNeverWritesJournal() throws Exception {
        Fixture f=new Fixture();f.servlet.doGet(f.request,f.response);
        var draft=(MealRecommendationsServlet.Draft)f.sessionValues.get(MealRecommendationsServlet.DRAFT);
        f.params.put("csrfToken",Csrf.token(f.request));f.params.put("action","preview");f.params.put("suggestionToken",draft.token);
        for(var type:MealEntry.MealType.values())f.params.put("servings_"+type,"1");
        f.servlet.doPost(f.request,f.response);
        assertEquals(0,f.writes);assertEquals(200,f.status);
        String json=f.body.toString();
        String quote=Character.toString(34);
        for(String field:List.of("meals","caloriesKcal","proteinG","carbsG","fatG","fiberG","total","targetKcal","differenceKcal","personalized")) {
            assertTrue(json.contains(quote+field+quote),field);
        }
        assertTrue(json.contains(quote+"personalized"+quote+":false"));
    }

    @Test void missingCsrfUnauthenticatedOrOtherAccountCannotSave() throws Exception {
        Fixture f=new Fixture();f.servlet.doGet(f.request,f.response);
        f.params.put("action","save");
        f.servlet.doPost(f.request,f.response);assertEquals(403,f.status);assertEquals(0,f.writes);
        f.params.put("csrfToken",Csrf.token(f.request));
        f.sessionValues.put("userId",43L);
        var draft=(MealRecommendationsServlet.Draft)f.sessionValues.get(MealRecommendationsServlet.DRAFT);
        f.params.put("suggestionToken",draft.token);
        f.servlet.doPost(f.request,f.response);assertEquals(403,f.status);assertEquals(0,f.writes);
        f.sessionValues.remove("userId");f.servlet.doPost(f.request,f.response);assertEquals(401,f.status);
    }
    @Test void staleSuggestionAndInvalidPortionAreRejected() throws Exception {
        Fixture f=new Fixture();f.servlet.doGet(f.request,f.response);
        var draft=(MealRecommendationsServlet.Draft)f.sessionValues.get(MealRecommendationsServlet.DRAFT);
        f.params.put("csrfToken",Csrf.token(f.request));f.params.put("action","save");f.params.put("suggestionToken",draft.token);
        for(var type:MealEntry.MealType.values())f.params.put("servings_"+type,"0");
        f.servlet.doPost(f.request,f.response);assertEquals(400,f.status);assertEquals(0,f.writes);
        f.sessionValues.put(MealRecommendationsServlet.DRAFT,new MealRecommendationsServlet.Draft(draft.token,
                draft.suggestion,Instant.now().minusSeconds(1900)));
        f.servlet.doPost(f.request,f.response);assertEquals(400,f.status);assertEquals(0,f.writes);
    }
    @Test void saveFailureCannotBeAutomaticallyReplayed() throws Exception {
        Fixture f=new Fixture();f.servlet.doGet(f.request,f.response);f.failSave=true;
        var draft=(MealRecommendationsServlet.Draft)f.sessionValues.get(MealRecommendationsServlet.DRAFT);
        f.params.put("csrfToken",Csrf.token(f.request));f.params.put("action","save");f.params.put("suggestionToken",draft.token);
        for(var type:MealEntry.MealType.values())f.params.put("servings_"+type,"1");
        f.servlet.doPost(f.request,f.response);assertEquals(400,f.status);
        f.servlet.doPost(f.request,f.response);assertEquals(1,f.writes);
    }
    @Test void directPreferencePostPassesThroughServiceAuthorizationAndCsrf() throws Exception {
        Fixture f=new Fixture();f.params.put("csrfToken",Csrf.token(f.request));
        f.params.put("action","save");f.params.put("foodId","7");f.params.put("type","LIKE");
        final int[] attempts={0};
        FoodPreferenceServlet preferences=new FoodPreferenceServlet(new FoodPreferenceService(){
            @Override public void setPreference(long user,long food,FoodPreference.PreferenceType type){
                assertEquals(42,user);attempts[0]++;throw new SecurityException("PREMIUM_REQUIRED");
            }
            @Override public void removePreference(long user,long food){
                attempts[0]++;throw new SecurityException("PREMIUM_REQUIRED");
            }
        });
        preferences.doPost(f.request,f.response);assertEquals(403,f.status);assertEquals(1,attempts[0]);
        f.params.put("action","delete");preferences.doPost(f.request,f.response);
        assertEquals(403,f.status);assertEquals(2,attempts[0]);
        f.params.remove("csrfToken");preferences.doPost(f.request,f.response);assertEquals(2,attempts[0]);
    }
    private static class Fixture {
        final Map<String,Object> sessionValues=new HashMap<>(),attributes=new HashMap<>();
        final Map<String,String> params=new HashMap<>();
        int status=200,writes;long savedUser;boolean failSave;
        Map<MealEntry.MealType,BigDecimal> amounts;
        final StringWriter body=new StringWriter();
        final HttpSession session=(HttpSession)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{HttpSession.class},
                (p,m,a)->switch(m.getName()){
                    case "getAttribute" -> sessionValues.get(a[0]);
                    case "setAttribute" -> {sessionValues.put((String)a[0],a[1]);yield null;}
                    default -> throw new AssertionError(m.getName());
                });
        final RequestDispatcher dispatcher=new RequestDispatcher(){
            @Override public void forward(ServletRequest req,ServletResponse resp){}
            @Override public void include(ServletRequest req,ServletResponse resp){}
        };
        final HttpServletRequest request=(HttpServletRequest)Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class<?>[]{HttpServletRequest.class},(p,m,a)->switch(m.getName()){
                    case "getSession" -> {assertArrayEquals(new Object[]{false},a);yield session;}
                    case "getParameter" -> params.get(a[0]);
                    case "setAttribute" -> {attributes.put((String)a[0],a[1]);yield null;}
                    case "getRequestDispatcher" -> dispatcher;
                    case "getContextPath" -> "";
                    case "setCharacterEncoding" -> null;
                    default -> throw new AssertionError(m.getName());
                });
        final HttpServletResponse response=(HttpServletResponse)Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class<?>[]{HttpServletResponse.class},(p,m,a)->switch(m.getName()){
                    case "sendError","setStatus" -> {status=(int)a[0];yield null;}
                    case "sendRedirect","setContentType" -> null;
                    case "getWriter" -> new PrintWriter(body);
                    default -> throw new AssertionError(m.getName());
                });
        final MealSuggestion suggestion=new MealSuggestion(42,LocalDate.now(),new BigDecimal("2400"),false,
                Arrays.stream(MealEntry.MealType.values()).map(t->new SuggestedMeal(t.ordinal()+1,"Recipe",t,
                        BigDecimal.ONE,new NutritionFacts(new BigDecimal("800"),BigDecimal.TEN,
                        BigDecimal.TEN,BigDecimal.TEN,BigDecimal.ONE))).toList());
        final MealRecommendationService recommendations=new MealRecommendationService(){
            @Override public MealSuggestion recommendDay(long user){return suggestion;}
            @Override public MealSuggestion refresh(long user,MealSuggestion s,Map<MealEntry.MealType,BigDecimal> amounts){return s;}
        };
        final MealPlannerService planner=new MealPlannerService(){
            @Override public MealSuggestion saveSuggestion(long user,MealSuggestion s,Map<MealEntry.MealType,BigDecimal> servings){
                savedUser=user;amounts=servings;writes++;
                if(failSave)throw new IllegalArgumentException("injected failure");
                return s;
            }
        };
        final MealRecommendationsServlet servlet=new MealRecommendationsServlet(recommendations,planner);
        Fixture(){
            sessionValues.put("userId",42L);sessionValues.put("authVersion",1L);
            sessionValues.put("role","USER");sessionValues.put("fullName","Unit test fixture");
        }
    }
}
