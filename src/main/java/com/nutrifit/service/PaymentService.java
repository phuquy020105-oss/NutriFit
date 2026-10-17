package com.nutrifit.service;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.*;
import com.nutrifit.dto.*;
import com.nutrifit.model.*;
import java.math.BigInteger;
import java.sql.*;
import java.security.SecureRandom;
import java.time.*;
import java.util.*;

public final class PaymentService {
    private static final SecureRandom RNG=new SecureRandom();
    private final SubscriptionPlanDAO plans=new SubscriptionPlanDAO();
    private final PaymentTransactionDAO transactions=new PaymentTransactionDAO();
    private final PremiumAccessService premium=new PremiumAccessService();
    public CheckoutDTO checkout(long userId,long planId,String clientIp)throws SQLException {
        VnpayService vnpay=new VnpayService();
        try(Connection c=DatabaseConfig.getConnection()) {
            SubscriptionPlan plan=plans.findActive(planId,c);
            if(plan==null||plan.priceVnd()<=0||plan.priceVnd()>9_999_999_999L||plan.durationDays()<=0)throw new IllegalArgumentException("Invalid plan");
            // Random, DB-unique transaction reference; no user-controlled price.
            String ref=new BigInteger(130,RNG).toString(32).toUpperCase(Locale.ROOT);
            String url=vnpay.paymentUrl(plan,ref,clientIp);
            transactions.insert(userId,plan.id(),plan.priceVnd(),ref,c);
            return new CheckoutDTO(ref,url);
        }
    }
    public IpnResult processIpn(Map<String,String> payload){
        VnpayService vnpay;
        try{vnpay=new VnpayService();}catch(Exception e){return IpnResult.ERROR;}
        if(!vnpay.validCallback(payload))return IpnResult.BAD_HASH;
        String ref=payload.get("vnp_TxnRef");
        if(ref==null||ref.isBlank())return IpnResult.UNKNOWN;
        try(Connection c=DatabaseConfig.getConnection()){
            c.setAutoCommit(false);
            try{
                PaymentTransaction tx=transactions.lockByReference(ref,c);
                if(tx==null){c.rollback();return IpnResult.UNKNOWN;}
                long received=new BigInteger(Objects.requireNonNullElse(payload.get("vnp_Amount"),"-")).longValueExact();
                if(Math.multiplyExact(tx.amountVnd(),100)!=received){c.rollback();return IpnResult.INVALID_AMOUNT;}
                if(!"PENDING".equals(tx.status())){c.rollback();return IpnResult.ALREADY_PROCESSED;}
                boolean success="00".equals(payload.get("vnp_ResponseCode")) && "00".equals(payload.get("vnp_TransactionStatus"));
                if(!transactions.updateIfPending(tx.id(),success?"SUCCESS":"FAILED",c)){
                    c.rollback();return IpnResult.ALREADY_PROCESSED;
                }
                if(success){
                    SubscriptionPlan plan=plans.findById(tx.planId(),false,c);
                    // Plan must be preserved for pending payments even if later marked inactive.
                    if(plan==null || plan.durationDays()<=0)throw new SQLException("Paid plan missing");
                    premium.extendPremium(tx.userId(),plan.durationDays(),c);
                }
                c.commit();return IpnResult.OK;
            }catch(Exception e){c.rollback();return IpnResult.ERROR;}
            finally{c.setAutoCommit(true);}
        }catch(SQLException e){return IpnResult.ERROR;}
    }
    public PaymentTransaction getUserPayment(String ref,long userId)throws SQLException {
        return transactions.findForUser(ref,userId);
    }
}
