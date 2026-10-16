package com.nutrifit.util;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import java.util.OptionalLong;

/**
 * INTEGRATION POINT: change this to the session contract of the Auth owner.
 * Read only a server-generated session attribute; NEVER read userId from form/query.
 */
public final class CurrentUser {
    private CurrentUser() { }

    public static OptionalLong id(HttpServletRequest request) {
        HttpSession session = request.getSession(false);
        if (session == null) return OptionalLong.empty();
        Object value = session.getAttribute("userId");
        if (value == null) value = session.getAttribute("user_id");
        long id;
        try {
            if (value instanceof Number n) id = n.longValue();
            else if (value instanceof String s) id = Long.parseLong(s);
            else return OptionalLong.empty();
        } catch (NumberFormatException e) {
            return OptionalLong.empty();
        }
        return id > 0 ? OptionalLong.of(id) : OptionalLong.empty();
    }
}
