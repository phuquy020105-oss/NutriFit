package com.nutrifit.controller;

import com.nutrifit.dao.SubscriptionPlanDAO;
import com.nutrifit.dto.CheckoutDTO;
import com.nutrifit.service.PaymentService;
import com.nutrifit.service.VnpayService;
import com.nutrifit.util.SessionUser;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.sql.SQLException;

/** Only the payment presentation and setup-failure UX are changed. */
@WebServlet("/payment")
public final class PaymentServlet extends HttpServlet {
    private final PaymentService payments = new PaymentService();
    private final SubscriptionPlanDAO plans = new SubscriptionPlanDAO();

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse res)
            throws ServletException, IOException {
        try {
            SessionUser.requireId(req);
            res.setHeader("Cache-Control", "no-store");
            req.setAttribute("plans", plans.findAllActive());
            req.setAttribute("csrf", SessionUser.csrf(req.getSession()));
            req.setAttribute("vnpConfigured", VnpayService.isConfigured());
            req.getRequestDispatcher("/WEB-INF/views/payment/plans.jsp").forward(req, res);
        } catch (SecurityException e) {
            res.sendRedirect(req.getContextPath() + "/login");
        } catch (SQLException e) {
            throw new ServletException("Cannot load Premium plans", e);
        }
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse res)
            throws ServletException, IOException {
        try {
            SessionUser.requireId(req);
            req.setCharacterEncoding("UTF-8");
            if (!SessionUser.validCsrf(req)) {
                res.sendError(HttpServletResponse.SC_FORBIDDEN, "Invalid CSRF token");
                return;
            }
            if (!VnpayService.isConfigured()) {
                res.sendRedirect(req.getContextPath() + "/payment?notice=setup");
                return;
            }
            long planId = Long.parseLong(req.getParameter("planId"));
            CheckoutDTO checkout = payments.checkout(SessionUser.requireId(req), planId, req.getRemoteAddr());
            res.setStatus(HttpServletResponse.SC_SEE_OTHER);
            res.setHeader("Location", checkout.paymentUrl());
        } catch (SecurityException e) {
            res.sendRedirect(req.getContextPath() + "/login");
        } catch (IllegalArgumentException e) {
            res.sendRedirect(req.getContextPath() + "/payment?notice=invalid-plan");
        } catch (IllegalStateException e) {
            getServletContext().log("VNPay Sandbox configuration incomplete", e);
            res.sendRedirect(req.getContextPath() + "/payment?notice=setup");
        } catch (SQLException e) {
            throw new ServletException("Cannot initialize VNPay checkout", e);
        }
    }
}
