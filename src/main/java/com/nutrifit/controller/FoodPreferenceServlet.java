package com.nutrifit.controller;

import com.nutrifit.service.FoodPreferenceService;
import com.nutrifit.util.Csrf;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;

@WebServlet("/nutrition/preferences")
public class FoodPreferenceServlet extends NutritionServletSupport {
    private final FoodPreferenceService service = new FoodPreferenceService();

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        Long user = requireUser(req, resp);
        if (user == null) return;
        try {
            req.setAttribute("preferences", service.listSavedPreferences(user));
            req.setAttribute("foods", service.listAvailableFoods(user));
            req.setAttribute("csrf", Csrf.token(req));
            req.getRequestDispatcher("/WEB-INF/views/nutrition/food-preferences.jsp").forward(req, resp);
        } catch (Exception e) {
            fail(req, resp, e);
        }
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        req.setCharacterEncoding("UTF-8");
        Long user = requireUser(req, resp);
        if (user == null || !requireCsrf(req, resp)) return;
        try {
            String action = required(req.getParameter("action"));
            long foodId = parseId(req.getParameter("foodId"));
            if ("delete".equals(action)) {
                service.removePreference(user, foodId);
            } else if ("save".equals(action)) {
                service.setPreference(user, foodId,
                        parsePreferenceType(req.getParameter("type")));
            } else {
                throw new IllegalArgumentException("Unknown preference action");
            }
            resp.sendRedirect(req.getContextPath() + "/nutrition/preferences?message=saved");
        } catch (Exception e) {
            fail(req, resp, e);
        }
    }
}
