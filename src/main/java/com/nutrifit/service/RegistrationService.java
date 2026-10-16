
package com.nutrifit.service;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.RegistrationOTPDAO;
import com.nutrifit.dao.RegistrationOTPIPQuotaDAO;
import com.nutrifit.dao.UserDAO;
import com.nutrifit.model.User;
import com.nutrifit.util.PasswordUtil;
import jakarta.mail.MessagingException;

import java.security.SecureRandom;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.Locale;

public class RegistrationService {

    private static final int OTP_EXPIRY_MINUTES = 5;
    private static final int MAX_ATTEMPTS = 5;
    private static final int MAX_EMAIL_SENDS = 3;
    private static final int RESEND_WAIT_SECONDS = 60;

    private final UserDAO userDAO = new UserDAO();

    private final RegistrationOTPDAO otpDAO =
            new RegistrationOTPDAO();

    private final RegistrationOTPIPQuotaDAO ipQuotaDAO =
            new RegistrationOTPIPQuotaDAO();

    private final SecureRandom random = new SecureRandom();

    /**
     * Đăng ký tài khoản:
     * - Kiểm tra dữ liệu
     * - Kiểm tra email đã tồn tại
     * - Giới hạn số lần gửi OTP
     * - Tạo OTP 6 số
     * - Lưu OTP đã hash
     * - Gửi email thật
     */
    public void requestRegistration(
            String fullName,
            String email,
            String password,
            String clientIp
    ) throws SQLException, MessagingException {

        fullName = fullName == null
                ? ""
                : fullName.trim();

        email = normalizeEmail(email);

        validateRegistration(fullName, email, password);

        if (userDAO.findByEmail(email).isPresent()) {
            throw new IllegalArgumentException(
                    "Email này đã được đăng ký."
            );
        }

        // Kiểm tra quota IP trước khi xử lý gửi email.
        if (!ipQuotaDAO.tryConsumeQuota(clientIp)) {
            throw new IllegalArgumentException(
                    "Bạn đã yêu cầu OTP quá nhiều lần. "
                    + "Vui lòng thử lại sau."
            );
        }

        LocalDateTime now = LocalDateTime.now();

        String otp = String.format(
                Locale.ROOT,
                "%06d",
                random.nextInt(1_000_000)
        );

        String passwordHash = PasswordUtil.hash(password);
        String otpHash = PasswordUtil.hash(otp);

        /*
         * Sử dụng transaction và khóa theo email.
         * GET_LOCK giúp tuần tự hóa yêu cầu gửi OTP
         * cùng một email trên cùng MySQL server.
         */
        String lockName = "nutrifit:otp:"
                + Integer.toHexString(email.hashCode());

        try (Connection conn = DatabaseConfig.getConnection()) {

            boolean locked = acquireLock(conn, lockName);

            if (!locked) {
                throw new IllegalArgumentException(
                        "Hệ thống đang xử lý yêu cầu. "
                        + "Vui lòng thử lại."
                );
            }

            try {
                conn.setAutoCommit(false);

                if (userDAO.findByEmail(conn, email).isPresent()) {
                    throw new IllegalArgumentException(
                            "Email này đã được đăng ký."
                    );
                }

                var existing =
                        otpDAO.findByEmailForUpdate(conn, email);

                LocalDateTime windowStart = now;
                int sentInWindow = 0;

                if (existing.isPresent()) {

                    var previous = existing.get();

                    if (previous.lastSentAt()
                            .plusSeconds(RESEND_WAIT_SECONDS)
                            .isAfter(now)) {

                        throw new IllegalArgumentException(
                                "Vui lòng chờ 60 giây "
                                + "trước khi gửi lại OTP."
                        );
                    }

                    if (previous.windowStart()
                            .plusHours(1)
                            .isAfter(now)) {

                        windowStart = previous.windowStart();
                        sentInWindow = previous.sentInWindow();
                    }

                    if (sentInWindow >= MAX_EMAIL_SENDS) {
                        throw new IllegalArgumentException(
                                "Email đã vượt quá 3 lần "
                                + "yêu cầu OTP trong 1 giờ."
                        );
                    }
                }

                String sql = """
                    INSERT INTO registrationotps (
                        email,
                        full_name,
                        password_hash,
                        otp_hash,
                        expires_at,
                        last_sent_at,
                        attempts,
                        window_start,
                        sent_in_window
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
                    ON DUPLICATE KEY UPDATE
                        full_name = VALUES(full_name),
                        password_hash = VALUES(password_hash),
                        otp_hash = VALUES(otp_hash),
                        expires_at = VALUES(expires_at),
                        last_sent_at = VALUES(last_sent_at),
                        attempts = 0,
                        window_start = VALUES(window_start),
                        sent_in_window = VALUES(sent_in_window)
                    """;

                try (PreparedStatement ps =
                             conn.prepareStatement(sql)) {

                    ps.setString(1, email);
                    ps.setString(2, fullName);
                    ps.setString(3, passwordHash);
                    ps.setString(4, otpHash);

                    ps.setTimestamp(
                            5,
                            Timestamp.valueOf(
                                    now.plusMinutes(
                                            OTP_EXPIRY_MINUTES
                                    )
                            )
                    );

                    ps.setTimestamp(
                            6,
                            Timestamp.valueOf(now)
                    );

                    ps.setTimestamp(
                            7,
                            Timestamp.valueOf(windowStart)
                    );

                    ps.setInt(8, sentInWindow + 1);

                    ps.executeUpdate();
                }

                /*
                 * Gửi email trước khi commit.
                 * Nếu SMTP báo lỗi, rollback OTP mới.
                 *
                 * Lưu ý: SMTP không tham gia transaction
                 * MySQL, nên không thể bảo đảm tuyệt đối
                 * trạng thái email và database đồng bộ.
                 */
                new EmailService().sendRegistrationOtp(
                        email, otp
                );

                conn.commit();

            } catch (SQLException | MessagingException
                     | RuntimeException e) {

                conn.rollback();
                throw e;

            } finally {
                releaseLock(conn, lockName);
            }
        }
    }

