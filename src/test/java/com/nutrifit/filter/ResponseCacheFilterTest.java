package com.nutrifit.filter;
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import java.lang.reflect.Proxy;
import java.net.URI;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class ResponseCacheFilterTest {
 @Test void onlyExistingGetHeadAssetsCanBePubliclyCached()throws Exception {
  for(String path:List.of("/dashboard","/profile","/payment","/payment/ipn","/nutrition/recommendations","/login","/register","/assets/missing.css","/assets/../private.css","/assets/test.html"))assertEquals("no-store",header(path,"GET",false));
  assertEquals("no-store",header("/assets/main.css","POST",true));
  assertEquals("public, max-age=300, must-revalidate",header("/assets/main.css","GET",false));
  assertEquals("public, max-age=31536000, immutable",header("/assets/main.css","GET",true));
  assertEquals("public, max-age=31536000, immutable",header("/assets/main.css","HEAD",true));
 }
 static String header(String path,String method,boolean versioned)throws Exception {
  Map<String,String> headers=new HashMap<>();
  ServletContext ctx=(ServletContext)Proxy.newProxyInstance(ResponseCacheFilterTest.class.getClassLoader(),new Class<?>[]{ServletContext.class},(p,m,a)->switch(m.getName()){
   case "getAttribute"->"revision";case "getResource"->path.contains("missing")?null:URI.create("file:/public.css").toURL();default->null;
  });
  FilterConfig config=(FilterConfig)Proxy.newProxyInstance(ResponseCacheFilterTest.class.getClassLoader(),new Class<?>[]{FilterConfig.class},(p,m,a)->ctx);
  HttpServletRequest request=(HttpServletRequest)Proxy.newProxyInstance(ResponseCacheFilterTest.class.getClassLoader(),new Class<?>[]{HttpServletRequest.class},(p,m,a)->switch(m.getName()){
   case "getServletPath"->path;case "getMethod"->method;case "getParameter"->versioned?"revision":null;default->null;
  });
  HttpServletResponse response=(HttpServletResponse)Proxy.newProxyInstance(ResponseCacheFilterTest.class.getClassLoader(),new Class<?>[]{HttpServletResponse.class},(p,m,a)->{if(m.getName().equals("setHeader"))headers.put((String)a[0],(String)a[1]);return null;});
  ResponseCacheFilter filter=new ResponseCacheFilter();filter.init(config);filter.doFilter(request,response,(req,res)->{});return headers.get("Cache-Control");
 }
}
