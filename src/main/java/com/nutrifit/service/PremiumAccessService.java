package com.nutrifit.service;

import java.sql.SQLException;

public class PremiumAccessService {

    /**
     * TODO: thay bằng lời gọi DAO của module payment/user
     * (kiểm tra subscription còn hạn). Tạm thời trả về false:
     * user chỉ thấy bài FREE, không bao giờ lộ bài PREMIUM.
     */
    public boolean hasActivePremium(long userId) throws SQLException {
        return false;
    }
}