    /**
     * Xác minh OTP.
     *
     * Trả về userId khi thành công.
     * Ném IllegalArgumentException khi OTP không hợp lệ.
     */
    public Long verifyRegistration(
            String email,
            String otp
    ) throws SQLException {

        email = normalizeEmail(email);

        if (email.isBlank()) {
            throw new IllegalArgumentException(
                    "Email không được để trống."
            );
        }

        if (otp == null || !otp.matches("\\d{6}")) {
            throw new IllegalArgumentException(
                    "OTP phải gồm đúng 6 chữ số."
            );
        }

        try (Connection conn = DatabaseConfig.getConnection()) {

            conn.setAutoCommit(false);

            boolean committed = false;

            try {
                var pending = otpDAO.findByEmailForUpdate(
                        conn, email
                ).orElseThrow(() ->
                        new IllegalArgumentException(
                                "Không tìm thấy yêu cầu đăng ký."
                        )
                );

                LocalDateTime now = LocalDateTime.now();

                if (!pending.expiresAt().isAfter(now)) {
                    throw new IllegalArgumentException(
                            "OTP đã hết hạn. "
                            + "Vui lòng yêu cầu mã mới."
                    );
                }

                if (pending.attempts() >= MAX_ATTEMPTS) {
                    throw new IllegalArgumentException(
                            "Bạn đã nhập sai OTP quá 5 lần. "
                            + "Vui lòng yêu cầu mã mới."
                    );
                }

                boolean valid = PasswordUtil.verify(
                        otp,
                        pending.otpHash()
                );

                if (!valid) {

                    String sql = """
                        UPDATE registrationotps
                        SET attempts = attempts + 1
                        WHERE email = ?
                        """;

                    try (PreparedStatement ps =
                                 conn.prepareStatement(sql)) {

                        ps.setString(1, email);
                        ps.executeUpdate();
                    }

                    // Lưu số lần nhập sai trước khi báo lỗi.
                    conn.commit();
                    committed = true;

                    throw new IllegalArgumentException(
                            "Mã OTP không chính xác."
                    );
                }

                if (userDAO.findByEmail(
                        conn, email
                ).isPresent()) {

                    throw new IllegalArgumentException(
                            "Email đã được đăng ký."
                    );
                }

                User user = new User();

                user.setEmail(email);
                user.setFullName(pending.fullName());
                user.setPasswordHash(pending.passwordHash());

                // Tạo tài khoản bằng cùng connection.
                Long userId = userDAO.create(conn, user);

                // Xóa OTP để không thể dùng lại.
                otpDAO.deleteByEmail(conn, email);

                conn.commit();
                committed = true;

                return userId;

            } catch (SQLException | RuntimeException e) {

                if (!committed) {
                    conn.rollback();
                }

                throw e;
            }
        }
    }

    /**
     * Kiểm tra dữ liệu đăng ký.
     */
    private void validateRegistration(
            String fullName,
            String email,
            String password
    ) {

        if (fullName.isBlank()
                || fullName.length() > 150) {

            throw new IllegalArgumentException(
                    "Họ tên phải có từ 1 đến 150 ký tự."
            );
        }

        if (email.length() > 255
                || !email.matches(
                    "^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$"
                )) {

            throw new IllegalArgumentException(
                    "Địa chỉ email không hợp lệ."
            );
        }

        if (password == null
                || password.length() < 8
                || password.length() > 72) {

            throw new IllegalArgumentException(
                    "Mật khẩu phải có từ 8 đến 72 ký tự."
            );
        }
    }

    /**
     * Chuẩn hóa email.
     */
    private String normalizeEmail(String email) {

        return email == null
                ? ""
                : email.trim().toLowerCase(Locale.ROOT);
    }

    /**
     * Khóa xử lý theo email trên MySQL.
     */
    private boolean acquireLock(
            Connection conn,
            String lockName
    ) throws SQLException {

        try (PreparedStatement ps =
                     conn.prepareStatement(
                             "SELECT GET_LOCK(?, 10)"
                     )) {

            ps.setString(1, lockName);

            try (var rs = ps.executeQuery()) {

                return rs.next()
                        && rs.getInt(1) == 1;
            }
        }
    }

    /**
     * Giải phóng khóa MySQL.
     */
    private void releaseLock(
            Connection conn,
            String lockName
    ) throws SQLException {

        try (PreparedStatement ps =
                     conn.prepareStatement(
                             "SELECT RELEASE_LOCK(?)"
                     )) {

            ps.setString(1, lockName);
            ps.executeQuery();
        }
    }
}
