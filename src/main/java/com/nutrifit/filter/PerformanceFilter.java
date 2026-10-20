package com.nutrifit.filter;

import com.nutrifit.observability.Performance;
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import java.io.IOException;
import java.util.logging.Logger;

/** Mapped first by web.xml. Disabled unless NUTRIFIT_PERF_ENABLED=true. */
public final class PerformanceFilter implements Filter {
    private static final Logger LOG=Logger.getLogger(PerformanceFilter.class.getName());
    private boolean enabled;
    @Override public void init(FilterConfig config) {
        enabled="true".equalsIgnoreCase(System.getenv("NUTRIFIT_PERF_ENABLED"));
    }
    @Override public void doFilter(ServletRequest raw,ServletResponse result,FilterChain chain)
            throws IOException,ServletException {
        if(!enabled || !(raw instanceof HttpServletRequest request)
                || !(result instanceof HttpServletResponse response)){chain.doFilter(raw,result);return;}
        Performance.Sample sample=Performance.begin();
        boolean failed=true;
        try {
            chain.doFilter(new HttpServletRequestWrapper(request){
                @Override public RequestDispatcher getRequestDispatcher(String path) {
                    RequestDispatcher delegate=super.getRequestDispatcher(path);
                    if(delegate==null)return null;
                    return new RequestDispatcher(){
                        @Override public void forward(ServletRequest req,ServletResponse res)throws ServletException,IOException {
                            try(var ignored=Performance.scope("view")){delegate.forward(req,res);}
                        }
                        @Override public void include(ServletRequest req,ServletResponse res)throws ServletException,IOException {
                            delegate.include(req,res);
                        }
                    };
                }
            },response);
            failed=false;
        } finally {
            try{LOG.info(sample.summary(request.getServletPath(),failed?500:response.getStatus()));}
            finally{Performance.end();}
        }
    }
}
