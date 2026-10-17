
package com.nutrifit.service;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.PasswordResetOTPDAO;
import com.nutrifit.dao.RegistrationOTPIPQuotaDAO;
import com.nutrifit.dao.UserDAO;
import com.nutrifit.util.PasswordUtil;

import jakarta.mail.MessagingException;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.util.HexFormat;
import java.util.Locale;

public class PasswordResetService {

    private static final int OTP_EXPIRY_MINUTES = 5;
    private static final int COOLDOWN_SECONDS = 60;
    private static final int MAX_SENDS_PER_HOUR = 3;
    private static final int MAX_ATTEMPTS = 5;

    private final PasswordResetOTPDAO otpDAO =
            new PasswordResetOTPDAO();

    private final RegistrationOTPIPQuotaDAO ipQuotaDAO =
            new RegistrationOTPIPQuotaDAO();

    private final UserDAO userDAO = new UserDAO();

    private final SecureRandom random = new SecureRandom();

    // ============================================
    // 1. GỬI OTP ĐẶT LẠI MẬT KHẨU
    // ============================================

    public void requestReset(String rawEmail, String clientIp)
            throws SQLException, MessagingException {

        String email = normalizeEmail(rawEmail);
        validateEmail(email);

        if (clientIp == null || clientIp.isBlank()) {
            throw new IllegalArgumentException(
                    "Không xác định được địa chỉ IP.");
        }

        // Dùng chung giới hạn 10 yêu cầu/giờ/IP
        // với chức năng đăng ký.
        if (!ipQuotaDAO.tryConsumeQuota(clientIp)) {
            return;
        }

        // Không tiết lộ email có tồn tại hay không.
        if (userDAO.findByEmail(email).isEmpty()) {
            return;
        }

        String lockName = buildLockName(email);

        try (Connection conn = DatabaseConfig.getConnection()) {

            boolean lockAcquired = false;
            boolean transactionStarted = false;

            try {
                lockAcquired = acquireLock(conn, lockName);

                if (!lockAcquired) {
                    throw new IllegalStateException(
                            "Hệ thống đang bận. Vui lòng thử lại.");
                }

                conn.setAutoCommit(false);
                transactionStarted = true;

                LocalDateTime now = LocalDateTime.now();

                PasswordResetOTPDAO.PasswordResetOTP existing =
                        otpDAO.findByEmailForUpdate(conn, email);

                int sentInWindow = 1;
                LocalDateTime windowStart = now;

                if (existing != null) {

                    // Chờ ít nhất 60 giây trước khi gửi lại.
                    if (existing.lastSentAt()
                            .plusSeconds(COOLDOWN_SECONDS)
                            .isAfter(now)) {
                        conn.rollback();
                        return;
                    }

                    // Tối đa 3 lần gửi trong 1 giờ/email.
                    if (existing.windowStart()
                            .plusHours(1).isAfter(now)) {

                        if (existing.sentInWindow()
                                >= MAX_SENDS_PER_HOUR) {
                            conn.rollback();
                            return;
                        }

                        sentInWindow =
                                existing.sentInWindow() + 1;

                        windowStart = existing.windowStart();
                    }
                }

                String otp = String.format(
                        Locale.ROOT,
                        "%06d",
                        random.nextInt(1_000_000)
                );

                PasswordResetOTPDAO.PasswordResetOTP record =
                        new PasswordResetOTPDAO.PasswordResetOTP(
                                email,
                                PasswordUtil.hash(otp),
                                now.plusMinutes(OTP_EXPIRY_MINUTES),
                                0,
                                now,
                                windowStart,
                                sentInWindow
                        );

                otpDAO.save(conn, record);

                new EmailService().sendPasswordResetOtp(
                        email, otp);

                conn.commit();

            } catch (SQLException | MessagingException |
                     RuntimeException e) {

                if (transactionStarted) {
                    try {
                        conn.rollback();
                    } catch (SQLException rollbackError) {
                        e.addSuppressed(rollbackError);
                    }
                }

                throw e;

            } finally {

                try {
                    if (transactionStarted) {
                        conn.setAutoCommit(true);
                    }
                } finally {
                    if (lockAcquired) {
                        releaseLock(conn, lockName);
                    }
                }
            }
        }
    }

    // ============================================
    // 2. XÁC MINH OTP VÀ ĐỔI MẬT KHẨU
    // ============================================

