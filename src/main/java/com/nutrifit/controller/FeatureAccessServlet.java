package com.nutrifit.controller;

import com.nutrifit.dto.FeatureAccessDTO;
import com.nutrifit.service.PremiumAccessService;
import com.nutrifit.util.*;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.*;
import java.io.IOException;
import java.sql.SQLException;
import java.util.List;
import java.util.stream.Collectors;

@WebServlet("/api/features")
public class FeatureAccessServlet extends HttpServlet {
    private final PremiumAccessService premium=new PremiumAccessService();
    @Override protected void doGet(HttpServletRequest req,HttpServletResponse resp)throws ServletException,IOException {
        try {
            long uid=SessionUser.requireId(req);
            List<FeatureAccessDTO> states=premium.getFeatureStates(uid);
            String json=states.stream().map(s->"{\"code\":"+JsonLite.quote(s.code().name())+
                ",\"module\":"+JsonLite.quote(s.module())+",\"requiredTier\":"+JsonLite.quote(s.requiredTier())+
                ",\"label\":"+JsonLite.quote(s.displayLabel())+",\"unlocked\":"+s.unlocked()+"}").collect(Collectors.joining(",","[","]"));
            resp.setContentType("application/json; charset=UTF-8");resp.setHeader("Cache-Control","no-store");resp.getWriter().write(json);
        }catch(SecurityException e){resp.sendError(401,"Login required");}
        catch(SQLException e){throw new ServletException("Feature check failed",e);}
    }
}
