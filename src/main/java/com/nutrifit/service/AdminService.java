
package com.nutrifit.service;

import com.nutrifit.dao.AdminDAO;
import com.nutrifit.model.User;
import com.nutrifit.model.UserRole;

import java.sql.SQLException;
import java.util.List;
import java.util.Locale;

public class AdminService {

    private final AdminDAO adminDAO;

    public AdminService() {
        this.adminDAO = new AdminDAO();
    }

    public AdminService(AdminDAO adminDAO) {
        this.adminDAO = adminDAO;
    }

    // ==========================================
    // 1. THỐNG KÊ DASHBOARD
    // ==========================================

    public long getTotalUsers() throws SQLException {
        return adminDAO.countUsers();
    }

    public long getTotalAdmins() throws SQLException {
        return adminDAO.countAdmins();
    }

    public long getTotalPremiumUsers() throws SQLException {
        return adminDAO.countPremiumUsers();
    }

    public long getNewUsersToday() throws SQLException {
        return adminDAO.countNewUsersToday();
    }

    // ==========================================
    // 2. DANH SÁCH VÀ TÌM KIẾM NGƯỜI DÙNG
    // ==========================================

    public List<User> getUsers(String keyword)
            throws SQLException {

        String search = keyword == null
                ? ""
                : keyword.trim();

        if (search.length() > 100) {
            throw new IllegalArgumentException(
                    "Từ khóa tìm kiếm tối đa 100 ký tự.");
        }

        return adminDAO.findUsers(search);
    }

    // ==========================================
    // 3. CẬP NHẬT QUYỀN NGƯỜI DÙNG
    // ==========================================

    public boolean changeUserRole(
            Long adminId,
            Long targetUserId,
            String roleName) throws SQLException {

        if (adminId == null || targetUserId == null
                || adminId <= 0 || targetUserId <= 0) {

            throw new IllegalArgumentException(
                    "Thông tin tài khoản không hợp lệ.");
        }

        if (roleName == null) {
            throw new IllegalArgumentException(
                    "Vui lòng chọn vai trò.");
        }

        UserRole newRole;

        try {
            newRole = UserRole.valueOf(
                    roleName.trim().toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException e) {
            throw new IllegalArgumentException(
                    "Vai trò phải là USER hoặc ADMIN.");
        }

        return adminDAO.updateUserRole(
                adminId, targetUserId, newRole);
    }
}
