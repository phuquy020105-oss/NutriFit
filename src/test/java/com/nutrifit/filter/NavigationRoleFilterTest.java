package com.nutrifit.filter;

import com.nutrifit.dao.UserDAO;
import com.nutrifit.model.*;
import jakarta.servlet.*;
import jakarta.servlet.annotation.WebFilter;
import jakarta.servlet.http.*;
import java.lang.reflect.*;
import java.sql.SQLException;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class NavigationRoleFilterTest {
    @Test void onlyCurrentAdminSeesManagementRegardlessOfSubscription() throws Exception {
        for (UserRole role : UserRole.values()) {
            for (SubscriptionStatus subscription : SubscriptionStatus.values()) {
                Fixture f = new Fixture();
                f.user.setRole(role);
                f.user.setSubscriptionStatus(subscription);
                new NavigationRoleFilter(f.users).doFilter(f.request, f.response, f.chain);
                assertEquals(role == UserRole.ADMIN, f.attributes.get("navigationAdmin"));
                assertEquals("no-store", f.headers.get("Cache-Control"));
                assertEquals(1, f.reads);
                assertEquals(1, f.forwarded);
            }
        }
    }

    @Test void roleChangesAreReflectedOnNextRequestWithoutTrustingSessionRole() throws Exception {
        Fixture f = new Fixture();
        NavigationRoleFilter filter = new NavigationRoleFilter(f.users);
        f.sessionValues.put("role", "ADMIN");
        f.user.setRole(UserRole.USER);
        filter.doFilter(f.request, f.response, f.chain);
        assertEquals(false, f.attributes.get("navigationAdmin"));
        f.sessionValues.put("role", "USER");
        f.user.setRole(UserRole.ADMIN);
        filter.doFilter(f.request, f.response, f.chain);
        assertEquals(true, f.attributes.get("navigationAdmin"));
        f.user.setRole(UserRole.USER);
        filter.doFilter(f.request, f.response, f.chain);
        assertEquals(false, f.attributes.get("navigationAdmin"));
        assertEquals(3, f.reads);
    }

    @Test void staleVersionDeletedAccountOrMismatchedIdentityNeverGrantsMenu() throws Exception {
        for (int scenario = 0; scenario < 3; scenario++) {
            Fixture f = new Fixture();
            if (scenario == 0) f.user.setAuthVersion(8L);
            if (scenario == 1) f.user = null;
            if (scenario == 2) f.user.setUserId(99L);
            f.attributes.put("navigationAdmin", true);
            new NavigationRoleFilter(f.users).doFilter(f.request, f.response, f.chain);
            assertEquals(false, f.attributes.get("navigationAdmin"));
        }
    }

    @Test void missingOrMalformedSessionCannotGrantMenuOrOpenDatabase() throws Exception {
        for (int scenario = 0; scenario < 4; scenario++) {
            Fixture f = new Fixture();
            if (scenario == 0) f.hasSession = false;
            if (scenario == 1) f.sessionValues.remove("authVersion");
            if (scenario == 2) f.sessionValues.put("userId", "42");
            if (scenario == 3) f.sessionValues.put("authVersion", "7");
            f.sessionValues.put("role", "ADMIN");
            new NavigationRoleFilter(f.users).doFilter(f.request, f.response, f.chain);
            assertEquals(false, f.attributes.get("navigationAdmin"));
            assertEquals(0, f.reads);
        }
    }

    @Test void databaseFailureCannotRenderAnAdminMenu() {
        Fixture f = new Fixture();
        f.failRead = true;
        assertThrows(ServletException.class,
                () -> new NavigationRoleFilter(f.users).doFilter(f.request, f.response, f.chain));
        assertEquals(false, f.attributes.get("navigationAdmin"));
        assertEquals(0, f.forwarded);
    }

    @Test void filterCoversAllWorkspaceSidebarRoutes() {
        Set<String> paths = Set.of(NavigationRoleFilter.class.getAnnotation(WebFilter.class).urlPatterns());
        assertTrue(paths.containsAll(Set.of("/dashboard", "/nutrition/*", "/profile",
                "/workout", "/workout/*", "/chatbot", "/payment")));
        assertFalse(paths.contains("/payment/ipn"));
    }

    @Test void unchangedAdminFilterDeniesDirectUserAccessAndAllowsFreeAdmin() throws Exception {
        for (UserRole role : UserRole.values()) {
            Fixture f = new Fixture();
            f.user.setRole(role);
            f.user.setSubscriptionStatus(SubscriptionStatus.FREE);
            f.sessionValues.put("role", "ADMIN");
            AdminFilter filter = adminFilter(f.users);
            filter.doFilter(f.request, f.response, f.chain);
            assertEquals(role == UserRole.ADMIN ? 1 : 0, f.forwarded);
            assertEquals(role == UserRole.ADMIN ? 200 : 403, f.status);
        }
    }

    @Test void unchangedAdminFilterRejectsStaleSessionEvenWithAdminRole() throws Exception {
        Fixture f = new Fixture();
        f.user.setAuthVersion(8L);
        adminFilter(f.users).doFilter(f.request, f.response, f.chain);
        assertEquals(0, f.forwarded);
        assertTrue(f.invalidated);
        assertEquals("/nutrifit/login", f.redirect);
    }

    private static AdminFilter adminFilter(UserDAO users) throws Exception {
        // Inject a read-only DAO stub into the existing filter without changing its production code.
        AdminFilter filter = new AdminFilter();
        Field field = AdminFilter.class.getDeclaredField("userDAO");
        field.setAccessible(true);
        field.set(filter, users);
        return filter;
    }

    private static class Fixture {
        User user = new User();
        boolean hasSession = true, failRead, invalidated;
        int reads, forwarded, status = 200;
        String redirect;
        final Map<String,Object> sessionValues = new HashMap<>(), attributes = new HashMap<>();
        final Map<String,String> headers = new HashMap<>();
        final UserDAO users = new UserDAO() {
            @Override public Optional<User> findById(Long id) throws SQLException {
                assertEquals(42L, id);
                reads++;
                if (failRead) throw new SQLException("Fixture database unavailable");
                return Optional.ofNullable(user);
            }
        };
        final HttpSession session = (HttpSession) Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class<?>[]{HttpSession.class}, (p,m,a) -> switch(m.getName()) {
                    case "getAttribute" -> sessionValues.get(a[0]);
                    case "invalidate" -> { invalidated = true; yield null; }
                    default -> throw new AssertionError(m.getName());
                });
        final HttpServletRequest request = (HttpServletRequest) Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class<?>[]{HttpServletRequest.class}, (p,m,a) -> switch(m.getName()) {
                    case "getSession" -> { assertArrayEquals(new Object[]{false}, a); yield hasSession ? session : null; }
                    case "setAttribute" -> { attributes.put((String)a[0], a[1]); yield null; }
                    case "getContextPath" -> "/nutrifit";
                    default -> throw new AssertionError(m.getName());
                });
        final HttpServletResponse response = (HttpServletResponse) Proxy.newProxyInstance(getClass().getClassLoader(),
                new Class<?>[]{HttpServletResponse.class}, (p,m,a) -> switch(m.getName()) {
                    case "setHeader" -> { headers.put((String)a[0], (String)a[1]); yield null; }
                    case "sendError" -> { status = (int)a[0]; yield null; }
                    case "sendRedirect" -> { redirect = (String)a[0]; yield null; }
                    default -> throw new AssertionError(m.getName());
                });
        final FilterChain chain = (req,resp) -> forwarded++;
        Fixture() {
            user.setUserId(42L);
            user.setRole(UserRole.ADMIN);
            user.setAuthVersion(7L);
            user.setSubscriptionStatus(SubscriptionStatus.FREE);
            sessionValues.put("userId", 42L);
            sessionValues.put("authVersion", 7L);
        }
    }
}