    public void resetPassword(
            String rawEmail,
            String otp,
            String newPassword) throws SQLException {

        String email = normalizeEmail(rawEmail);
        validateEmail(email);

        if (otp == null || !otp.matches("\\d{6}")) {
            throw new IllegalArgumentException(
                    "Mã OTP phải gồm 6 chữ số.");
        }

        if (newPassword == null || newPassword.length() < 8) {
            throw new IllegalArgumentException(
                    "Mật khẩu mới phải có ít nhất 8 ký tự.");
        }

        String errorMessage = null;
        boolean success = false;

        try (Connection conn = DatabaseConfig.getConnection()) {

            conn.setAutoCommit(false);

            try {
                PasswordResetOTPDAO.PasswordResetOTP record =
                        otpDAO.findByEmailForUpdate(conn, email);

                if (record == null) {

                    errorMessage =
                            "OTP không hợp lệ hoặc đã hết hạn.";

                } else if (!record.expiresAt()
                        .isAfter(LocalDateTime.now())) {

                    otpDAO.deleteByEmail(conn, email);
                    errorMessage = "OTP đã hết hạn.";

                } else if (record.attempts() >= MAX_ATTEMPTS) {

                    errorMessage =
                            "Đã vượt quá 5 lần nhập OTP. "
                            + "Vui lòng yêu cầu mã mới.";

                } else if (!PasswordUtil.verify(
                        otp, record.otpHash())) {

                    otpDAO.incrementAttempts(conn, email);

                    int remaining =
                            MAX_ATTEMPTS - record.attempts() - 1;

                    if (remaining <= 0) {
                        errorMessage =
                                "Đã nhập sai OTP 5 lần. "
                                + "Vui lòng yêu cầu mã mới.";
                    } else {
                        errorMessage =
                                "OTP không chính xác. "
                                + "Bạn còn " + remaining
                                + " lần thử.";
                    }

                } else {

                    String passwordHash =
                            PasswordUtil.hash(newPassword);

                    boolean updated = userDAO.updatePassword(
                            conn, email, passwordHash);

                    if (!updated) {
                        throw new SQLException(
                                "Không thể cập nhật mật khẩu.");
                    }

                    // OTP chỉ được sử dụng một lần.
                    otpDAO.deleteByEmail(conn, email);
                    success = true;
                }

                // Lưu cả số lần nhập sai OTP.
                conn.commit();

            } catch (SQLException | RuntimeException e) {

                try {
                    conn.rollback();
                } catch (SQLException rollbackError) {
                    e.addSuppressed(rollbackError);
                }

                throw e;

            } finally {
                conn.setAutoCommit(true);
            }
        }

        if (!success) {
            throw new IllegalArgumentException(errorMessage);
        }
    }

    // ============================================
    // 3. VALIDATION
    // ============================================

    private String normalizeEmail(String email) {
        return email == null
                ? ""
                : email.trim().toLowerCase(Locale.ROOT);
    }

    private void validateEmail(String email) {
        if (email.isBlank()
                || email.length() > 255
                || !email.matches(
                        "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$")) {
            throw new IllegalArgumentException(
                    "Email không hợp lệ.");
        }
    }

    // ============================================
    // 4. MYSQL NAMED LOCK
    // ============================================

    private String buildLockName(String email) {

        // SHA-256 tránh va chạm dễ gặp của hashCode().
        // Giới hạn tên khóa MySQL dưới 64 ký tự.
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest(email.getBytes(StandardCharsets.UTF_8));

            return "nf:reset:" +
                    HexFormat.of().formatHex(digest, 0, 16);

        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(
                    "SHA-256 không khả dụng.", e);
        }
    }

    private boolean acquireLock(
            Connection conn, String lockName)
            throws SQLException {

        try (PreparedStatement ps = conn.prepareStatement(
                "SELECT GET_LOCK(?, 5)")) {

            ps.setString(1, lockName);

            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() && rs.getInt(1) == 1;
            }
        }
    }

    private void releaseLock(
            Connection conn, String lockName)
            throws SQLException {

        try (PreparedStatement ps = conn.prepareStatement(
                "SELECT RELEASE_LOCK(?)")) {

            ps.setString(1, lockName);
            ps.executeQuery();
        }
    }
}
