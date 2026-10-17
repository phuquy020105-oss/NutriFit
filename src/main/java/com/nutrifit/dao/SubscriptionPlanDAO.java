package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.model.SubscriptionPlan;
import java.sql.*;
import java.util.*;

/** SQL mapped to the uploaded database/schema.sql (provided 2026-10-16). */
public class SubscriptionPlanDAO {
    private static SubscriptionPlan map(ResultSet rs) throws SQLException {
        return new SubscriptionPlan(rs.getLong("plan_id"),rs.getString("plan_name"),
            rs.getLong("price_vnd"),rs.getInt("duration_days"),rs.getString("description"));
    }
    public List<SubscriptionPlan> findAllActive() throws SQLException {
        String sql="SELECT plan_id, plan_name, price_vnd, duration_days, description FROM subscriptionplans WHERE is_active=1 ORDER BY price_vnd";
        try(Connection c=DatabaseConfig.getConnection();PreparedStatement s=c.prepareStatement(sql);ResultSet r=s.executeQuery()){
            List<SubscriptionPlan> list=new ArrayList<>(); while(r.next())list.add(map(r)); return list;
        }
    }
    public SubscriptionPlan findActive(long id, Connection c) throws SQLException {
        return findById(id, true, c);
    }
    public SubscriptionPlan findById(long id, boolean activeOnly, Connection c) throws SQLException {
        String sql="SELECT plan_id, plan_name, price_vnd, duration_days, description FROM subscriptionplans WHERE plan_id=?" + (activeOnly ? " AND is_active=1" : "");
        try(PreparedStatement s=c.prepareStatement(sql)){
            s.setLong(1,id);try(ResultSet r=s.executeQuery()){return r.next()?map(r):null;}
        }
    }
}
