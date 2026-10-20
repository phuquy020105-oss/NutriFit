
package com.nutrifit.controller;

import com.nutrifit.dao.UserDAO;
import com.nutrifit.model.User;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

import java.io.IOException;
import java.sql.SQLException;

@WebServlet("/dashboard")
public class DashboardServlet extends HttpServlet {

    private final UserDAO userDAO = new UserDAO();

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response)
            throws ServletException, IOException {

        HttpSession session = request.getSession(false);

        if (session == null
                || !(session.getAttribute("userId") instanceof Long userId)) {

            response.sendRedirect(
                    request.getContextPath() + "/login");
            return;
        }

        try {
            User user = com.nutrifit.util.VerifiedRequestUser.find(request, userDAO)
                    .orElse(null);

            if (user == null) {
                session.invalidate();
                response.sendRedirect(
                        request.getContextPath() + "/login");
                return;
            }

            request.setAttribute("user", user);

            new com.nutrifit.dao.DashboardReadDAO().find(userId).forEach(request::setAttribute);

            request.getRequestDispatcher(
                    "/WEB-INF/views/dashboard/dashboard.jsp"
            ).forward(request, response);

        } catch (SQLException e) {
            log("Dashboard database error", e);

            response.sendError(
                    HttpServletResponse.SC_INTERNAL_SERVER_ERROR,
                    "Không thể tải Dashboard lúc này.");
        }
    }
}
