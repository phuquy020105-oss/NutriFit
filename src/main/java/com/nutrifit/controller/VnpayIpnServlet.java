package com.nutrifit.controller;

import com.nutrifit.dto.IpnResult;
import com.nutrifit.service.PaymentService;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.*;
import java.io.IOException;
import java.util.*;

/** VNPay server callback: PUBLIC HTTPS endpoint, signature verified by service. */
@WebServlet("/payment/ipn")
public class VnpayIpnServlet extends HttpServlet {
    private final PaymentService payments=new PaymentService();
    @Override protected void doGet(HttpServletRequest req,HttpServletResponse res)throws IOException {
        Map<String,String> params=new HashMap<>();
        req.getParameterMap().forEach((key,v)->{
            if(v!=null&&v.length==1)params.put(key,v[0]);
        });
        IpnResult result=payments.processIpn(params);
        res.setContentType("application/json; charset=UTF-8");
        res.setHeader("Cache-Control","no-store");
        res.getWriter().write("{\"RspCode\":\""+result.code()+"\",\"Message\":\""+result.message()+"\"}");
    }
}
