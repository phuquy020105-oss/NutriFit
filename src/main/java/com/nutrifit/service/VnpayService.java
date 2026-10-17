package com.nutrifit.service;

import com.nutrifit.model.SubscriptionPlan;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.*;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/** VNPay 2.1.0 Sandbox. Callback checksum signs sorted, URL-encoded vnp_ fields. */
public final class VnpayService {
    private static final String SANDBOX = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html";
    private final String tmn, secret, returnUrl;
    private static final DateTimeFormatter DATE = DateTimeFormatter.ofPattern("yyyyMMddHHmmss");
    public VnpayService() {
        tmn=required("VNPAY_TMN_CODE"); secret=required("VNPAY_HASH_SECRET"); returnUrl=required("VNPAY_RETURN_URL");
        if(!returnUrl.startsWith("https://") && !returnUrl.startsWith("http://localhost:") && !returnUrl.startsWith("http://127.0.0.1:")) throw new IllegalStateException("Invalid return URL");
    }
    /** Read-only configuration check for the Premium page; never expose any secret. */
    public static boolean isConfigured() {
        try {
            new VnpayService();
            return true;
        } catch (IllegalStateException ex) {
            return false;
        }
    }
    private static String required(String key){String v=System.getenv(key);if(v==null||v.isBlank())throw new IllegalStateException("Missing "+key);return v;}
    public String paymentUrl(SubscriptionPlan plan,String ref,String ip){
        Map<String,String> p=new TreeMap<>();
        p.put("vnp_Version","2.1.0");p.put("vnp_Command","pay");p.put("vnp_TmnCode",tmn);
        p.put("vnp_Amount",Long.toString(Math.multiplyExact(plan.priceVnd(),100)));
        p.put("vnp_CurrCode","VND");p.put("vnp_TxnRef",ref);
        p.put("vnp_OrderInfo","NutriFit Premium "+ref);p.put("vnp_OrderType","other");
        p.put("vnp_Locale","vn");p.put("vnp_ReturnUrl",returnUrl);
        p.put("vnp_IpAddr",ip == null || ip.isBlank()?"127.0.0.1":ip);
        LocalDateTime now=LocalDateTime.now(ZoneId.of("Asia/Ho_Chi_Minh"));
        p.put("vnp_CreateDate",DATE.format(now));p.put("vnp_ExpireDate",DATE.format(now.plusMinutes(15)));
        String query=canonical(p);return SANDBOX+"?"+query+"&vnp_SecureHash="+hmac(query);
    }
    private static String encode(String s){return URLEncoder.encode(s,StandardCharsets.UTF_8);}
    public static String canonical(Map<String,String> p){
        StringJoiner joiner=new StringJoiner("&");
        new TreeMap<>(p).forEach((k,v)->{
            if(k.startsWith("vnp_") && !k.equals("vnp_SecureHash") && !k.equals("vnp_SecureHashType") && v!=null && !v.isEmpty())
                joiner.add(encode(k)+"="+encode(v));
        });return joiner.toString();
    }
    private String hmac(String data){
        try{
            Mac mac=Mac.getInstance("HmacSHA512");mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8),"HmacSHA512"));
            return HexFormat.of().formatHex(mac.doFinal(data.getBytes(StandardCharsets.UTF_8)));
        }catch(Exception e){throw new IllegalStateException("HMAC unavailable",e);}
    }
    public boolean validCallback(Map<String,String> p){
        String hash=p.get("vnp_SecureHash");
        if(hash==null||!hash.matches("(?i)[a-f0-9]{128}"))return false;
        boolean signature = MessageDigest.isEqual(hmac(canonical(p)).getBytes(StandardCharsets.US_ASCII),hash.toLowerCase(Locale.ROOT).getBytes(StandardCharsets.US_ASCII));
        return signature && tmn.equals(p.get("vnp_TmnCode"))
            && (p.get("vnp_CurrCode") == null || "VND".equals(p.get("vnp_CurrCode")));
    }
}
