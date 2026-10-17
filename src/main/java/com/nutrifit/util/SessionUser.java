package com.nutrifit.util;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.nio.charset.StandardCharsets;
import java.util.HexFormat;

/** The Auth module must store a server-validated userId in the session. */
public final class SessionUser {
    private static final SecureRandom RANDOM = new SecureRandom();
    private SessionUser() {}
    public static long requireId(HttpServletRequest request) {
        HttpSession session = request.getSession(false);
        Object id = session == null ? null : session.getAttribute("userId");
        if (id instanceof Number n && n.longValue() > 0) return n.longValue();
        throw new SecurityException("Please log in");
    }
    public static String csrf(HttpSession session) {
        synchronized (session) {
            String t = (String) session.getAttribute("nutrifitCsrf");
            if (t == null) {
                byte[] random = new byte[32]; RANDOM.nextBytes(random);
                t = HexFormat.of().formatHex(random);
                session.setAttribute("nutrifitCsrf", t);
            }
            return t;
        }
    }
    public static boolean validCsrf(HttpServletRequest req) {
        HttpSession s = req.getSession(false);
        if (s == null) return false;
        String expected = (String)s.getAttribute("nutrifitCsrf");
        String got = req.getParameter("csrf");
        return expected != null && got != null && MessageDigest.isEqual(
            expected.getBytes(StandardCharsets.UTF_8), got.getBytes(StandardCharsets.UTF_8));
    }
}
