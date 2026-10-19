
package com.nutrifit.controller;

import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;

@WebServlet("/health")
public class HealthServlet extends HttpServlet {

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response
    ) throws IOException {

        response.setContentType("application/json;charset=UTF-8");

        response.setHeader("Cache-Control", "no-store");
        response.getWriter().write(healthJson(System.getenv("RENDER_GIT_COMMIT")));
    }
    // Expose only the documented, non-secret deployment SHA, never arbitrary environment content.
    static String healthJson(String revision) {
        String safe = revision != null && revision.matches("[0-9a-fA-F]{40}")
                ? revision.toLowerCase(java.util.Locale.ROOT) : "unknown";
        return "{\"status\":\"ok\",\"application\":\"NutriFit\",\"revision\":\"" + safe + "\"}";
    }
}
