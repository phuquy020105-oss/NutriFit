package com.nutrifit.controller;

import com.nutrifit.util.JsonLite;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class HealthServletTest {
    @Test void reportsAnExactDeploymentRevisionWithoutChangingExistingHealthFields() {
        String sha="F04B2DAE07D764D8A50B7D855C3345B5E9FAE3C1";
        String json=HealthServlet.healthJson(sha);
        assertEquals("{\"status\":\"ok\",\"application\":\"NutriFit\",\"revision\":\""+sha.toLowerCase(java.util.Locale.ROOT)+"\"}",json);
        assertNotNull(JsonLite.parse(json));
    }
    @Test void missingOrMalformedEnvironmentValueNeverLeaksIntoResponse() {
        for (String raw : new String[]{null,"", "short", "password=do-not-echo", "\"}\nsecret"}) {
            String json=HealthServlet.healthJson(raw);
            assertTrue(json.contains("\"revision\":\"unknown\""));
            assertNotNull(JsonLite.parse(json));
            assertFalse(json.contains("secret"));
            assertFalse(json.contains("password"));
        }
    }
}
