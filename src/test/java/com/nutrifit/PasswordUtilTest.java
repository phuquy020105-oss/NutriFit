
package com.nutrifit;

import com.nutrifit.util.PasswordUtil;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class PasswordUtilTest {

    @Test
    void shouldHashAndVerifyPassword() {
        String password = "TestPassword123!";
        String hash = PasswordUtil.hash(password);

        assertNotEquals(password, hash);
        assertTrue(PasswordUtil.verify(password, hash));
        assertFalse(PasswordUtil.verify("WrongPassword", hash));
    }

    @Test
    void shouldRejectEmptyPassword() {
        assertThrows(IllegalArgumentException.class,
                () -> PasswordUtil.hash(""));
    }

    @Test
    void shouldRejectInvalidHash() {
        assertFalse(PasswordUtil.verify("password", "invalid"));
    }
}
