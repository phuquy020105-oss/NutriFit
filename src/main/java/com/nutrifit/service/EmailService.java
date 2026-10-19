package com.nutrifit.service;

import com.nutrifit.util.JsonLite;
import jakarta.mail.MessagingException;
import jakarta.mail.internet.AddressException;
import jakarta.mail.internet.InternetAddress;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;

/** Brevo HTTPS transport; OTP generation, persistence and verification remain in Auth. */
public class EmailService {
    private static final URI ENDPOINT = URI.create("https://api.brevo.com/v3/smtp/email");
    private static final HttpClient HTTP = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .followRedirects(HttpClient.Redirect.NEVER)
            .build();

    private final String apiKey;
    private final String senderEmail;
    private final String senderName;

    public EmailService() {
        apiKey = required("BREVO_API_KEY");
        if (!apiKey.chars().allMatch(c -> c >= 33 && c <= 126)) {
            throw new IllegalStateException("BREVO_API_KEY must be a valid HTTP header value.");
        }
        senderEmail = required("BREVO_SENDER_EMAIL").strip();
        if (!isMailbox(senderEmail)) {
            throw new IllegalStateException("BREVO_SENDER_EMAIL must contain one valid email address.");
        }
        String name = System.getenv("BREVO_SENDER_NAME");
        senderName = name == null || name.isBlank() ? "NutriFit" : name.strip();
    }

    public void sendRegistrationOtp(String recipientEmail, String otp) throws MessagingException {
        validate(recipientEmail, otp);
        String body = """
                Xin chào,

                Mã OTP đăng ký tài khoản NutriFit của bạn là: %s

                Mã có hiệu lực trong 5 phút.
                Không chia sẻ mã này với bất cứ ai.

                Nếu bạn không yêu cầu đăng ký, hãy bỏ qua email này.

                NutriFit Team
                """.formatted(otp);
        send(recipientEmail, "NutriFit - Mã xác minh đăng ký", body);
    }

    public void sendPasswordResetOtp(String recipientEmail, String otp) throws MessagingException {
        validate(recipientEmail, otp);
        String body = """
                Xin chào,

                Bạn vừa yêu cầu đặt lại mật khẩu NutriFit.

                Mã OTP của bạn là: %s

                Mã có hiệu lực trong 5 phút.
                Không chia sẻ mã này với bất kỳ ai.

                Nếu bạn không yêu cầu đổi mật khẩu, hãy bỏ qua email này.

                NutriFit Team
                """.formatted(otp);
        send(recipientEmail, "NutriFit - Mã OTP đặt lại mật khẩu", body);
    }

    private void send(String recipientEmail, String subject, String text) throws MessagingException {
        String payload = "{\"sender\":{\"name\":" + JsonLite.quote(senderName)
                + ",\"email\":" + JsonLite.quote(senderEmail)
                + "},\"to\":[{\"email\":" + JsonLite.quote(recipientEmail)
                + "}],\"subject\":" + JsonLite.quote(subject)
                + ",\"textContent\":" + JsonLite.quote(text) + "}";
        HttpRequest request = HttpRequest.newBuilder(ENDPOINT)
                .timeout(Duration.ofSeconds(20))
                .header("api-key", apiKey)
                .header("Accept", "application/json")
                .header("Content-Type", "application/json; charset=utf-8")
                .POST(HttpRequest.BodyPublishers.ofString(payload, StandardCharsets.UTF_8))
                .build();
        try {
            // Discard all provider bodies: neither response details nor OTP enter logs.
            HttpResponse<Void> response = HTTP.send(request, HttpResponse.BodyHandlers.discarding());
            if (response.statusCode() != 201) {
                throw new MessagingException("Brevo email request failed (HTTP "
                        + response.statusCode() + ").");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new MessagingException("Email delivery was interrupted.");
        } catch (IOException e) {
            // Do not attach upstream exceptions that might contain request details.
            throw new MessagingException("Cannot reach the email provider over HTTPS.");
        }
    }

    private static String required(String name) {
        String value = System.getenv(name);
        if (value == null || value.isBlank()) {
            throw new IllegalStateException("Missing email environment variable: " + name);
        }
        return value;
    }

    private static void validate(String recipientEmail, String otp) {
        if (!isMailbox(recipientEmail)) {
            throw new IllegalArgumentException("Recipient email must contain one valid address.");
        }
        if (otp == null || !otp.matches("\\d{6}")) {
            throw new IllegalArgumentException("OTP must contain 6 digits");
        }
    }

    private static boolean isMailbox(String value) {
        if (value == null || value.isBlank() || value.indexOf('\r') >= 0 || value.indexOf('\n') >= 0) {
            return false;
        }
        try {
            InternetAddress address = new InternetAddress(value, true);
            address.validate();
            return address.getPersonal() == null && value.equals(address.getAddress());
        } catch (AddressException e) {
            return false;
        }
    }
}
