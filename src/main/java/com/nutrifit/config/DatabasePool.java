package com.nutrifit.config;
import com.zaxxer.hikari.*;
import javax.sql.DataSource;
import java.sql.*;
import java.lang.reflect.*;
import java.util.regex.Pattern;

/** One pool per webapp classloader. Close returns leases; shutdown closes physical sockets. */
final class DatabasePool implements AutoCloseable {
    private final HikariDataSource source;
    DatabasePool(DataSource physical) {
        HikariConfig config=new HikariConfig();
        config.setPoolName("NutriFit");config.setDataSource(physical);
        config.setMaximumPoolSize(3);config.setMinimumIdle(1);
        config.setConnectionTimeout(10_000);config.setValidationTimeout(3_000);
        config.setMaxLifetime(240_000);config.setKeepaliveTime(60_000);config.setIdleTimeout(120_000);
        config.setInitializationFailTimeout(-1);config.setIsolateInternalQueries(true);
        source=new HikariDataSource(config);
    }
    private static final Pattern NAMED_LOCK = Pattern.compile("(?i)GET_LOCK");
    Connection getConnection() throws SQLException {
        Connection lease = source.getConnection();
        boolean[] namedLock = {false}, closed = {false};
        return (Connection) Proxy.newProxyInstance(DatabasePool.class.getClassLoader(), new Class<?>[]{Connection.class}, (proxy,method,args) -> {
            if (method.getName().equals("equals")) return proxy == args[0];
            if (method.getName().equals("hashCode")) return System.identityHashCode(proxy);
            if (method.getName().equals("close")) {
                if (!closed[0]) {
                    closed[0] = true;
                    // Named locks survive rollback. OTP leases retain physical-close semantics,
                    // including when RELEASE_LOCK itself fails with a non-fatal SQL state.
                    try { if (namedLock[0]) source.evictConnection(lease); }
                    finally { lease.close(); }
                }
                return null;
            }
            if (args != null && args.length > 0 && args[0] instanceof String sql
                    && method.getName().startsWith("prepare") && NAMED_LOCK.matcher(sql).find()) namedLock[0] = true;
            Object result = invoke(lease, method, args);
            if (result instanceof Statement statement) {
                Class<?> type = result instanceof CallableStatement ? CallableStatement.class
                        : result instanceof PreparedStatement ? PreparedStatement.class : Statement.class;
                return Proxy.newProxyInstance(DatabasePool.class.getClassLoader(), new Class<?>[]{type}, (p,m,a) -> {
                    if (m.getName().equals("equals")) return p == a[0];
                    if (m.getName().equals("hashCode")) return System.identityHashCode(p);
                    if (m.getName().equals("getConnection")) return proxy;
                    if (m.getName().startsWith("execute") && a != null && a.length > 0 && a[0] instanceof String sql
                            && NAMED_LOCK.matcher(sql).find()) namedLock[0] = true;
                    return invoke(statement,m,a);
                });
            }
            return result;
        });
    }
    private static Object invoke(Object target,Method method,Object[] args)throws Throwable {
        try{return method.invoke(target,args);}catch(InvocationTargetException error){throw error.getCause();}
    }
    @Override public void close() { source.close(); }
}
