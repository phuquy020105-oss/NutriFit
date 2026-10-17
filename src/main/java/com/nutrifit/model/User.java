
package com.nutrifit.model;

import java.time.LocalDateTime;

public class User {

    private Long userId;
    private String email;
    private String passwordHash;
    private String fullName;
    private UserRole role;
    private SubscriptionStatus subscriptionStatus;
    private LocalDateTime premiumExpiresAt;
    private LocalDateTime createdAt;

    // Phiên bản xác thực dùng để vô hiệu hóa session cũ
    private long authVersion;

    public User() {
    }

    public Long getUserId() {
        return userId;
    }

    public void setUserId(Long userId) {
        this.userId = userId;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPasswordHash() {
        return passwordHash;
    }

    public void setPasswordHash(String passwordHash) {
        this.passwordHash = passwordHash;
    }

    public String getFullName() {
        return fullName;
    }

    public void setFullName(String fullName) {
        this.fullName = fullName;
    }

    public UserRole getRole() {
        return role;
    }

    public void setRole(UserRole role) {
        this.role = role;
    }

    public SubscriptionStatus getSubscriptionStatus() {
        return subscriptionStatus;
    }

    public void setSubscriptionStatus(
            SubscriptionStatus subscriptionStatus) {
        this.subscriptionStatus = subscriptionStatus;
    }

    public LocalDateTime getPremiumExpiresAt() {
        return premiumExpiresAt;
    }

    public void setPremiumExpiresAt(
            LocalDateTime premiumExpiresAt) {
        this.premiumExpiresAt = premiumExpiresAt;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public long getAuthVersion() {
        return authVersion;
    }

    public void setAuthVersion(long authVersion) {
        this.authVersion = authVersion;
    }
}
