package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.model.ChatConversation;
import java.sql.*;
import java.util.*;

public class ChatConversationDAO {
    public List<ChatConversation> findForUser(long userId)throws SQLException {
        String sql="SELECT conversation_id,user_id,title FROM chatconversations WHERE user_id=? ORDER BY updated_at DESC LIMIT 50";
        try(Connection c=DatabaseConfig.getConnection();PreparedStatement s=c.prepareStatement(sql)){
            s.setLong(1,userId);try(ResultSet r=s.executeQuery()){
                List<ChatConversation> result=new ArrayList<>();
                while(r.next())result.add(new ChatConversation(r.getLong(1),r.getLong(2),r.getString(3)));
                return result;
            }
        }
    }
    public boolean ownedBy(long conversationId,long userId,Connection c)throws SQLException {
        try(PreparedStatement s=c.prepareStatement("SELECT 1 FROM chatconversations WHERE conversation_id=? AND user_id=?")) {
            s.setLong(1,conversationId);s.setLong(2,userId);
            try(ResultSet r=s.executeQuery()){return r.next();}
        }
    }
    public long create(long userId,String title,Connection c)throws SQLException {
        String sql="INSERT INTO chatconversations(user_id,title,created_at,updated_at) VALUES(?,?,NOW(),NOW())";
        try(PreparedStatement s=c.prepareStatement(sql,Statement.RETURN_GENERATED_KEYS)){
            s.setLong(1,userId);s.setString(2,title);
            if(s.executeUpdate()!=1)throw new SQLException("Could not create conversation");
            try(ResultSet r=s.getGeneratedKeys()){if(r.next())return r.getLong(1);}
            throw new SQLException("No generated conversation ID");
        }
    }
    public void touch(long conversationId,Connection c)throws SQLException {
        try(PreparedStatement s=c.prepareStatement("UPDATE chatconversations SET updated_at=NOW() WHERE conversation_id=?")) {
            s.setLong(1,conversationId);s.executeUpdate();
        }
    }
}
