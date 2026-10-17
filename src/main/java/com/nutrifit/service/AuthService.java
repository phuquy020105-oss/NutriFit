
package com.nutrifit.service;

import com.nutrifit.dao.UserDAO;
import com.nutrifit.model.User;
import com.nutrifit.util.PasswordUtil;

import java.sql.SQLException;
import java.util.Locale;
import java.util.Optional;

public class AuthService {

    private final UserDAO userDAO;

    public AuthService() {
        this.userDAO = new UserDAO();
    }

    public AuthService(UserDAO userDAO) {
        this.userDAO = userDAO;
    }

    public Optional<User> login(String email, String password)
            throws SQLException {

        if (email == null || password == null) {
            return Optional.empty();
        }

        String normalizedEmail =
                email.trim().toLowerCase(Locale.ROOT);

        if (normalizedEmail.isEmpty() || password.isEmpty()) {
            return Optional.empty();
        }

        Optional<User> foundUser =
                userDAO.findByEmail(normalizedEmail);

        if (foundUser.isEmpty()) {
            return Optional.empty();
        }

        User user = foundUser.get();

        if (!PasswordUtil.verify(
                password, user.getPasswordHash())) {
            return Optional.empty();
        }

        return Optional.of(user);
    }
}
