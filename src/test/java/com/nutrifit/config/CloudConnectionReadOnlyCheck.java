package com.nutrifit.config;
import java.sql.*;
import java.util.*;
/** Explicit, bounded SELECT-only connection experiment; not a JUnit test or web endpoint. */
public final class CloudConnectionReadOnlyCheck {
 public static void main(String[] args)throws Exception {
  String expected="jdbc:mysql://nutrifit-mysql-buihaidagggg-d131.g.aivencloud.com:27047/nutrifitdb?sslMode=VERIFY_IDENTITY";
  if(!expected.equals(System.getenv("NUTRIFIT_DB_URL"))||System.getenv("NUTRIFIT_DB_CA_FILE")==null||System.getenv("NUTRIFIT_LOCAL_DB_NAME")!=null)throw new IllegalStateException("Exact approved cloud read-only target/TLS/CA required");
  try {
   for(boolean pooled:List.of(false,true)) {
    List<Double> acquire=new ArrayList<>();List<Double> sql=new ArrayList<>();
    for(int i=0;i<5;i++) {
     long begin=System.nanoTime();
     try(Connection c=pooled?DatabaseConfig.getConnection():DatabaseConfig.openPhysical()) {
      double elapsed=(System.nanoTime()-begin)/1e6;long q=System.nanoTime();
      try(var s=c.createStatement();var result=s.executeQuery("SELECT 1,DATABASE(),@@session.wait_timeout,@@max_connections")) {
       if(!result.next()||result.getInt(1)!=1||!"nutrifitdb".equals(result.getString(2)))throw new IllegalStateException("Wrong read-only target");
       if(i==0)System.out.println("AIVEN SELECT-only mode="+(pooled?"pool":"direct")+" wait_timeout="+result.getLong(3)+" max_connections="+result.getLong(4));
      }
      // warm samples only; the first TLS/pool initialization is deliberately separate.
      if(i>0){acquire.add(elapsed);sql.add((System.nanoTime()-q)/1e6);}
     }
    }
    Collections.sort(acquire);Collections.sort(sql);
    System.out.printf(Locale.ROOT,"READONLY client-to-Aiven mode=%s n=4 acquire_median_ms=%.3f acquire_max_ms=%.3f select_median_ms=%.3f%n",pooled?"pool":"direct",(acquire.get(1)+acquire.get(2))/2,acquire.getLast(),(sql.get(1)+sql.get(2))/2);
   }
  }finally{DatabaseConfig.closePool();}
 }
}
