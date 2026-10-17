package com.nutrifit.dao;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.model.ChatMessage;
import java.sql.*;
import java.util.*;

public class ChatMessageDAO {
    public List<ChatMessage> history(long conversationId,long userId,int max)throws SQLException {
        String sql="SELECT m.message_id,m.conversation_id,m.sender_role,m.content FROM chatmessages m JOIN chatconversations c ON c.conversation_id=m.conversation_id WHERE m.conversation_id=? AND c.user_id=? ORDER BY m.message_id DESC LIMIT ?";
        try(Connection c=DatabaseConfig.getConnection();PreparedStatement s=c.prepareStatement(sql)){
            s.setLong(1,conversationId);s.setLong(2,userId);s.setInt(3,max);
            try(ResultSet r=s.executeQuery()){
                List<ChatMessage> list=new ArrayList<>();
                while(r.next())list.add(new ChatMessage(r.getLong(1),r.getLong(2),r.getString(3),r.getString(4)));
                Collections.reverse(list);return list;
            }
        }
    }
    public void insert(long conversationId,String role,String text,Connection c)throws SQLException {
        String sql="INSERT INTO chatmessages(conversation_id,sender_role,content,created_at) VALUES(?,?,?,NOW())";
        try(PreparedStatement s=c.prepareStatement(sql)){
            s.setLong(1,conversationId);s.setString(2,role);s.setString(3,text);
            if(s.executeUpdate()!=1)throw new SQLException("Could not insert chat message");
        }
    }
}
