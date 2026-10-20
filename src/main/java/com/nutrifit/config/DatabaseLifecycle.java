package com.nutrifit.config;
import jakarta.servlet.*;
import jakarta.servlet.annotation.WebListener;

@WebListener
public final class DatabaseLifecycle implements ServletContextListener {
    @Override public void contextInitialized(ServletContextEvent event) {
        String revision=System.getenv("RENDER_GIT_COMMIT");
        event.getServletContext().setAttribute("assetVersion",revision!=null&&revision.matches("[0-9a-fA-F]{40}")
                ?revision.toLowerCase(java.util.Locale.ROOT):java.util.UUID.randomUUID().toString());
    }
    @Override public void contextDestroyed(ServletContextEvent event) { DatabaseConfig.closePool(); }
}
