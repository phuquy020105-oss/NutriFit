package com.nutrifit.controller;

import com.nutrifit.model.MealEntry;
import com.nutrifit.service.MealRecommendationService;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;

@WebServlet("/nutrition/recommendations")
public class MealRecommendationsServlet extends NutritionServletSupport {
    private final MealRecommendationService service = new MealRecommendationService();

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        Long user = requireUser(req, resp);
        if (user == null) return;
        try {
            MealEntry.MealType type = req.getParameter("mealType") == null
                    ? MealEntry.MealType.LUNCH : parseMealType(req.getParameter("mealType"));
            boolean premium = service.hasPremiumAccess(user);
            req.setAttribute("premium", premium);
            req.setAttribute("mealType", type);
            if (premium) req.setAttribute("recommendations", service.recommend(user, type, 15));
            req.getRequestDispatcher("/WEB-INF/views/nutrition/meal-recommendations.jsp")
                    .forward(req, resp);
        } catch (Exception e) {
            fail(resp, e);
        }
    }
}
