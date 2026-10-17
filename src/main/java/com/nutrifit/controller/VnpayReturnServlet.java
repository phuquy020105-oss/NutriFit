package com.nutrifit.controller;

import com.nutrifit.model.PaymentTransaction;
import com.nutrifit.service.*;
import com.nutrifit.util.SessionUser;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.*;
import java.io.IOException;
import java.sql.SQLException;
import java.util.*;

/** Browser return is display-only: never changes transaction nor Premium. */
@WebServlet("/payment/return")
public class VnpayReturnServlet extends HttpServlet {
    private final PaymentService payments=new PaymentService();
    @Override protected void doGet(HttpServletRequest req,HttpServletResponse res)throws ServletException,IOException {
        try{
            long uid=SessionUser.requireId(req);
            Map<String,String> params=new HashMap<>();
            req.getParameterMap().forEach((k,v)->{if(v!=null&&v.length==1)params.put(k,v[0]);});
            boolean valid=new VnpayService().validCallback(params);
            PaymentTransaction tx=valid?payments.getUserPayment(params.get("vnp_TxnRef"),uid):null;
            req.setAttribute("state",tx==null?"INVALID":tx.status());
            req.setAttribute("txnRef",tx==null?"":tx.txnRef());
            req.getRequestDispatcher("/WEB-INF/views/payment/result.jsp").forward(req,res);
        }catch(SecurityException e){res.sendError(401,"Login required");}
        catch(SQLException|IllegalStateException e){throw new ServletException("Read payment failed",e);}
    }
}
