package com.nutrifit.controller;

import com.nutrifit.service.MealPlannerService;
import com.nutrifit.util.Csrf;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;

@WebServlet("/nutrition/meal-planner")
public class MealPlannerServlet extends NutritionServletSupport {
    private final MealPlannerService service = new MealPlannerService();

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        Long user = requireUser(req, resp);
        if (user == null) return;
        try {
            req.setAttribute("today", service.getToday(user));
            req.setAttribute("targetKcal", service.getTargetKcal(user).orElse(null));
            req.setAttribute("recipes", service.listAvailableRecipes());
            req.setAttribute("csrf", Csrf.token(req));
            req.getRequestDispatcher("/WEB-INF/views/nutrition/meal-planner.jsp").forward(req, resp);
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
            if ("add".equals(action)) {
                service.addMeal(user, parseId(req.getParameter("recipeId")),
                        parseMealType(req.getParameter("mealType")),
                        parseServings(req.getParameter("servings")));
            } else if ("update".equals(action)) {
                service.updateMeal(user, parseId(req.getParameter("entryId")),
                        parseId(req.getParameter("recipeId")),
                        parseMealType(req.getParameter("mealType")),
                        parseServings(req.getParameter("servings")));
            } else if ("delete".equals(action)) {
                service.removeMeal(user, parseId(req.getParameter("entryId")));
            } else {
                throw new IllegalArgumentException("Unknown action");
            }
            String message = switch (action) {
                case "add" -> "added";
                case "update" -> "updated";
                case "delete" -> "deleted";
                default -> "saved";
            };
            resp.sendRedirect(req.getContextPath() + "/nutrition/meal-planner?message=" + message);
        } catch (Exception e) {
            fail(req, resp, e);
        }
    }
}
