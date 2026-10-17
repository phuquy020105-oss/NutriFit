package com.nutrifit.controller;

import com.nutrifit.service.ChatService;
import com.nutrifit.util.SessionUser;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.*;
import java.io.IOException;
import java.sql.SQLException;

@WebServlet("/chatbot")
public class ChatServlet extends HttpServlet {
    private final ChatService chat=new ChatService();
    @Override protected void doGet(HttpServletRequest req,HttpServletResponse res)throws ServletException,IOException {
        try{
            long userId=SessionUser.requireId(req);
            res.setHeader("Cache-Control", "no-store");
            long conversationId=parseId(req.getParameter("conversationId"));
            req.setAttribute("conversations",chat.conversations(userId));
            req.setAttribute("messages",conversationId==0?java.util.List.of():chat.history(userId,conversationId));
            req.setAttribute("conversationId",conversationId);
            req.setAttribute("csrf",SessionUser.csrf(req.getSession()));
            req.setAttribute("geminiModel", System.getenv().getOrDefault("GEMINI_MODEL", "gemini-3.8-flash"));
            req.getRequestDispatcher("/WEB-INF/views/chatbot/chat.jsp").forward(req,res);
        }catch(SecurityException e){res.sendError(403,"Login or conversation ownership required");}
        catch(IllegalArgumentException e){res.sendError(400,"Invalid conversation");}
        catch(SQLException e){throw new ServletException("Read chat failed",e);}
    }
    @Override protected void doPost(HttpServletRequest req,HttpServletResponse res)throws ServletException,IOException {
        req.setCharacterEncoding("UTF-8");
        try{
            long userId=SessionUser.requireId(req);
            if(!SessionUser.validCsrf(req)){res.sendError(403,"Invalid CSRF token");return;}
            String text=req.getParameter("text");
            if(text==null||text.isBlank()||text.length()>2000){res.sendError(400,"Message too long or empty");return;}
            // Basic per-session, per-instance throttle; use shared persistent limiter for production scale.
            HttpSession session=req.getSession(false);
            synchronized(session){
                Long last=(Long)session.getAttribute("nutrifitLastChatMs");
                long now=System.currentTimeMillis();
                if(last!=null&&now-last<2500){res.sendError(429,"Please wait before sending again");return;}
                session.setAttribute("nutrifitLastChatMs",now);
            }
            long conversationId=parseId(req.getParameter("conversationId"));
            long result=chat.send(userId,conversationId,text);
            res.sendRedirect(req.getContextPath()+"/chatbot?conversationId="+result);
        }catch(SecurityException e){res.sendError(403,"Unauthorized");}
        catch(IllegalArgumentException e){res.sendError(400,"Invalid request");}
        catch(SQLException e){throw new ServletException("Save chat failed",e);}
    }
    private static long parseId(String s){
        if(s==null||s.isBlank())return 0;
        long id=Long.parseLong(s);if(id<0)throw new IllegalArgumentException("Bad ID");return id;
    }
}
