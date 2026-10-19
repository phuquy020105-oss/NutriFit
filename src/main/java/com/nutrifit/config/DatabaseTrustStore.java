package com.nutrifit.config;

import java.io.InputStream;
import java.io.OutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.InvalidPathException;
import java.nio.file.Path;
import java.nio.file.attribute.PosixFilePermissions;
import java.security.GeneralSecurityException;
import java.security.KeyStore;
import java.security.SecureRandom;
import java.security.cert.Certificate;
import java.security.cert.CertificateFactory;
import java.security.cert.X509Certificate;
import java.sql.SQLException;
import java.util.Arrays;
import java.util.Collection;
import java.util.HexFormat;
import java.util.Properties;

/** A private Connector/J truststore; JVM HTTPS trust configuration is untouched. */
final class DatabaseTrustStore {
    private static Properties cached;

    private DatabaseTrustStore() {
    }

    static synchronized void configure(Properties properties, String caFile) throws SQLException {
        if (cached == null) {
            cached = create(caFile);
        }
        properties.putAll(cached);
    }

    private static Properties create(String caFile) throws SQLException {
        Path storeFile = null;
        byte[] random = new byte[32];
        new SecureRandom().nextBytes(random);
        char[] password = HexFormat.of().formatHex(random).toCharArray();
        try {
            Path certificateFile = Path.of(caFile);
            if (!Files.isRegularFile(certificateFile) || !Files.isReadable(certificateFile)) {
                throw new IOException();
            }
            Collection<? extends Certificate> certificates;
            try (InputStream input = Files.newInputStream(certificateFile)) {
                certificates = CertificateFactory.getInstance("X.509").generateCertificates(input);
            }
            if (certificates.isEmpty()) {
                throw new GeneralSecurityException();
            }
            KeyStore store = KeyStore.getInstance("PKCS12");
            store.load(null, password);
            int index = 0;
            for (Certificate certificate : certificates) {
                if (!(certificate instanceof X509Certificate ca) || ca.getBasicConstraints() < 0) {
                    throw new GeneralSecurityException();
                }
                ca.checkValidity();
                store.setCertificateEntry("aiven-ca-" + index++, ca);
            }
            Path temp = Path.of(System.getProperty("java.io.tmpdir"));
            if (Files.getFileStore(temp).supportsFileAttributeView("posix")) {
                storeFile = Files.createTempFile(temp, "nutrifit-jdbc-ca-", ".p12",
                        PosixFilePermissions.asFileAttribute(PosixFilePermissions.fromString("rw-------")));
            } else {
                // Local Windows development uses the current user's temp ACLs.
                storeFile = Files.createTempFile(temp, "nutrifit-jdbc-ca-", ".p12");
            }
            try (OutputStream output = Files.newOutputStream(storeFile)) {
                store.store(output, password);
            }
            storeFile.toFile().deleteOnExit();
            Properties result = new Properties();
            result.setProperty("trustCertificateKeyStoreUrl", storeFile.toUri().toASCIIString());
            result.setProperty("trustCertificateKeyStoreType", "PKCS12");
            result.setProperty("trustCertificateKeyStorePassword", new String(password));
            result.setProperty("fallbackToSystemTrustStore", "false");
            return result;
        } catch (IOException | GeneralSecurityException | InvalidPathException e) {
            if (storeFile != null) {
                try {
                    Files.deleteIfExists(storeFile);
                } catch (IOException ignored) {
                    // Contains only CA certificates; the container temp directory is ephemeral.
                }
            }
            throw new SQLException("Cannot load NUTRIFIT_DB_CA_FILE; provide a readable, valid PEM CA certificate.");
        } finally {
            Arrays.fill(password, '\0');
            Arrays.fill(random, (byte) 0);
        }
    }
}
