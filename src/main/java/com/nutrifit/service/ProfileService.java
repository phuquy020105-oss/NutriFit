
package com.nutrifit.service;

import com.nutrifit.dao.UserDAO;
import com.nutrifit.model.User;
import com.nutrifit.util.PasswordUtil;

import java.sql.SQLException;

public class ProfileService {

    private final UserDAO userDAO = new UserDAO();

    public void updateFullName(Long userId, String fullName)
            throws SQLException {

        if (userId == null) {
            throw new IllegalArgumentException(
                    "Phiên đăng nhập không hợp lệ.");
        }

        if (fullName == null
                || fullName.trim().isEmpty()
                || fullName.trim().length() > 100) {

            throw new IllegalArgumentException(
                    "Họ tên phải có từ 1 đến 100 ký tự.");
        }

        boolean updated = userDAO.updateFullName(
                userId, fullName.trim());

        if (!updated) {
            throw new IllegalArgumentException(
                    "Không tìm thấy tài khoản.");
        }
    }

    public void changePassword(
            Long userId,
            String currentPassword,
            String newPassword,
            String confirmPassword) throws SQLException {

        if (userId == null) {
            throw new IllegalArgumentException(
                    "Phiên đăng nhập không hợp lệ.");
        }

        if (currentPassword == null
                || currentPassword.isEmpty()) {
            throw new IllegalArgumentException(
                    "Vui lòng nhập mật khẩu hiện tại.");
        }

        if (newPassword == null
                || newPassword.length() < 8) {
            throw new IllegalArgumentException(
                    "Mật khẩu mới phải có ít nhất 8 ký tự.");
        }

        if (!newPassword.equals(confirmPassword)) {
            throw new IllegalArgumentException(
                    "Xác nhận mật khẩu không khớp.");
        }

        User user = userDAO.findById(userId)
                .orElseThrow(() ->
                        new IllegalArgumentException(
                                "Không tìm thấy tài khoản."));

        if (!PasswordUtil.verify(
                currentPassword, user.getPasswordHash())) {

            throw new IllegalArgumentException(
                    "Mật khẩu hiện tại không chính xác.");
        }

        if (PasswordUtil.verify(
                newPassword, user.getPasswordHash())) {

            throw new IllegalArgumentException(
                    "Mật khẩu mới phải khác mật khẩu cũ.");
        }

        String newHash = PasswordUtil.hash(newPassword);

        boolean updated = userDAO.updatePasswordById(
                userId, newHash);

        if (!updated) {
            throw new SQLException(
                    "Không thể cập nhật mật khẩu.");
        }
    }
}
