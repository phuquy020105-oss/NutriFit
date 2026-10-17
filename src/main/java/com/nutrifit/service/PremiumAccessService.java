package com.nutrifit.service;

import com.nutrifit.config.*;
import com.nutrifit.dao.PremiumUserDAO;
import com.nutrifit.dto.FeatureAccessDTO;
import com.nutrifit.model.FeatureCode;
import java.sql.*;
import java.time.*;
import java.util.*;

/** Proposed SHARED service. Coordinate with Auth/Nutrition/Workout teams before merging. */
public final class PremiumAccessService {
    private final PremiumUserDAO users=new PremiumUserDAO();
    public boolean hasActivePremium(long userId)throws SQLException {
        try(Connection c=DatabaseConfig.getConnection();PreparedStatement s=c.prepareStatement(
            "SELECT subscription_status,premium_expires_at FROM users WHERE user_id=?")) {
            s.setLong(1,userId);
            try(ResultSet r=s.executeQuery()){
                if(!r.next())return false;
                Timestamp expires=r.getTimestamp(2);
                return "PREMIUM".equals(r.getString(1))&&expires!=null&&expires.toLocalDateTime().isAfter(LocalDateTime.now());
            }
        }
    }
    public boolean canUse(long userId,FeatureCode code)throws SQLException {
        FeatureAccessDTO d=FeatureCatalog.describe(code,false);
        return "FREE".equals(d.requiredTier())||hasActivePremium(userId);
    }
    public void requireFeature(long userId,FeatureCode code)throws SQLException {
        if(!canUse(userId,code))throw new SecurityException("PREMIUM_REQUIRED");
    }
    public List<FeatureAccessDTO> getFeatureStates(long userId)throws SQLException {
        boolean premium=hasActivePremium(userId);
        List<FeatureAccessDTO> result=new ArrayList<>();
        for(FeatureCode code:FeatureCode.values())result.add(FeatureCatalog.describe(code,premium));
        return result;
    }
    /** Caller owns transaction: extend and mark payment SUCCESS atomically. */
    public void extendPremium(long userId,int days,Connection c)throws SQLException {
        if(days<=0||days>3650)throw new IllegalArgumentException("Invalid premium duration");
        LocalDateTime expiry=users.lockExpiry(userId,c);
        LocalDateTime now=LocalDateTime.now();
        LocalDateTime from=expiry!=null&&expiry.isAfter(now)?expiry:now;
        users.updateExpiry(userId,from.plusDays(days),c);
    }
}
