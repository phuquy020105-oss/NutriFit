package com.nutrifit.filter;

import com.nutrifit.dao.UserProfileDAO;
import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.annotation.WebFilter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;
import java.io.IOException;
import java.sql.SQLException;

@WebFilter(urlPatterns={"/dashboard","/dashboard/*","/nutrition/*",
        "/workout","/workout/*","/chatbot"})
public class OnboardingGateFilter implements Filter {
    private final UserProfileDAO dao = new UserProfileDAO();
    @Override public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest request=(HttpServletRequest)req;
        HttpServletResponse response=(HttpServletResponse)res;
        HttpSession session=request.getSession(false);
        if(session==null || !(session.getAttribute("userId") instanceof Long userId)) {
            response.sendRedirect(request.getContextPath()+"/login");return;
        }
        try {
            if(!dao.isComplete(userId)) {
                response.sendRedirect(request.getContextPath()+"/onboarding");return;
            }
        } catch(SQLException ex) {throw new ServletException("Không thể kiểm tra hồ sơ",ex);}
        chain.doFilter(req,res);
    }
}
