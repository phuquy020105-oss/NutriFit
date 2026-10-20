package com.nutrifit.filter;
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import java.io.IOException;

/** Cache only existing public static files. HTML/API/security/payment responses stay no-store. */
public final class ResponseCacheFilter implements Filter {
    private ServletContext context;
    @Override public void init(FilterConfig config) { context=config.getServletContext(); }
    @Override public void doFilter(ServletRequest raw,ServletResponse result,FilterChain chain)throws IOException,ServletException {
        HttpServletRequest request=(HttpServletRequest)raw;HttpServletResponse response=(HttpServletResponse)result;
        response.setHeader("Cache-Control","no-store");
        String path=request.getServletPath();
        if (("GET".equals(request.getMethod())||"HEAD".equals(request.getMethod()))
                && path!=null && path.matches("/assets/[A-Za-z0-9_./-]+\\.(css|js|webp|svg|png|jpg|ico)")
                && !path.contains("..") && context.getResource(path)!=null) {
            Object version=context.getAttribute("assetVersion");
            boolean versioned=version instanceof String && version.equals(request.getParameter("v"));
            response.setHeader("Cache-Control",versioned?"public, max-age=31536000, immutable":"public, max-age=300, must-revalidate");
        }
        try { chain.doFilter(raw,result); }
        catch(IOException|ServletException|RuntimeException e){if(!response.isCommitted())response.setHeader("Cache-Control","no-store");throw e;}
    }
}
