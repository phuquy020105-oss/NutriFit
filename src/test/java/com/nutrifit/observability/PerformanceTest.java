package com.nutrifit.observability;
import org.junit.jupiter.api.Test;
import java.lang.reflect.Proxy;
import java.sql.*;
import java.util.concurrent.*;
import static org.junit.jupiter.api.Assertions.*;
class PerformanceTest {
 @Test void metricsContainOnlyAllowlistedRoutesGroupsAndCountersEvenOnSqlFailure()throws Exception {
  Performance.Sample sample=Performance.begin();
  try {
   Statement statement=(Statement)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{PreparedStatement.class},(p,m,a)->{throw new SQLException("raw secret fixture");});
   Connection raw=(Connection)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{Connection.class},(p,m,a)->statement);
   Connection c=Performance.instrument(raw);Performance.acquired(System.nanoTime());
   assertThrows(SQLException.class,()->c.prepareStatement("SELECT * FROM users WHERE email='private@example.invalid'").executeQuery());
   String report=sample.summary("/private@example.invalid?password=secret",500);
   assertTrue(report.contains("route=other"));assertTrue(report.contains("queries=1"));assertTrue(report.contains("connections=1"));
   assertFalse(report.contains("secret"));assertFalse(report.contains("@"));assertFalse(report.contains("SELECT"));
   var executor=Executors.newSingleThreadExecutor();try{assertFalse(executor.submit(Performance::active).get());}finally{executor.shutdownNow();}
  }finally{Performance.end();}
  assertFalse(Performance.active());
 }
 @Test void disabledModeReturnsOriginalConnection() {
  assertFalse(Performance.active());assertNull(Performance.instrument(null));
  assertEquals("/assets/*",Performance.route("/assets/user-chosen.webp"));
 }
}
