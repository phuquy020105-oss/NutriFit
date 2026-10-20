package com.nutrifit.config;
import org.junit.jupiter.api.Test;
import javax.sql.DataSource;
import java.lang.reflect.*;
import java.sql.*;
import java.io.PrintWriter;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;
import java.util.logging.Logger;
import static org.junit.jupiter.api.Assertions.*;

class DatabasePoolTest {
 @Test void concurrentBorrowersAreBoundedReusedAndClosedOnShutdown()throws Exception {
  FakeSource physical=new FakeSource();DatabasePool pool=new DatabasePool(physical);
  try {
   var executor=Executors.newFixedThreadPool(8);
   try {
    List<Callable<Void>> tasks=new ArrayList<>();
    for(int i=0;i<24;i++)tasks.add(()->{try(Connection c=pool.getConnection()){assertTrue(c.isValid(1));Thread.sleep(5);}return null;});
    for(var result:executor.invokeAll(tasks))result.get(10,TimeUnit.SECONDS);
   }finally{executor.shutdownNow();}
   assertTrue(physical.created.get()<=3,"must not open one physical socket per borrower");
   assertTrue(physical.created.get()>0);
  }finally{pool.close();}
  assertEquals(physical.created.get(),physical.closed.get());
  assertThrows(SQLException.class,pool::getConnection);pool.close();
 }
 @Test void errorAndUncommittedTransactionReturnLeaseWithoutSharingDirtyState()throws Exception {
  FakeSource physical=new FakeSource();
  try(DatabasePool pool=new DatabasePool(physical)) {
   assertThrows(IllegalStateException.class,()->{try(Connection c=pool.getConnection()){c.setAutoCommit(false);try(Statement s=c.createStatement()){s.executeUpdate("fixture");}throw new IllegalStateException("service failure");}});
   try(Connection c=pool.getConnection()){assertTrue(c.getAutoCommit());assertFalse(c.isReadOnly());}
   assertEquals(1,physical.rollbacks.get());
   for(int i=0;i<50;i++)try(Connection c=pool.getConnection()){assertTrue(c.getAutoCommit());}
   assertTrue(physical.created.get()<=3);
  }
  assertEquals(physical.created.get(),physical.closed.get());
 }
 @Test void fatalConnectionFailureIsEvictedAndNextBorrowReconnects()throws Exception {
  FakeSource physical=new FakeSource();
  try(DatabasePool pool=new DatabasePool(physical)) {
   try(Connection c=pool.getConnection()) {
    physical.failNext.set(true);
    try(Statement statement=c.createStatement()){assertThrows(SQLException.class,()->statement.executeUpdate("fixture"));}
   }
   try(Connection next=pool.getConnection()){assertTrue(next.isValid(1));}
   assertTrue(physical.closed.get()>=1);assertTrue(physical.created.get()>=2);
  }
  assertEquals(physical.created.get(),physical.closed.get());
 }
 @Test void namedLockLeaseRetiresPhysicalSocketEvenWhenCallerDoesNotReleaseLock()throws Exception {
  FakeSource physical=new FakeSource();
  try(DatabasePool pool=new DatabasePool(physical)) {
   try(Connection c=pool.getConnection();Statement statement=c.createStatement()) {
    assertTrue(c.equals(c));assertSame(c,statement.getConnection());
    statement.execute("SELECT GET_LOCK('local-fixture',0)");
   }
   // Hikari removes the lease immediately and closes the physical socket on its close executor.
   for(int i=0;i<200 && physical.closed.get()==0;i++)Thread.sleep(10);
   assertTrue(physical.closed.get()>=1);
   try(Connection next=pool.getConnection()){assertTrue(next.isValid(1));}
   assertTrue(physical.created.get()>=2);
  }
  assertEquals(physical.created.get(),physical.closed.get());
 }
 @Test void listenerClosesApplicationPoolAndCannotReopenAfterShutdown()throws Exception {
  // Run lifecycle in a child JVM to keep the application-wide shutdown state out of other tests.
  var executable=java.nio.file.Path.of(System.getProperty("java.home"),"bin","java");
  Process p=new ProcessBuilder(executable.toString(),"-cp",System.getProperty("java.class.path"),ShutdownProbe.class.getName()).redirectErrorStream(true).start();
  assertTrue(p.waitFor(15,TimeUnit.SECONDS));assertEquals(0,p.exitValue(),new String(p.getInputStream().readAllBytes()));
 }
 public static final class ShutdownProbe {
  public static void main(String[] args)throws Exception {
   new DatabaseLifecycle().contextDestroyed(null);
   try{DatabaseConfig.getConnection();throw new AssertionError("pool reopened");}catch(SQLException expected){ }
  }
 }
 static final class FakeSource implements DataSource {
  final AtomicInteger created=new AtomicInteger(),closed=new AtomicInteger(),rollbacks=new AtomicInteger();
  final AtomicBoolean failNext=new AtomicBoolean();
  @Override public Connection getConnection() {
   created.incrementAndGet();boolean[] state={true,false,false};
   return (Connection)Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{Connection.class},(p,m,a)->switch(m.getName()){
    case "getAutoCommit"->state[0];case "setAutoCommit"->{state[0]=(boolean)a[0];yield null;}
    case "isReadOnly"->state[1];case "setReadOnly"->{state[1]=(boolean)a[0];yield null;}
    case "close"->{if(!state[2]){state[2]=true;closed.incrementAndGet();}yield null;}
    case "isClosed"->state[2];case "isValid"->!state[2];case "rollback"->{rollbacks.incrementAndGet();yield null;}
    case "getTransactionIsolation"->Connection.TRANSACTION_READ_COMMITTED;case "getNetworkTimeout"->0;
    case "getCatalog","getSchema","getWarnings"->null;
    case "createStatement"->Proxy.newProxyInstance(getClass().getClassLoader(),new Class<?>[]{Statement.class},(sp,sm,sa)->{if(sm.getName().equals("execute"))return true;if(sm.getName().equals("executeUpdate")){if(failNext.getAndSet(false))throw new SQLException("Fixture broken socket","08006");return 1;}return null;});
    case "toString"->"Fixture physical connection";
    case "setNetworkTimeout","setTransactionIsolation","clearWarnings","commit","setCatalog","setSchema"->null;
    default->throw new UnsupportedOperationException(m.getName());
   });
  }
  public Connection getConnection(String u,String p){return getConnection();}public PrintWriter getLogWriter(){return null;}public void setLogWriter(PrintWriter w){}public int getLoginTimeout(){return 0;}public void setLoginTimeout(int s){}public Logger getParentLogger(){return Logger.getGlobal();}public boolean isWrapperFor(Class<?> c){return false;}public <T>T unwrap(Class<T> c)throws SQLException{throw new SQLException();}
 }
}
