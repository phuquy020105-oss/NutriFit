package com.nutrifit.dao;

import java.sql.*;
import java.time.LocalDateTime;

/** Only Payment owns writes to Premium status; Auth module retains shared User model. */
public class PremiumUserDAO {
    public LocalDateTime lockExpiry(long userId,Connection conn)throws SQLException {
        try(PreparedStatement s=conn.prepareStatement("SELECT premium_expires_at FROM users WHERE user_id=? FOR UPDATE")){
            s.setLong(1,userId);try(ResultSet r=s.executeQuery()){
                if(!r.next())throw new SQLException("User not found");
                Timestamp t=r.getTimestamp(1);return t==null?null:t.toLocalDateTime();
            }
        }
    }
    public void updateExpiry(long userId,LocalDateTime expiresAt,Connection conn)throws SQLException {
        try(PreparedStatement s=conn.prepareStatement("UPDATE users SET subscription_status='PREMIUM',premium_expires_at=? WHERE user_id=?")){
            s.setTimestamp(1,Timestamp.valueOf(expiresAt));s.setLong(2,userId);
            if(s.executeUpdate()!=1)throw new SQLException("Premium update failed");
        }
    }
}
