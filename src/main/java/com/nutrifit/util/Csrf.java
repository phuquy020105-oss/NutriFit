package com.nutrifit.util;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;

public final class Csrf {
    private static final SecureRandom RANDOM = new SecureRandom();
    private static final String ATTRIBUTE = "nutrifit.csrfToken";
    private Csrf() { }

    public static String token(HttpServletRequest request) {
        HttpSession session = request.getSession(false);
        if (session == null) throw new IllegalStateException("Login session required");
        synchronized (session) {
            Object value = session.getAttribute(ATTRIBUTE);
            String token = value instanceof String s && s.length() == 43 ? s : null;
            if (token == null) {
                byte[] bytes = new byte[32];
                RANDOM.nextBytes(bytes);
                token = Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
                session.setAttribute(ATTRIBUTE, token);
            }
            return token;
        }
    }

    public static boolean valid(HttpServletRequest request) {
        HttpSession session = request.getSession(false);
        if (session == null) return false;
        try {
            Object expected = session.getAttribute(ATTRIBUTE);
            String actual = request.getParameter("csrfToken");
            return expected instanceof String e && e.length() == 43
                    && actual != null && actual.length() == e.length()
                    && MessageDigest.isEqual(e.getBytes(StandardCharsets.UTF_8),
                            actual.getBytes(StandardCharsets.UTF_8));
        } catch (IllegalStateException e) {
            return false;
        }
    }
}
