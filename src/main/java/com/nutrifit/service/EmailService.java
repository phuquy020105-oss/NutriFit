
package com.nutrifit.service;

import jakarta.mail.Authenticator;
import jakarta.mail.Message;
import jakarta.mail.MessagingException;
import jakarta.mail.PasswordAuthentication;
import jakarta.mail.Session;
import jakarta.mail.Transport;
import jakarta.mail.internet.InternetAddress;
import jakarta.mail.internet.MimeMessage;

import java.nio.charset.StandardCharsets;
import java.util.Properties;

public class EmailService {

    private final String smtpUser;
    private final String smtpPassword;

    public EmailService() {
        this.smtpUser = System.getenv("NUTRIFIT_SMTP_USER");
        this.smtpPassword = System.getenv("NUTRIFIT_SMTP_PASSWORD");

        if (smtpUser == null || smtpUser.isBlank()
                || smtpPassword == null || smtpPassword.isBlank()) {
            throw new IllegalStateException(
                "Missing Gmail SMTP environment variables"
            );
        }
    }

    public void sendRegistrationOtp(String recipientEmail, String otp)
            throws MessagingException {

        if (recipientEmail == null || recipientEmail.isBlank()) {
            throw new IllegalArgumentException("Recipient email is required");
        }

        if (otp == null || !otp.matches("\\d{6}")) {
            throw new IllegalArgumentException("OTP must contain 6 digits");
        }

        Properties props = new Properties();

        props.put("mail.smtp.host", "smtp.gmail.com");
        props.put("mail.smtp.port", "587");
        props.put("mail.smtp.auth", "true");
        props.put("mail.smtp.starttls.enable", "true");
        props.put("mail.smtp.starttls.required", "true");

        props.put("mail.smtp.connectiontimeout", "10000");
        props.put("mail.smtp.timeout", "10000");
        props.put("mail.smtp.writetimeout", "10000");

        props.put("mail.smtp.ssl.checkserveridentity", "true");

        Session session = Session.getInstance(
            props,
            new Authenticator() {
                @Override
                protected PasswordAuthentication getPasswordAuthentication() {
                    return new PasswordAuthentication(
                        smtpUser,
                        smtpPassword
                    );
                }
            }
        );

        MimeMessage message = new MimeMessage(session);

        message.setFrom(new InternetAddress(smtpUser));

        message.setRecipient(
            Message.RecipientType.TO,
            new InternetAddress(recipientEmail, true)
        );

        message.setSubject(
            "NutriFit - Ma xac minh dang ky",
            StandardCharsets.UTF_8.name()
        );

        String body =
            "Xin chào,\n\n"
            + "Mã OTP đăng ký tài khoản NutriFit của bạn là: "
            + otp + "\n\n"
            + "Mã có hiệu lực trong 5 phút.\n"
            + "Không chia sẽ mã này với bất cứ ai.\n\n"
            + "Nếu bạn không yêu cầu đăng ký, "
            + "hãy bỏ qua email này.\n\n"
            + "NutriFit Team";

        message.setText(
            body,
            StandardCharsets.UTF_8.name()
        );

        Transport.send(message);
    }

public void sendPasswordResetOtp(String recipientEmail, String otp)
        throws MessagingException {

    if (recipientEmail == null || recipientEmail.isBlank()) {
        throw new IllegalArgumentException("Recipient email is required");
    }

    if (otp == null || !otp.matches("\\d{6}")) {
        throw new IllegalArgumentException("OTP must contain 6 digits");
    }

    Properties props = new Properties();
    props.put("mail.smtp.host", "smtp.gmail.com");
    props.put("mail.smtp.port", "587");
    props.put("mail.smtp.auth", "true");
    props.put("mail.smtp.starttls.enable", "true");
    props.put("mail.smtp.starttls.required", "true");
    props.put("mail.smtp.connectiontimeout", "10000");
    props.put("mail.smtp.timeout", "10000");
    props.put("mail.smtp.writetimeout", "10000");
    props.put("mail.smtp.ssl.checkserveridentity", "true");

    Session session = Session.getInstance(props, new Authenticator() {
        @Override
        protected PasswordAuthentication getPasswordAuthentication() {
            return new PasswordAuthentication(smtpUser, smtpPassword);
        }
    });

    MimeMessage message = new MimeMessage(session);
    message.setFrom(new InternetAddress(smtpUser));
    message.setRecipient(
            Message.RecipientType.TO,
            new InternetAddress(recipientEmail, true)
    );

    message.setSubject(
            "NutriFit - Ma OTP dat lai mat khau",
            StandardCharsets.UTF_8.name()
    );

    String body = """
            Xin chào,

            Bạn vừa yêu cầu đặt lại mật khẩu NutriFit.

            Mã OTP của bạn là: %s

            Mã có hiệu lực trong 5 phút.
            Không chia sẽ mã này với bất kì ai.

            Nếu bạn không có yêu cầu đổi lại mật khẩu,
            hãy bỏ qua email này.

            NutriFit Team
            """.formatted(otp);

    message.setText(body, StandardCharsets.UTF_8.name());
    Transport.send(message);
}

}
