package com.nutrifit.filter;

import com.nutrifit.dao.UserDAO;
import com.nutrifit.model.User;
import com.nutrifit.model.UserRole;
import jakarta.servlet.*;
import jakarta.servlet.annotation.WebFilter;
import jakarta.servlet.http.*;
import java.io.IOException;
import java.sql.SQLException;

/** Supplies current, server-verified navigation permissions without changing authentication. */
@WebFilter(urlPatterns = {
        "/dashboard", "/dashboard/*", "/nutrition/*", "/profile", "/profile/*",
        "/workout", "/workout/*", "/chatbot", "/payment"
})
public class NavigationRoleFilter implements Filter {
    private final UserDAO users;

    public NavigationRoleFilter() { this(new UserDAO()); }
    NavigationRoleFilter(UserDAO users) { this.users = users; }

    @Override
    public void doFilter(ServletRequest rawRequest, ServletResponse rawResponse, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest request = (HttpServletRequest) rawRequest;
        HttpServletResponse response = (HttpServletResponse) rawResponse;
        request.setAttribute("navigationAdmin", false);
        response.setHeader("Cache-Control", "no-store");
        HttpSession session = request.getSession(false);
        if (session != null && session.getAttribute("userId") instanceof Long userId
                && session.getAttribute("authVersion") instanceof Long version) {
            try {
                User user = users.findById(userId).orElse(null);
                request.setAttribute("navigationAdmin", user != null
                        && userId.equals(user.getUserId()) && user.getAuthVersion() == version
                        && user.getRole() == UserRole.ADMIN);
            } catch (SQLException e) {
                throw new ServletException("Không thể xác minh quyền điều hướng.", e);
            }
        }
        chain.doFilter(request, response);
    }
}
