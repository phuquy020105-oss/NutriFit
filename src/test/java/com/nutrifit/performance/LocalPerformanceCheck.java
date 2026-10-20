package com.nutrifit.performance;
import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.util.PasswordUtil;
import java.sql.*;
/** Explicit fixture executable, never auto-run by JUnit or packaged in the WAR. */
public final class LocalPerformanceCheck {
 public static void requireTarget() {
  if(!"nutrifit_performance_20261020_test".equals(System.getenv("NUTRIFIT_LOCAL_DB_NAME"))
    ||System.getenv("NUTRIFIT_DB_URL")!=null&&!System.getenv("NUTRIFIT_DB_URL").isBlank())throw new IllegalStateException("Approved local target required");
 }
 public static void main(String[] args)throws Exception {
  requireTarget();String db=System.getenv("NUTRIFIT_LOCAL_DB_NAME");
  try(Connection c=DatabaseConfig.getConnection()) {
   try(var s=c.createStatement();var q=s.executeQuery("SELECT DATABASE()")){if(!q.next()||!db.equals(q.getString(1)))throw new IllegalStateException("Wrong database");}
   if("setup-additional".equals(args[0])) {
    c.setAutoCommit(false);
    try(var p=c.prepareStatement("INSERT INTO users(email,password_hash,full_name,role,subscription_status) VALUES(?,?,?,'USER','FREE')",Statement.RETURN_GENERATED_KEYS)) {
     p.setString(1,"performance-2@example.invalid");p.setString(2,PasswordUtil.hash(System.getenv("NUTRIFIT_BENCH_PASSWORD")));p.setString(3,"Local benchmark");p.executeUpdate();
     try(var keys=p.getGeneratedKeys()){keys.next();try(var profile=c.prepareStatement("INSERT INTO userprofiles(user_id,gender,age,height_cm,weight_kg,activity_level,goal,bmr,tdee,target_kcal,target_water_ml) VALUES(?,'male',25,170,65,'moderate','maintain',1600,2200,2200,2500)")){profile.setLong(1,keys.getLong(1));profile.executeUpdate();}}
    }
    c.commit();
    System.out.println("PASS additional equivalent Free/empty-journal fixture; earlier transaction evidence retained");
   } else if("setup".equals(args[0])) {
    try(var s=c.createStatement();var q=s.executeQuery("SELECT COUNT(*) FROM users")){q.next();if(q.getInt(1)!=0)throw new IllegalStateException("Requires zero users; never overwrite");}
    c.setAutoCommit(false);
    try {
     for(int i=0;i<2;i++) {
      try(var s=c.prepareStatement("INSERT INTO users(email,password_hash,full_name,role,subscription_status,premium_expires_at) VALUES(?,?,?,?,?,?)",Statement.RETURN_GENERATED_KEYS)) {
       s.setString(1,"performance-"+i+"@example.invalid");s.setString(2,PasswordUtil.hash(System.getenv("NUTRIFIT_BENCH_PASSWORD")));s.setString(3,"Local benchmark");s.setString(4,i==0?"USER":"ADMIN");s.setString(5,i==0?"FREE":"PREMIUM");s.setTimestamp(6,i==0?null:Timestamp.valueOf(java.time.LocalDateTime.now().plusDays(2)));s.executeUpdate();
       try(var k=s.getGeneratedKeys()){k.next();try(var profile=c.prepareStatement("INSERT INTO userprofiles(user_id,gender,age,height_cm,weight_kg,activity_level,goal,bmr,tdee,target_kcal,target_water_ml) VALUES(?,'male',25,170,65,'moderate','maintain',1600,2200,2200,2500)")){profile.setLong(1,k.getLong(1));profile.executeUpdate();}}
      }
     }
     c.commit();
    }catch(Exception e){c.rollback();throw e;}
    System.out.println("PASS two isolated accounts for actual BCrypt login; no production access");
   } else if("inspect".equals(args[0])) {
    try(var s=c.createStatement();var q=s.executeQuery("SELECT @@version,@@wait_timeout,@@max_connections")){q.next();System.out.println("LOCAL MySQL="+q.getString(1)+" wait_timeout="+q.getLong(2)+" max_connections="+q.getLong(3));}
    for(String sql:new String[]{"SELECT * FROM users WHERE user_id=1","SELECT * FROM userprofiles WHERE user_id=1","SELECT SUM(amount_ml) FROM waterintakelog WHERE user_id=1 AND logged_date=CURRENT_DATE()","SELECT weight_kg,recorded_date FROM bodymetriclog WHERE user_id=1 ORDER BY recorded_date DESC,metric_id DESC LIMIT 1"})try(var s=c.createStatement();var q=s.executeQuery("EXPLAIN FORMAT=TRADITIONAL "+sql)){while(q.next())System.out.println("EXPLAIN table="+q.getString("table")+" type="+q.getString("type")+" key="+q.getString("key")+" rows="+q.getString("rows"));}
   } else if("integration".equals(args[0])) { integration(c); }
   else throw new IllegalArgumentException("Unknown action");
  }finally{DatabaseConfig.closePool();}
 }
 static void check(boolean condition,String message){if(!condition)throw new IllegalStateException(message);}
 static void integration(Connection c)throws Exception {
  long user;try(var s=c.createStatement();var q=s.executeQuery("SELECT user_id FROM users WHERE email='performance-0@example.invalid'")){check(q.next(),"Missing fixture");user=q.getLong(1);}
  c.setAutoCommit(false);
  try {
   // All test mutations here are uncommitted and always rolled back.
   for(int i=0;i<3;i++) {
    try(var p=c.prepareStatement("INSERT INTO waterintakelog(user_id,logged_date,amount_ml) VALUES(?,CURRENT_DATE()-INTERVAL ? DAY,?)")){p.setLong(1,user);p.setInt(2,i==2?1:0);p.setInt(3,100+i*50);p.executeUpdate();}
    try(var p=c.prepareStatement("INSERT INTO bodymetriclog(user_id,recorded_date,weight_kg) VALUES(?,CURRENT_DATE()-INTERVAL ? DAY,?)")){p.setLong(1,user);p.setInt(2,i==2?1:0);p.setInt(3,66+i);p.executeUpdate();}
    try(var p=c.prepareStatement("INSERT INTO workoutlogs(user_id,workout_id,logged_date,duration_minutes,met_value,estimated_calories) SELECT ?,MIN(workout_id),CURRENT_DATE()-INTERVAL ? DAY,?,3,? FROM workouts")){p.setLong(1,user);p.setInt(2,i==2?1:0);p.setInt(3,10+i*10);p.setInt(4,100+i*100);p.executeUpdate();}
   }
   var data=new com.nutrifit.dao.DashboardReadDAO().find(c,user);
   check(data.get("waterToday").equals(250L)&&data.get("workoutSessions").equals(2L)&&data.get("workoutMinutes").equals(30L),"Dashboard row multiplication or day mismatch");
   check(((java.math.BigDecimal)data.get("workoutCalories")).compareTo(new java.math.BigDecimal("300"))==0,"Workout calories changed");
   check(((java.math.BigDecimal)data.get("latestWeight")).compareTo(new java.math.BigDecimal("67"))==0,"Latest metric order changed");
   var absent=new com.nutrifit.dao.DashboardReadDAO().find(c,Long.MAX_VALUE);
   check(absent.get("targetCalories")==null&&absent.get("latestWeight")==null&&absent.get("waterToday").equals(0L),"Missing profile/empty aggregates changed");
   System.out.println("PASS Dashboard multiple rows/day/owner/empty/latest tie-break equivalence");
  }finally{c.rollback();c.setAutoCommit(true);}
  String lock="nutrifit:local-pool-test:"+java.util.UUID.randomUUID();
  try(Connection named=DatabaseConfig.getConnection();var stmt=named.prepareStatement("SELECT GET_LOCK(?,0)")) {
   stmt.setString(1,lock);try(var q=stmt.executeQuery()){check(q.next()&&q.getInt(1)==1,"Local named lock unavailable");}
   // Deliberately omit RELEASE_LOCK to simulate an interrupted OTP cleanup path.
  }
  boolean released=false;
  for(int i=0;i<100&&!released;i++) {
   try(var stmt=c.prepareStatement("SELECT IS_FREE_LOCK(?)")){stmt.setString(1,lock);try(var q=stmt.executeQuery()){released=q.next()&&q.getInt(1)==1;}}
   if(!released)Thread.sleep(10); // Hikari's physical close executor is asynchronous.
  }
  check(released,"Named lock leaked through pooled close");
  System.out.println("PASS actual MySQL named lock released on physical retirement; no cross-request lock leak");
  var executor=java.util.concurrent.Executors.newFixedThreadPool(8);
  java.util.Set<Long> sockets=java.util.concurrent.ConcurrentHashMap.newKeySet();
  try {
   java.util.List<java.util.concurrent.Callable<Void>> tasks=new java.util.ArrayList<>();
   for(int i=0;i<40;i++)tasks.add(()->{try(Connection lease=DatabaseConfig.getConnection();var st=lease.createStatement();var q=st.executeQuery("SELECT CONNECTION_ID()")){check(q.next()&&lease.getAutoCommit(),"Dirty pooled state");sockets.add(q.getLong(1));}return null;});
   for(var result:executor.invokeAll(tasks))result.get(15,java.util.concurrent.TimeUnit.SECONDS);
   check(sockets.size()<=3,"Too many physical connections");
   System.out.println("PASS actual MySQL pool:40 leases/8 threads/bounded sockets/autoCommit reset");
  }finally{executor.shutdownNow();}
 }

}
