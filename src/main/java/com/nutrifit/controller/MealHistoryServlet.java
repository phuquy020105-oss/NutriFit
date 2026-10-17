package com.nutrifit.controller;

import com.nutrifit.service.MealHistoryService;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;

@WebServlet("/nutrition/history")
public class MealHistoryServlet extends NutritionServletSupport {
    private final MealHistoryService service = new MealHistoryService();

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        Long user = requireUser(req, resp);
        if (user == null) return;
        try {
            String dateParam = req.getParameter("date");
            if (dateParam != null) {
                req.setAttribute("selected", service.getPastDay(user, parseDate(dateParam)));
            }
            req.setAttribute("history", service.listHistory(user, 30));
            req.setAttribute("latestDate", service.today().minusDays(1));
            req.getRequestDispatcher("/WEB-INF/views/nutrition/meal-history.jsp").forward(req, resp);
        } catch (Exception e) {
            fail(req, resp, e);
        }
    }
}
