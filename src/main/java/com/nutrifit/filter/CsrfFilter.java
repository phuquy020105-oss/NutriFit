
package com.nutrifit.filter;

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
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.Set;

@WebFilter("/*")
public class CsrfFilter implements Filter {

    private static final String TOKEN_KEY = "csrfToken";

    private static final Set<String> PROTECTED_PATHS =
            Set.of(
                    "/login",
                    "/logout",
                    "/register",
                    "/verify-otp",
                    "/forgot-password",
                    "/reset-password",
                    "/profile"
            );

    private final SecureRandom secureRandom =
            new SecureRandom();

    @Override
    public void doFilter(
            ServletRequest servletRequest,
            ServletResponse servletResponse,
            FilterChain chain)
            throws IOException, ServletException {

        if (!(servletRequest instanceof HttpServletRequest request)
                || !(servletResponse instanceof HttpServletResponse response)) {

            chain.doFilter(
                    servletRequest, servletResponse);
            return;
        }

        String path = request.getServletPath();
        String method = request.getMethod();

        if (!PROTECTED_PATHS.contains(path)) {
            chain.doFilter(request, response);
            return;
        }

        // Đặt UTF-8 trước khi đọc form parameters
        request.setCharacterEncoding("UTF-8");

        HttpSession session = request.getSession(false);

        // GET: tạo CSRF token cho form
        if ("GET".equalsIgnoreCase(method)) {

            if (session == null) {
                session = request.getSession(true);
            }

            getOrCreateToken(session);

            response.setHeader(
                    "Cache-Control", "no-store");

            chain.doFilter(request, response);
            return;
        }

        // POST: kiểm tra CSRF token
        if ("POST".equalsIgnoreCase(method)) {

            if (session == null) {
                reject(response);
                return;
            }

            String expectedToken =
                    (String) session.getAttribute(TOKEN_KEY);

            String submittedToken =
                    request.getParameter("_csrf");

            if (expectedToken == null
                    || submittedToken == null
                    || !constantTimeEquals(
                            expectedToken, submittedToken)) {

                reject(response);
                return;
            }

            response.setHeader(
                    "Cache-Control", "no-store");

            chain.doFilter(request, response);
            return;
        }

        response.sendError(
                HttpServletResponse.SC_METHOD_NOT_ALLOWED);
    }

    private String getOrCreateToken(
            HttpSession session) {

        synchronized (session) {

            String existing =
                    (String) session.getAttribute(TOKEN_KEY);

            if (existing != null) {
                return existing;
            }

            byte[] randomBytes = new byte[32];

            secureRandom.nextBytes(randomBytes);

            String token = Base64.getUrlEncoder()
                    .withoutPadding()
                    .encodeToString(randomBytes);

            session.setAttribute(TOKEN_KEY, token);

            return token;
        }
    }

    private boolean constantTimeEquals(
            String expected, String actual) {

        return MessageDigest.isEqual(
                expected.getBytes(StandardCharsets.UTF_8),
                actual.getBytes(StandardCharsets.UTF_8)
        );
    }

    private void reject(
            HttpServletResponse response)
            throws IOException {

        response.sendError(
                HttpServletResponse.SC_FORBIDDEN,
                "CSRF token không hợp lệ. "
                + "Vui lòng tải lại trang và thử lại."
        );
    }
}
