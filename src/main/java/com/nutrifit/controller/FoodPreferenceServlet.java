package com.nutrifit.controller;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.FoodCatalogDAO;
import com.nutrifit.model.FoodPreference;
import com.nutrifit.service.FoodPreferenceService;
import com.nutrifit.util.Csrf;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.sql.Connection;

@WebServlet("/nutrition/preferences")
public class FoodPreferenceServlet extends NutritionServletSupport {
    private final FoodPreferenceService service = new FoodPreferenceService();
    private final FoodCatalogDAO catalog = new FoodCatalogDAO();

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        Long user = requireUser(req, resp);
        if (user == null) return;
        try (Connection c = DatabaseConfig.getConnection()) {
            req.setAttribute("preferences", service.listPreferences(user));
            req.setAttribute("foods", catalog.listActive(c));
            req.setAttribute("csrf", Csrf.token(req));
            req.getRequestDispatcher("/WEB-INF/views/nutrition/food-preferences.jsp").forward(req, resp);
        } catch (Exception e) {
            fail(resp, e);
        }
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        Long user = requireUser(req, resp);
        if (user == null || !requireCsrf(req, resp)) return;
        try {
            long foodId = parseId(req.getParameter("foodId"));
            if ("delete".equals(req.getParameter("action"))) {
                service.removePreference(user, foodId);
            } else if ("save".equals(req.getParameter("action"))) {
                service.setPreference(user, foodId,
                        FoodPreference.PreferenceType.valueOf(req.getParameter("type")));
            } else {
                throw new IllegalArgumentException("Unknown preference action");
            }
            resp.sendRedirect(req.getContextPath() + "/nutrition/preferences?message=saved");
        } catch (Exception e) {
            fail(resp, e);
        }
    }
}
