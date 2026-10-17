package com.nutrifit.util;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import java.util.OptionalLong;

/**
 * Reads the Auth session contract, never form/query identity.
 * Checking attribute types is NOT session revocation validation: the integrated
 * AuthFilter must verify authVersion against Auth's authoritative state.
 */
public final class CurrentUser {
    private CurrentUser() { }

    public static OptionalLong id(HttpServletRequest request) {
        HttpSession session = request.getSession(false);
        if (session == null) return OptionalLong.empty();
        try {
            Object value = session.getAttribute("userId");
            if (!(value instanceof Long id) || id <= 0
                    || !(session.getAttribute("authVersion") instanceof Long)
                    || !(session.getAttribute("role") instanceof String)
                    || !(session.getAttribute("fullName") instanceof String)) {
                return OptionalLong.empty();
            }
            return OptionalLong.of(id);
        } catch (IllegalStateException e) {
            // The session may have been invalidated by a concurrent logout.
            return OptionalLong.empty();
        }
    }
}
