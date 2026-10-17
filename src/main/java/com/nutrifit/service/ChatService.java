package com.nutrifit.service;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.*;
import com.nutrifit.model.*;
import java.sql.*;
import java.io.IOException;
import java.util.logging.Logger;
import java.util.*;

public final class ChatService {
    private static final Logger LOG=Logger.getLogger(ChatService.class.getName());
    private final ChatConversationDAO conversations=new ChatConversationDAO();
    private final ChatMessageDAO messages=new ChatMessageDAO();
    private final GeminiClient ai=new GeminiClient();
    /** User-facing diagnostics, no credentials or provider response bodies exposed. */
    private static String toUserMessage(Exception error) {
        String reason = error.getMessage() == null ? "" : error.getMessage();
        if (reason.equals("GEMINI_API_KEY_MISSING"))
            return "Chưa thiết lập Gemini API Key trên Tomcat. Hãy cấu hình GEMINI_API_KEY rồi khởi động lại.";
        if (reason.startsWith("GEMINI_ACCESS_DENIED"))
            return "Gemini từ chối truy cập (401/403). Kiểm tra quyền API Key và dự án Google AI Studio.";
        if (reason.equals("GEMINI_MODEL_NOT_FOUND"))
            return "Model Gemini đang chọn chưa khả dụng (404). Hãy kiểm tra GEMINI_MODEL và danh sách model của dự án.";
        if (reason.equals("GEMINI_QUOTA_EXCEEDED"))
            return "Gemini đã chạm quota/rate limit (429). Hãy đợi rồi thử lại hoặc kiểm tra hạn mức/billing.";
        if (reason.startsWith("GEMINI_SERVER_"))
            return "Dịch vụ Gemini đang gặp sự cố. Vui lòng thử lại sau.";
        if (reason.equals("GEMINI_BAD_REQUEST_INVALID_KEY"))
            return "Gemini báo API Key không hợp lệ (400). Hãy tạo key mới đúng dự án trong Google AI Studio.";
        if (reason.equals("GEMINI_BAD_REQUEST_BILLING_OR_REGION"))
            return "Gemini yêu cầu cấu hình billing hoặc chưa hỗ trợ gói API tại khu vực này (400). Kiểm tra Google AI Studio.";
        if (reason.equals("GEMINI_BAD_REQUEST_MODEL_INCOMPATIBLE"))
            return "Model Gemini chưa hỗ trợ yêu cầu hiện tại (400). Kiểm tra GEMINI_MODEL.";
        if (reason.equals("GEMINI_BAD_REQUEST_UNSUPPORTED_PARAMETER"))
            return "Tham số gửi tới Gemini không được hỗ trợ (400). Hãy kiểm tra cấu hình model.";
        if (reason.startsWith("GEMINI_BAD_REQUEST_"))
            return "Gemini trả về 400 (" + reason.substring("GEMINI_BAD_REQUEST_".length()) +
                    "). Hãy chạy test-gemini.ps1 để xác định nguyên nhân chi tiết.";
        if (error instanceof java.net.http.HttpTimeoutException)
            return "Gemini trả lời quá lâu. Tin nhắn của bạn đã được lưu, hãy thử lại sau.";
        return "NutriFit AI tạm thời không khả dụng. Tin nhắn đã được lưu; vui lòng thử lại sau.";
    }

    private static String safeReason(Exception error) {
        // Internal log only known error codes, never arbitrary HTTP messages/secrets.
        String code = error.getMessage();
        return code != null && code.matches("GEMINI_[A-Z_0-9]+") ? code : "NETWORK_OR_PARSE_ERROR";
    }

    public List<ChatConversation> conversations(long userId)throws SQLException{return conversations.findForUser(userId);}
    public List<ChatMessage> history(long userId,long conversationId)throws SQLException {
        try(Connection c=DatabaseConfig.getConnection()){
            if(!conversations.ownedBy(conversationId,userId,c))throw new SecurityException("Conversation does not belong to user");
        }
        return messages.history(conversationId,userId,100);
    }
    public long send(long userId,long conversationId,String text)throws SQLException {
        if(text==null||text.isBlank()||text.length()>2000)throw new IllegalArgumentException("Text length must be 1..2000");
        long id=conversationId;
        try(Connection c=DatabaseConfig.getConnection()){
            c.setAutoCommit(false);
            try {
                if(id==0)id=conversations.create(userId,text.length()>60?text.substring(0,60):text,c);
                else if(!conversations.ownedBy(id,userId,c))throw new SecurityException("Conversation does not belong to user");
                messages.insert(id,"USER",text.strip(),c);
                conversations.touch(id,c);c.commit();
            }catch(Exception ex){c.rollback();throw ex;}
            finally{c.setAutoCommit(true);}
        }
        // IMPORTANT: call remote AI outside JDBC transaction and without an open connection.
        List<ChatMessage> recent=messages.history(id,userId,16);
        String reply;
        String role="ASSISTANT";
        try {
            reply=ai.generateReply(recent);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            LOG.warning("Gemini request interrupted");
            role="SYSTEM";
            reply="NutriFit AI đang gián đoạn. Tin nhắn của bạn đã được lưu, vui lòng thử lại sau.";
        } catch (IOException | IllegalStateException e) {
            // Do not turn a provider outage into a browser error page; preserve chat history.
            // Never log API keys or the user's messages.
            LOG.warning("Gemini failure: " + e.getClass().getSimpleName() + " / " + safeReason(e));
            role="SYSTEM";
            reply=toUserMessage(e);
        }
        try(Connection c=DatabaseConfig.getConnection()){
            if(!conversations.ownedBy(id,userId,c))throw new SecurityException("Conversation does not belong to user");
            messages.insert(id,role,reply,c);
            conversations.touch(id,c);
        }
        return id;
    }
}
