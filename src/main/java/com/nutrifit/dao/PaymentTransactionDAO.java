package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.model.PaymentTransaction;
import java.sql.*;

/** SQL column names verified against schema.sql (provided 2026-10-16). */
public class PaymentTransactionDAO {
    public void insert(long userId,long planId,long amountVnd,String ref,Connection c) throws SQLException {
        String sql="INSERT INTO paymenttransactions(user_id,plan_id,amount_vnd,method,transaction_code,status,created_at,updated_at) VALUES(?,?,?,'VNPAY',?,'PENDING',NOW(),NOW())";
        try(PreparedStatement s=c.prepareStatement(sql)){
            s.setLong(1,userId);s.setLong(2,planId);s.setLong(3,amountVnd);s.setString(4,ref);
            if(s.executeUpdate()!=1)throw new SQLException("Could not create payment");
        }
    }
    private PaymentTransaction map(ResultSet r)throws SQLException {
        return new PaymentTransaction(r.getLong("transaction_id"),r.getLong("user_id"),r.getLong("plan_id"),r.getLong("amount_vnd"),r.getString("transaction_code"),r.getString("status"));
    }
    public PaymentTransaction lockByReference(String ref,Connection c)throws SQLException {
        try(PreparedStatement s=c.prepareStatement("SELECT transaction_id,user_id,plan_id,amount_vnd,transaction_code,status FROM paymenttransactions WHERE transaction_code=? FOR UPDATE")){
            s.setString(1,ref);try(ResultSet r=s.executeQuery()){return r.next()?map(r):null;}
        }
    }
    public PaymentTransaction findForUser(String ref,long userId)throws SQLException {
        try(Connection c=DatabaseConfig.getConnection();PreparedStatement s=c.prepareStatement("SELECT transaction_id,user_id,plan_id,amount_vnd,transaction_code,status FROM paymenttransactions WHERE transaction_code=? AND user_id=?")){
            s.setString(1,ref);s.setLong(2,userId);try(ResultSet r=s.executeQuery()){return r.next()?map(r):null;}
        }
    }
    public boolean updateIfPending(long id,String status,Connection c)throws SQLException {
        String sql="UPDATE paymenttransactions SET status=?,paid_at=CASE WHEN ?='SUCCESS' THEN NOW() ELSE paid_at END,updated_at=NOW() WHERE transaction_id=? AND status='PENDING'";
        try(PreparedStatement s=c.prepareStatement(sql)){
            s.setString(1,status);s.setString(2,status);s.setLong(3,id);return s.executeUpdate()==1;
        }
    }
}
