package com.nutrifit.controller;

import com.nutrifit.dto.*;
import com.nutrifit.model.*;
import jakarta.servlet.Servlet;
import jakarta.servlet.ServletContainerInitializer;
import jakarta.servlet.http.*;
import java.io.IOException;
import java.math.BigDecimal;
import java.net.*;
import java.net.http.*;
import java.nio.file.*;
import java.time.*;
import java.util.*;
import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

/** Real JSP rendering in an isolated loopback Tomcat context, without app filters, users or DB access.
 * TOMCAT_HOME supplies the installed server jars; no new Maven dependency or production test route.
 */
class NutritionViewsTest {
    static URLClassLoader loader;
    static Object tomcat;
    static String base;
    static final LocalDate DAY=LocalDate.of(2026,10,19);
    static Object call(Object object,String name,Class<?>[] types,Object... args)throws Exception{
        return object.getClass().getMethod(name,types).invoke(object,args);
    }
    @BeforeAll static void start()throws Exception{
        String home=System.getenv("TOMCAT_HOME");
        Assumptions.assumeTrue(home!=null&&Files.isDirectory(Path.of(home,"lib")),"Set TOMCAT_HOME for real JSP rendering tests");
        List<URL> urls=new ArrayList<>();
        try(var jars=Files.list(Path.of(home,"lib"))){for(Path jar:jars.filter(p->p.toString().endsWith(".jar")).toList())urls.add(jar.toUri().toURL());}
        urls.add(Path.of(home,"bin/tomcat-juli.jar").toUri().toURL());
        loader=new URLClassLoader(urls.toArray(URL[]::new),NutritionViewsTest.class.getClassLoader());
        Path work=Files.createTempDirectory(Path.of("target"),"nutrition-views-");Path web=work.resolve("web");
        for(String path:List.of("WEB-INF/views/nutrition/meal-history.jsp","WEB-INF/views/nutrition/meal-recommendations.jsp","WEB-INF/views/shared/admin-navigation.jspf")){
            Path copy=web.resolve(path);Files.createDirectories(copy.getParent());Files.copy(Path.of("src/main/webapp").resolve(path),copy);
        }
        ClassLoader prior=Thread.currentThread().getContextClassLoader();
        try{
            Thread.currentThread().setContextClassLoader(loader);
            Class<?> type=loader.loadClass("org.apache.catalina.startup.Tomcat"),contextType=loader.loadClass("org.apache.catalina.Context");
            tomcat=type.getConstructor().newInstance();call(tomcat,"setBaseDir",new Class<?>[]{String.class},work.resolve("server").toAbsolutePath().toString());
            call(tomcat,"setPort",new Class<?>[]{int.class},0);
            Object connector=call(tomcat,"getConnector",new Class<?>[]{});call(connector,"setProperty",new Class<?>[]{String.class,String.class},"address","127.0.0.1");
            Object context=call(tomcat,"addContext",new Class<?>[]{String.class,String.class},"/views",web.toAbsolutePath().toString());
            call(context,"setParentClassLoader",new Class<?>[]{ClassLoader.class},loader);
            Object scanner=call(context,"getJarScanner",new Class<?>[]{});call(scanner,"setScanClassPath",new Class<?>[]{boolean.class},false);
            Object jasper=loader.loadClass("org.apache.jasper.servlet.JasperInitializer").getConstructor().newInstance();
            call(context,"addServletContainerInitializer",new Class<?>[]{ServletContainerInitializer.class,Set.class},jasper,null);
            Object jsp=loader.loadClass("org.apache.jasper.servlet.JspServlet").getConstructor().newInstance();
            type.getMethod("addServlet",contextType,String.class,Servlet.class).invoke(null,context,"jsp",jsp);
            call(context,"addServletMappingDecoded",new Class<?>[]{String.class,String.class},"*.jsp","jsp");
            type.getMethod("addServlet",contextType,String.class,Servlet.class).invoke(null,context,"fixture",new FixtureServlet());
            call(context,"addServletMappingDecoded",new Class<?>[]{String.class,String.class},"/render","fixture");
            call(tomcat,"start",new Class<?>[]{});
            int port=(Integer)call(connector,"getLocalPort",new Class<?>[]{});assertTrue(port>0);base="http://127.0.0.1:"+port+"/views/render?state=";
        }finally{Thread.currentThread().setContextClassLoader(prior);}
    }
    @AfterAll static void stop()throws Exception{
        try{if(tomcat!=null){call(tomcat,"stop",new Class<?>[]{});call(tomcat,"destroy",new Class<?>[]{});}}
        finally{if(loader!=null)loader.close();}
    }
    static String render(String state)throws Exception{
        var response=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build().send(
                HttpRequest.newBuilder(URI.create(base+state)).timeout(Duration.ofSeconds(20)).GET().build(),HttpResponse.BodyHandlers.ofString());
        assertEquals(200,response.statusCode(),response.body());return response.body();
    }
    @Test void noHistoryKeepsDatePickerAndShowsConciseEmptyMessage()throws Exception{
        String html=render("history-none");assertTrue(html.contains("Bạn chưa có lịch sử ăn uống."));
        assertTrue(html.contains("type=\"date\""));assertTrue(html.contains("max=\"2026-10-19\""));
        assertFalse(html.contains("nf-stats"));assertFalse(html.contains("<table>"));
    }
    @Test void selectingEmptyDayHidesAllZeroCardsAndEmptyTable()throws Exception{
        for(String state:List.of("history-empty","history-no-plan")){
            String html=render(state);assertTrue(html.contains("Bạn chưa ghi nhận món ăn nào trong ngày này."));
            assertTrue(html.contains("value=\"2026-10-19\""));assertFalse(html.contains("nf-stats"));assertFalse(html.contains("<table>"));
            assertFalse(html.contains("Không có món ăn."));assertFalse(html.contains("tổng bằng 0"));
        }
    }
    @Test void storedEntriesAndFiveTotalsRenderAsHalfUpIntegersWithoutEditing()throws Exception{
        String html=render("history-data");assertTrue(html.contains("nf-stats"));assertTrue(html.contains("<table>"));
        String totals=html.substring(html.indexOf("<div class=\"nf-stats\">"),html.indexOf("<div class=\"nf-table-scroll\">"));
        for(String value:List.of("301","31","51","6","4"))assertTrue(totals.contains("<strong>"+value+"</strong>"),value);
        assertTrue(html.contains("Bánh mì &lt;trứng&gt;"));assertTrue(html.contains("Cơm gà cũ"));
        assertTrue(html.contains("<td>Sáng</td>"));assertTrue(html.contains("<td>Trưa</td>"));
        assertFalse(html.contains("Bạn chưa ghi nhận món ăn nào trong ngày này."));
        assertFalse(html.contains("name=\"entryId\""));assertFalse(html.contains("name=\"servings\""));
        assertTrue(html.contains("/nutrition/history?date=2026-10-19"));
    }
    @Test void aRealZeroValuedEntryIsNotMistakenForAnEmptyDay()throws Exception{
        String html=render("history-zero-entry");assertTrue(html.contains("<table>"));assertTrue(html.contains("Món có snapshot bằng 0"));
        assertFalse(html.contains("Bạn chưa ghi nhận món ăn nào trong ngày này."));
    }
    @Test void menuLabelsSeparateOneSlotRegenerationAndSaveWithoutChangingActions()throws Exception{
        String html=render("recommendations");
        assertEquals(3,html.split("data-swap-form",-1).length-1);assertEquals(3,html.split(">Đổi món</button>",-1).length-1);
        assertEquals(1,html.split(">Đổi thực đơn</button>",-1).length-1);assertTrue(html.contains("name=\"action\" value=\"regenerate\""));
        assertTrue(html.contains("Lưu thực đơn vào nhật ký"));assertFalse(html.contains("Gợi ý lại"));
        assertEquals(1,render("recommendations-unavailable").split(">Đổi thực đơn</button>",-1).length-1);
    }
    static NutritionFacts facts(String k,String p,String c,String f,String fiber){return new NutritionFacts(new BigDecimal(k),new BigDecimal(p),new BigDecimal(c),new BigDecimal(f),new BigDecimal(fiber));}
    static final class FixtureServlet extends HttpServlet {
        @Override protected void doGet(HttpServletRequest req,HttpServletResponse resp)throws IOException,jakarta.servlet.ServletException{
            String state=req.getParameter("state");req.setAttribute("latestDate",DAY);
            var plan=new MealPlan(10L,42L,DAY,DAY.atStartOfDay());List<MealEntry> entries=List.of();NutritionFacts total=NutritionFacts.ZERO;
            if("history-data".equals(state)){
                var a=facts("100.500","10.500","20.400","2.500","1.500");var b=facts("200.000","20.000","30.200","3.000","2.000");
                entries=List.of(entry(5,"Bánh mì <trứng>",MealEntry.MealType.BREAKFAST,a),entry(6,"Cơm gà cũ",MealEntry.MealType.LUNCH,b));total=a.add(b);
            }else if("history-zero-entry".equals(state))entries=List.of(entry(5,"Món có snapshot bằng 0",MealEntry.MealType.DINNER,NutritionFacts.ZERO));
            req.setAttribute("history",entries.isEmpty()?List.of():List.of(plan));
            if(!"history-none".equals(state))req.setAttribute("selected",new DaySummary(DAY,"history-no-plan".equals(state)?null:plan,entries,total));
            if(state.startsWith("recommendations")){
                req.setAttribute("today",new DaySummary(DAY,null,List.of(),NutritionFacts.ZERO));req.setAttribute("recipes",List.of());
                req.setAttribute("csrf","fixture-only");req.setAttribute("suggestionToken","fixture-only");
                if(!state.endsWith("unavailable"))req.setAttribute("suggestion",new MealSuggestion(42,DAY,new BigDecimal("1800"),false,
                    Arrays.stream(MealEntry.MealType.values()).map(t->new SuggestedMeal(t.ordinal()+1,"Món thử "+t,t,new BigDecimal("1.00"),facts("600","30","75","20","8"))).toList()));
                req.getRequestDispatcher("/WEB-INF/views/nutrition/meal-recommendations.jsp").forward(req,resp);
            }else req.getRequestDispatcher("/WEB-INF/views/nutrition/meal-history.jsp").forward(req,resp);
        }
        static MealEntry entry(long recipe,String name,MealEntry.MealType type,NutritionFacts n){return new MealEntry(10L,recipe,name,type,new BigDecimal("1.32"),n.caloriesKcal(),n.proteinG(),n.carbsG(),n.fatG(),n.fiberG());}
    }
}
