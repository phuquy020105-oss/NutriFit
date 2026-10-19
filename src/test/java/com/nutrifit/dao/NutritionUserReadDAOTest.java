package com.nutrifit.dao;

import java.lang.reflect.Proxy;
import java.sql.*;
import java.time.LocalDateTime;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class NutritionUserReadDAOTest {
    @Test void onlyPremiumWithStrictlyFutureExpiryIsActive() throws Exception {
        LocalDateTime now=LocalDateTime.of(2026,10,19,12,0);
        for (String status : new String[]{"FREE","PREMIUM"}) for (LocalDateTime expiry :
                new LocalDateTime[]{null,now.minusSeconds(1),now,now.plusSeconds(1)}) {
            ResultSet rs=(ResultSet) Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{ResultSet.class},
                    (p,m,a)->switch(m.getName()){
                        case "next" -> true;
                        case "getString" -> status;
                        case "getTimestamp" -> expiry==null?null:Timestamp.valueOf(expiry);
                        case "close" -> null;
                        default -> throw new AssertionError(m.getName());
                    });
            PreparedStatement ps=(PreparedStatement) Proxy.newProxyInstance(getClass().getClassLoader(),
                    new Class<?>[]{PreparedStatement.class},(p,m,a)->switch(m.getName()){
                        case "setLong" -> {assertEquals(42L,a[1]);yield null;}
                        case "executeQuery" -> rs;
                        case "close" -> null;
                        default -> throw new AssertionError(m.getName());
                    });
            Connection c=(Connection) Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{Connection.class},
                    (p,m,a)->{assertEquals("prepareStatement",m.getName());return ps;});
            assertEquals("PREMIUM".equals(status)&&expiry!=null&&expiry.isAfter(now),
                    new NutritionUserReadDAO().hasPremiumAccess(c,42,now));
        }
    }
}
