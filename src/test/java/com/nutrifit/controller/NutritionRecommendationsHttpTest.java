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
        for(var type:MealEntry.MealType.values())f.params.put("servings_"+type,"1.5");
        f.servlet.doPost(f.request,f.response);f.servlet.doPost(f.request,f.response);
        assertEquals(1,f.writes);
        assertEquals(42,f.savedUser);
        assertEquals(new BigDecimal("1.00"),f.amounts.get(MealEntry.MealType.DINNER));
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
        for(String field:List.of("meals","caloriesKcal","proteinG","carbsG","fatG","fiberG","total","targetKcal","differenceKcal","personalized","recordedToday","projectedDay","recordedMealCount","projectedDifferenceKcal","exceedsTarget")) {
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
        // Even invalid posted amounts are ignored; expiry still rejects before a save.
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
    @Test void postedPortionsAreIgnoredOnPreviewAndSave() throws Exception {
        for (String action:List.of("preview","save")) for (String amount:List.of("1.32","0.89","1.53","0.25","3")) {
            Fixture f=new Fixture();f.servlet.doGet(f.request,f.response);
            var draft=(MealRecommendationsServlet.Draft)f.sessionValues.get(MealRecommendationsServlet.DRAFT);
            f.params.put("csrfToken",Csrf.token(f.request));f.params.put("action",action);f.params.put("suggestionToken",draft.token);
            for (var type:MealEntry.MealType.values())f.params.put("servings_"+type,amount);
            f.servlet.doPost(f.request,f.response);
            assertEquals(action.equals("save")?1:0,f.writes);
            if (action.equals("save")) assertTrue(f.amounts.values().stream().allMatch(n -> n.equals(new BigDecimal("1.00"))));
        }
    }
    @Test void pageReloadAndPostSaveRedirectKeepNonceAndNeverResave() throws Exception {
        Fixture f=new Fixture();f.servlet.doGet(f.request,f.response);
        var draft=(MealRecommendationsServlet.Draft)f.sessionValues.get(MealRecommendationsServlet.DRAFT);
        f.servlet.doGet(f.request,f.response);
        assertSame(draft,f.sessionValues.get(MealRecommendationsServlet.DRAFT));assertEquals(1,f.generated);
        f.params.put("csrfToken",Csrf.token(f.request));f.params.put("action","save");f.params.put("suggestionToken",draft.token);
        f.servlet.doPost(f.request,f.response);
        assertEquals("/nutrition/recommendations?message=suggested",f.redirect);
        f.params.put("message","suggested");f.servlet.doGet(f.request,f.response);
        assertEquals(true,f.attributes.get("suggestionSaved"));assertNotNull(f.attributes.get("notice"));
        f.servlet.doPost(f.request,f.response);assertEquals(1,f.writes);assertEquals(1,f.generated);
    }
    @Test void regenerationRequiresCsrfReplacesNonceAndNeverWritesMeals() throws Exception {
        Fixture f=new Fixture();f.servlet.doGet(f.request,f.response);
        Object original=f.sessionValues.get(MealRecommendationsServlet.DRAFT);
        f.params.put("action","regenerate");f.servlet.doPost(f.request,f.response);
        assertEquals(403,f.status);assertSame(original,f.sessionValues.get(MealRecommendationsServlet.DRAFT));
        f.params.put("csrfToken",Csrf.token(f.request));f.servlet.doPost(f.request,f.response);
        assertNotSame(original,f.sessionValues.get(MealRecommendationsServlet.DRAFT));
        assertEquals(0,f.writes);assertEquals(2,f.generated);
        assertEquals("/nutrition/recommendations?message=regenerated",f.redirect);
    }
    @Test void legacyGetRedirectsAndManualStandardPostIgnoresClientServings() throws Exception {
        Fixture f=new Fixture();final BigDecimal[] captured={null};
        MealPlannerServlet old=new MealPlannerServlet(new MealPlannerService(){
            @Override public com.nutrifit.model.MealEntry addMeal(long user,long recipe,MealEntry.MealType type,BigDecimal amount){
                assertEquals(42,user);captured[0]=amount;return null;
            }
        });
        f.params.put("message","suggested");old.doGet(f.request,f.response);
        assertEquals("/nutrition/recommendations?message=suggested",f.redirect);
        f.params.put("action","addStandard");f.params.put("recipeId","7");f.params.put("mealType","LUNCH");f.params.put("servings","123.45");
        old.doPost(f.request,f.response);assertNull(captured[0]);assertEquals(403,f.status);
        f.params.put("csrfToken",Csrf.token(f.request));old.doPost(f.request,f.response);
        assertEquals(new BigDecimal("1.00"),captured[0]);assertEquals("/nutrition/recommendations?message=added",f.redirect);
    }
    @Test void missingTargetStillRendersJournalAndManualRecipeChoices() throws Exception {
        Fixture f=new Fixture();f.unavailable=true;f.servlet.doGet(f.request,f.response);
        assertNotNull(f.attributes.get("today"));assertNotNull(f.attributes.get("recipes"));
        assertNotNull(f.attributes.get("suggestionError"));assertEquals(0,f.writes);
    }
    private static class Fixture {
        final Map<String,Object> sessionValues=new HashMap<>(),attributes=new HashMap<>();
        final Map<String,String> params=new HashMap<>();
        int status=200,writes,generated;
        String redirect;long savedUser;boolean failSave, unavailable;
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
                    case "sendRedirect" -> {status=302;redirect=(String)a[0];yield null;}
                    case "setContentType" -> null;
                    case "getWriter" -> new PrintWriter(body);
                    default -> throw new AssertionError(m.getName());
                });
        final MealSuggestion suggestion=new MealSuggestion(42,LocalDate.now(),new BigDecimal("2400"),false,
                Arrays.stream(MealEntry.MealType.values()).map(t->new SuggestedMeal(t.ordinal()+1,"Recipe",t,
                        BigDecimal.ONE,new NutritionFacts(new BigDecimal("800"),BigDecimal.TEN,
                        BigDecimal.TEN,BigDecimal.TEN,BigDecimal.ONE))).toList());
        final MealRecommendationService recommendations=new MealRecommendationService(){
            @Override public MealSuggestion recommendDay(long user){
                generated++;
                if(unavailable) throw new RecommendationUnavailableException("Hãy hoàn tất mục tiêu trong hồ sơ.");
                return suggestion;
            }
            @Override public MealSuggestion recommendDay(long user,MealSuggestion previous,List<List<Long>> recent){
                generated++;
                return new MealSuggestion(user,LocalDate.now(),suggestion.targetKcal(),false,
                        suggestion.meals().stream().map(m -> new SuggestedMeal(m.recipeId()+10,m.name(),m.mealType(),
                                new BigDecimal("1.00"),m.nutrition())).toList());
            }
            @Override public MealSuggestion refresh(long user,MealSuggestion s,Map<MealEntry.MealType,BigDecimal> amounts){return s;}
        };
        final MealPlannerService planner=new MealPlannerService(){
            @Override public DaySummary getToday(long user){return new DaySummary(LocalDate.now(),null,List.of(),NutritionFacts.ZERO);}
            @Override public List<RecipeCandidate> listAvailableRecipes(){return List.of();}
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
