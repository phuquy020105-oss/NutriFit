package com.nutrifit.controller;

import com.nutrifit.service.MealPlannerService;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;

@WebServlet({"/nutrition/meal-planner", "/nutrition"})
public class MealPlannerServlet extends NutritionServletSupport {
    private final MealPlannerService service;
    public MealPlannerServlet() { this(new MealPlannerService()); }
    MealPlannerServlet(MealPlannerService service) { this.service = service; }

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        Long user = requireUser(req, resp);
        if (user == null) return;
        String message = req.getParameter("message");
        String suffix = java.util.Set.of("added","updated","deleted","saved","suggested").contains(
                message == null ? "" : message) ? "?message=" + message : "";
        resp.sendRedirect(req.getContextPath() + "/nutrition/recommendations" + suffix);
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        req.setCharacterEncoding("UTF-8");
        Long user = requireUser(req, resp);
        if (user == null || !requireCsrf(req, resp)) return;
        try {
            String action = required(req.getParameter("action"));
            if ("addStandard".equals(action)) {
                service.addMeal(user, parseId(req.getParameter("recipeId")),
                        parseMealType(req.getParameter("mealType")), new java.math.BigDecimal("1.00"));
            } else if ("changeRecipe".equals(action)) {
                service.changeRecipe(user, parseId(req.getParameter("entryId")),
                        parseId(req.getParameter("recipeId")), parseMealType(req.getParameter("mealType")));
            } else if ("add".equals(action)) {
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
                case "add", "addStandard" -> "added";
                case "update", "changeRecipe" -> "updated";
                case "delete" -> "deleted";
                default -> "saved";
            };
            resp.sendRedirect(req.getContextPath() + "/nutrition/recommendations?message=" + message);
        } catch (Exception e) {
            fail(req, resp, e);
        }
    }
}
