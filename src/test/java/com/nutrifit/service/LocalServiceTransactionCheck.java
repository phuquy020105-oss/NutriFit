package com.nutrifit.service;
import com.nutrifit.performance.LocalPerformanceCheck;
import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.*;
import com.nutrifit.dto.*;
import com.nutrifit.model.MealEntry;
import java.sql.*;
import java.math.BigDecimal;
import java.time.Clock;
import java.util.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;

/** Explicit real-DB regression, guarded to the approved LOCAL test target. Never JUnit-auto-run. */
public final class LocalServiceTransactionCheck {
 static void check(boolean value,String reason){if(!value)throw new IllegalStateException(reason);}
 public static void main(String[] args)throws Exception {
  LocalPerformanceCheck.requireTarget();
  check("LOCAL-PERFORMANCE-TEST".equals(System.getenv("VNPAY_TMN_CODE")),"Only synthetic VNPay configuration allowed");
  try {
   long user,plan,price;
   try(Connection c=DatabaseConfig.getConnection();var s=c.createStatement()) {
    try(var q=s.executeQuery("SELECT user_id FROM users WHERE email='performance-0@example.invalid'")){check(q.next(),"Missing fixture");user=q.getLong(1);}
    try(var q=s.executeQuery("SELECT plan_id,price_vnd FROM subscriptionplans ORDER BY plan_id LIMIT 1")){check(q.next(),"Missing sample plan");plan=q.getLong(1);price=q.getLong(2);}
    try(var q=s.executeQuery("SELECT COUNT(*) FROM mealplans")){q.next();check(q.getInt(1)==0,"Test requires untouched fixture journal; never clear data");}
   }
   MealSuggestion draft=new MealRecommendationService().recommendDay(user);
   MealEntryDAO injected=new MealEntryDAO(){int writes;
    @Override public long insert(Connection c,MealEntry e)throws SQLException {long id=super.insert(c,e);if(++writes==2)throw new SQLException("Injected second-entry failure");return id;}
   };
   var failing=new MealPlannerService(new MealPlanDAO(),injected,new JdbcRecipeReadAdapter(),new NutritionCalculator(),Clock.systemDefaultZone());
   try{failing.saveSuggestion(user,draft,Map.of());throw new AssertionError("Rollback injection did not fail");}catch(SQLException expected){ }
   try(Connection c=DatabaseConfig.getConnection();var s=c.createStatement();var q=s.executeQuery("SELECT (SELECT COUNT(*) FROM mealplans)+(SELECT COUNT(*) FROM mealentries)")){q.next();check(q.getInt(1)==0,"Nutrition partial transaction persisted");}
   new MealPlannerService().saveSuggestion(user,draft,Map.of());
   try(Connection c=DatabaseConfig.getConnection();var s=c.createStatement();var q=s.executeQuery("SELECT COUNT(*),SUM(servings<>1.00),COUNT(DISTINCT meal_type) FROM mealentries")){q.next();check(q.getInt(1)==3&&q.getInt(2)==0&&q.getInt(3)==3,"Nutrition save not three standard meals");}
   System.out.println("PASS actual pooled Nutrition: preview0writes/injected failure rollback/atomic3meal commit");
   PaymentService payments=new PaymentService();
   String ref="LOCALPERF"+UUID.randomUUID().toString().replace("-","");
   try(Connection c=DatabaseConfig.getConnection()){new PaymentTransactionDAO().insert(user,plan,price,ref,c);}
   Map<String,String> callback=new HashMap<>(Map.of("vnp_TmnCode",System.getenv("VNPAY_TMN_CODE"),"vnp_TxnRef",ref,"vnp_Amount",Long.toString(price*100),"vnp_ResponseCode","00","vnp_TransactionStatus","00","vnp_CurrCode","VND"));
   check(payments.processIpn(callback).equals(IpnResult.BAD_HASH),"Unsigned IPN accepted");
   callback.put("vnp_Amount",Long.toString(price*100+1));sign(callback);
   check(payments.processIpn(callback).equals(IpnResult.INVALID_AMOUNT),"Wrong amount accepted");
   check("PENDING".equals(payments.getUserPayment(ref,user).status()),"Invalid amount wrote payment");
   callback.put("vnp_Amount",Long.toString(price*100));sign(callback);
   check(payments.processIpn(callback).equals(IpnResult.OK),"Synthetic signed IPN failed");
   java.time.LocalDateTime expiry;
   try(Connection c=DatabaseConfig.getConnection();var s=c.prepareStatement("SELECT premium_expires_at FROM users WHERE user_id=?")){s.setLong(1,user);try(var q=s.executeQuery()){q.next();expiry=q.getTimestamp(1).toLocalDateTime();}}
   check(payments.processIpn(callback).equals(IpnResult.ALREADY_PROCESSED),"Duplicate IPN processed twice");
   try(Connection c=DatabaseConfig.getConnection();var s=c.prepareStatement("SELECT premium_expires_at FROM users WHERE user_id=?")){s.setLong(1,user);try(var q=s.executeQuery()){q.next();check(expiry.equals(q.getTimestamp(1).toLocalDateTime()),"Duplicate IPN extended Premium");}}
   System.out.println("PASS synthetic local IPN:bad signature/wrong amount rollback/signed commit/duplicate no double extension; no VNPay network");
  }finally{DatabaseConfig.closePool();}
 }
 static void sign(Map<String,String> callback)throws Exception {
  Mac mac=Mac.getInstance("HmacSHA512");mac.init(new SecretKeySpec(System.getenv("VNPAY_HASH_SECRET").getBytes(StandardCharsets.UTF_8),"HmacSHA512"));
  callback.put("vnp_SecureHash",HexFormat.of().formatHex(mac.doFinal(VnpayService.canonical(callback).getBytes(StandardCharsets.UTF_8))));
 }
}
