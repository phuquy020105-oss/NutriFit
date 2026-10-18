
package com.nutrifit.config;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public final class DatabaseConfig {

    private static final String URL =
        "jdbc:mysql://127.0.0.1:3306/nutrifitdb_java"
        + "?useUnicode=true&characterEncoding=UTF-8";

    private DatabaseConfig() {
    }

    public static Connection getConnection()
            throws SQLException {

        String username = System.getenv("NUTRIFIT_DB_USER");
        String password = System.getenv("NUTRIFIT_DB_PASSWORD");

        if (username == null || username.isBlank()
                || password == null || password.isBlank()) {
            throw new SQLException(
                "Missing database environment variables"
            );
        }

        try {
            Class.forName("com.mysql.cj.jdbc.Driver");
        } catch (ClassNotFoundException e) {
            throw new SQLException(
                "MySQL JDBC Driver not found", e
            );
        }

        return DriverManager.getConnection(
            URL, username, password
        );
    }
}
