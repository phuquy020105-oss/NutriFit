package com.nutrifit.controller;

import com.nutrifit.service.MealHistoryService;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.time.LocalDate;

@WebServlet("/nutrition/history")
public class MealHistoryServlet extends NutritionServletSupport {
    private final MealHistoryService service = new MealHistoryService();

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        Long user = requireUser(req, resp);
        if (user == null) return;
        try {
            req.setAttribute("history", service.listHistory(user, 30));
            String dateParam = req.getParameter("date");
            if (dateParam != null && !dateParam.isBlank()) {
                req.setAttribute("selected", service.getPastDay(user, LocalDate.parse(dateParam)));
            }
            req.getRequestDispatcher("/WEB-INF/views/nutrition/meal-history.jsp").forward(req, resp);
        } catch (Exception e) {
            fail(resp, e);
        }
    }
}
