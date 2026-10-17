package com.nutrifit.util;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import org.junit.jupiter.api.Test;
import java.lang.reflect.Proxy;
import java.util.HashMap;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

/** Isolated servlet API doubles only; no login endpoint or authenticated identity is created. */
class CsrfTest {
    @Test
    void rejectsMissingSessionAndDoesNotCreateOne() {
        HttpServletRequest request = request(null, null);
        assertFalse(Csrf.valid(request));
        assertThrows(IllegalStateException.class, () -> Csrf.token(request));
    }

    @Test
    void acceptsOnlyTheTokenOfTheSameSession() {
        HttpSession first = session();
        HttpServletRequest request = request(first, null);
        String token = Csrf.token(request);
        assertEquals(token, Csrf.token(request));
        assertEquals(43, token.length());
        assertFalse(Csrf.valid(request));
        assertFalse(Csrf.valid(request(first, "")));
        assertFalse(Csrf.valid(request(first, token + "wrong")));
        assertTrue(Csrf.valid(request(first, token)));
        HttpSession other = session();
        assertNotEquals(token, Csrf.token(request(other, null)));
        assertFalse(Csrf.valid(request(other, token)));
    }

    private HttpSession session() {
        Map<String, Object> attributes = new HashMap<>();
        return (HttpSession) Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class<?>[]{HttpSession.class}, (p, method, args) -> switch (method.getName()) {
                    case "getAttribute" -> attributes.get((String) args[0]);
                    case "setAttribute" -> { attributes.put((String) args[0], args[1]); yield null; }
                    default -> throw new AssertionError("Unexpected session access: " + method.getName());
                });
    }

    private HttpServletRequest request(HttpSession session, String token) {
        return (HttpServletRequest) Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class<?>[]{HttpServletRequest.class}, (p, method, args) -> {
                    if (method.getName().equals("getSession")) {
                        assertArrayEquals(new Object[]{false}, args);
                        return session;
                    }
                    if (method.getName().equals("getParameter")) {
                        assertEquals("csrfToken", args[0]);
                        return token;
                    }
                    throw new AssertionError("Unexpected request access: " + method.getName());
                });
    }
}
