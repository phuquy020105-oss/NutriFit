package com.nutrifit.config;

import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.util.Locale;
import java.util.Properties;

public final class DatabaseConfig {

    private static final String LOCAL_URL =
            "jdbc:mysql://127.0.0.1:3306/nutrifitdb_java"
            + "?useUnicode=true&characterEncoding=UTF-8";

    private DatabaseConfig() {
    }

    private static DatabasePool pool;
    private static boolean stopped;

    public static Connection getConnection() throws SQLException {
        long started = System.nanoTime();
        try {
            return com.nutrifit.observability.Performance.instrument(pool().getConnection());
        } catch (SQLException e) {
            throw new SQLException("Database connection failed; check configuration, network and TLS.",
                    e.getSQLState(), e.getErrorCode());
        } finally {
            com.nutrifit.observability.Performance.acquired(started);
        }
    }

    private static synchronized DatabasePool pool() throws SQLException {
        if (stopped) throw new SQLException("Database pool is closed.");
        if (pool == null) pool = new DatabasePool(new PhysicalDataSource());
        return pool;
    }

    public static synchronized void closePool() {
        stopped = true;
        if (pool != null) pool.close();
    }

    // Only the pool opens physical connections; all existing callers close logical leases.
    static Connection openPhysical() throws SQLException {
        String configuredUrl = System.getenv("NUTRIFIT_DB_URL");
        boolean customUrl = configuredUrl != null && !configuredUrl.isBlank();
        String localName = System.getenv("NUTRIFIT_LOCAL_DB_NAME");
        if (localName != null && !localName.isBlank()
                && (customUrl || !localName.matches("nutrifit_[a-z0-9_]+_test"))) {
            throw new SQLException("NUTRIFIT_LOCAL_DB_NAME accepts only an isolated local test database and no custom URL.");
        }
        String url = customUrl ? configuredUrl.strip() : localName != null && !localName.isBlank()
                ? LOCAL_URL.replace("/nutrifitdb_java", "/" + localName) : LOCAL_URL;
        String username = required("NUTRIFIT_DB_USER");
        String password = required("NUTRIFIT_DB_PASSWORD");
        String caFile = System.getenv("NUTRIFIT_DB_CA_FILE");

        Properties properties = new Properties();
        properties.setProperty("user", username);
        properties.setProperty("password", password);
        properties.setProperty("paranoid", "true");
        if (customUrl) {
            validateUrl(url);
            properties.setProperty("connectTimeout", "10000");
            // A custom URL never inherits Connector/J's opportunistic TLS default.
            properties.setProperty("sslMode", "VERIFY_IDENTITY");
            properties.setProperty("allowPublicKeyRetrieval", "false");
        }
        if (caFile != null && !caFile.isBlank()) {
            if (!customUrl) {
                throw new SQLException("NUTRIFIT_DB_CA_FILE requires NUTRIFIT_DB_URL.");
            }
            DatabaseTrustStore.configure(properties, caFile.strip());
        }

        try {
            Class.forName("com.mysql.cj.jdbc.Driver");
        } catch (ClassNotFoundException e) {
            throw new SQLException("MySQL JDBC Driver not found.");
        }
        try {
            return DriverManager.getConnection(url, properties);
        } catch (SQLException e) {
            // Controllers log this exception. Do not retain driver messages/causes
            // that might include a connection URL, credentials or other secrets.
            throw new SQLException(
                    "Database connection failed; check configuration, network and TLS.",
                    e.getSQLState(), e.getErrorCode());
        }
    }

    private static final class PhysicalDataSource implements javax.sql.DataSource {
        @Override public Connection getConnection() throws SQLException { return openPhysical(); }
        @Override public Connection getConnection(String u,String p) throws SQLException { throw new java.sql.SQLFeatureNotSupportedException(); }
        @Override public java.io.PrintWriter getLogWriter() { return null; }
        @Override public void setLogWriter(java.io.PrintWriter writer) throws SQLException { if(writer!=null)throw new java.sql.SQLFeatureNotSupportedException(); }
        @Override public void setLoginTimeout(int seconds) { }
        @Override public int getLoginTimeout() { return 10; }
        @Override public java.util.logging.Logger getParentLogger() { return java.util.logging.Logger.getLogger("com.nutrifit.config"); }
        @Override public <T> T unwrap(Class<T> type) throws SQLException { throw new java.sql.SQLFeatureNotSupportedException(); }
        @Override public boolean isWrapperFor(Class<?> type) { return false; }
        @Override public String toString() { return "NutriFit physical datasource"; }
    }

    private static String required(String name) throws SQLException {
        String value = System.getenv(name);
        if (value == null || value.isBlank()) {
            throw new SQLException("Missing database environment variable: " + name);
        }
        return value;
    }

    private static void validateUrl(String url) throws SQLException {
        try {
            if (!url.startsWith("jdbc:mysql://")) {
                throw new IllegalArgumentException();
            }
            URI uri = URI.create(url.substring("jdbc:".length()));
            if (uri.getHost() == null || uri.getRawUserInfo() != null
                    || uri.getRawFragment() != null || uri.getPath() == null
                    || uri.getPath().length() <= 1) {
                throw new IllegalArgumentException();
            }
            String query = uri.getRawQuery();
            if (query == null) {
                return;
            }
            for (String parameter : query.split("&")) {
                String[] pair = parameter.split("=", 2);
                String key = URLDecoder.decode(pair[0], StandardCharsets.UTF_8)
                        .toLowerCase(Locale.ROOT);
                String value = pair.length == 2
                        ? URLDecoder.decode(pair[1], StandardCharsets.UTF_8) : "";
                // URL properties override DriverManager Properties. Reject settings
                // that could weaken TLS or replace the managed CA truststore.
                boolean forbidden = switch (key) {
                    case "sslmode" -> !"VERIFY_IDENTITY".equalsIgnoreCase(value);
                    case "allowpublickeyretrieval" -> !"false".equalsIgnoreCase(value);
                    case "usessl", "requiressl", "verifyservercertificate" ->
                            !"true".equalsIgnoreCase(value);
                    case "user", "password", "trustcertificatekeystoreurl",
                         "trustcertificatekeystoretype", "trustcertificatekeystorepassword",
                         "fallbacktosystemtruststore" -> true;
                    default -> false;
                };
                if (forbidden) {
                    throw new SQLException("NUTRIFIT_DB_URL contains credentials or unsupported TLS settings; "
                            + "use VERIFY_IDENTITY and NUTRIFIT_DB_CA_FILE.");
                }
            }
        } catch (IllegalArgumentException e) {
            throw new SQLException("NUTRIFIT_DB_URL must be a single-host jdbc:mysql:// URL "
                    + "with a database name and without embedded credentials.");
        }
    }
}
