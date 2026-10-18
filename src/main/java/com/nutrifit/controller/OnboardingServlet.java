package com.nutrifit.controller;

import com.nutrifit.service.OnboardingService;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
import java.io.IOException;
import java.sql.SQLException;

@WebServlet("/onboarding")
public class OnboardingServlet extends HttpServlet {
    private final OnboardingService service = new OnboardingService();
    private Long currentUser(HttpServletRequest request) {
        HttpSession s = request.getSession(false);
        return s != null && s.getAttribute("userId") instanceof Long id ? id : null;
    }
    @Override protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        Long id = currentUser(req);
        if (id == null) { resp.sendRedirect(req.getContextPath()+"/login"); return; }
        try {
            if (service.isComplete(id)) {
                resp.sendRedirect(req.getContextPath()+"/dashboard"); return;
            }
            req.getRequestDispatcher("/WEB-INF/views/profile/onboarding.jsp").forward(req,resp);
        } catch (SQLException ex) { throw new ServletException("Không thể kiểm tra hồ sơ",ex); }
    }
    @Override protected void doPost(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        req.setCharacterEncoding("UTF-8");
        Long id = currentUser(req);
        if (id == null) { resp.sendRedirect(req.getContextPath()+"/login"); return; }
        try {
            service.save(id,req.getParameter("gender"),req.getParameter("age"),
                req.getParameter("heightCm"),req.getParameter("weightKg"),
                req.getParameter("activityLevel"),req.getParameter("goal"));
            resp.sendRedirect(req.getContextPath()+"/dashboard");
        } catch (IllegalArgumentException ex) {
            req.setAttribute("error",ex.getMessage());
            req.getRequestDispatcher("/WEB-INF/views/profile/onboarding.jsp").forward(req,resp);
        } catch (SQLException ex) { throw new ServletException("Không thể lưu hồ sơ",ex); }
    }
}
