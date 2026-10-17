
package com.nutrifit.filter;

import com.nutrifit.dao.UserDAO;
import com.nutrifit.model.User;
import com.nutrifit.model.UserRole;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.annotation.WebFilter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

import java.io.IOException;
import java.sql.SQLException;
import java.util.Optional;

@WebFilter(urlPatterns = {"/admin", "/admin/*"})
public class AdminFilter implements Filter {

    private final UserDAO userDAO = new UserDAO();

    @Override
    public void doFilter(
            ServletRequest servletRequest,
            ServletResponse servletResponse,
            FilterChain chain)
            throws IOException, ServletException {

        HttpServletRequest request =
                (HttpServletRequest) servletRequest;

        HttpServletResponse response =
                (HttpServletResponse) servletResponse;

        HttpSession session = request.getSession(false);

        // 1. Chưa đăng nhập
        if (session == null) {
            redirectToLogin(request, response);
            return;
        }

        Object userIdObject = session.getAttribute("userId");
        Object versionObject = session.getAttribute("authVersion");

        if (!(userIdObject instanceof Long userId)
                || !(versionObject instanceof Long sessionVersion)) {

            session.invalidate();
            redirectToLogin(request, response);
            return;
        }

        try {
            // 2. Lấy tài khoản hiện tại từ MySQL
            Optional<User> optionalUser = userDAO.findById(userId);

            if (optionalUser.isEmpty()) {
                session.invalidate();
                redirectToLogin(request, response);
                return;
            }

            User user = optionalUser.get();

            // 3. Kiểm tra session có còn hợp lệ không
            if (user.getAuthVersion() != sessionVersion.longValue()) {
                session.invalidate();
                redirectToLogin(request, response);
                return;
            }

            // 4. Kiểm tra quyền ADMIN từ database
            if (user.getRole() != UserRole.ADMIN) {
                response.sendError(
                        HttpServletResponse.SC_FORBIDDEN,
                        "Bạn không có quyền truy cập trang Admin.");
                return;
            }

            // 5. Được phép truy cập
            chain.doFilter(request, response);

        } catch (SQLException e) {
            throw new ServletException(
                    "Không thể xác minh quyền quản trị.", e);
        }
    }

    private void redirectToLogin(
            HttpServletRequest request,
            HttpServletResponse response) throws IOException {

        response.sendRedirect(
                request.getContextPath() + "/login");
    }
}
