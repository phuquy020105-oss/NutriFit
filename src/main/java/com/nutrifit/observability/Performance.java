package com.nutrifit.observability;

import java.lang.reflect.*;
import java.sql.*;
import java.util.*;

/** Request-local opt-in timings. Never retain SQL text, parameters or identity. */
public final class Performance {
    private static final ThreadLocal<Sample> CURRENT = new ThreadLocal<>();
    private Performance() { }
    public static final class Sample {
        private final long start = System.nanoTime();
        private long acquisition, sql, view, recommendation, swap;
        private int connections, queries;
        private final Map<String, Long> groups = new TreeMap<>();
        public String summary(String route, int status) {
            return "perf route=" + route(route) + " status=" + status + " request_us=" + us(System.nanoTime()-start)
                    + " connections=" + connections + " acquire_us=" + us(acquisition) + " queries=" + queries
                    + " sql_us=" + us(sql) + " view_us=" + us(view)
                    + " recommend_us=" + us(recommendation) + " swap_us=" + us(swap)
                    + " remaining_us=" + us(Math.max(0,System.nanoTime()-start-acquisition-sql-view))
                    + " sql_groups_us=" + groups;
        }
    }
    public static Sample begin() { Sample s=new Sample(); CURRENT.set(s); return s; }
    public static void end() { CURRENT.remove(); }
    public static boolean active() { return CURRENT.get()!=null; }
    private static long us(long nanos) { return nanos/1000; }
    public static String route(String path) {
        if (path==null) return "other";
        if (path.startsWith("/assets/")) return "/assets/*";
        return switch(path) {
            case "/dashboard", "/nutrition/recommendations", "/nutrition/meal-planner", "/nutrition/history",
                 "/nutrition/preferences", "/workout", "/workout/plan", "/profile", "/onboarding",
                 "/chatbot", "/payment", "/payment/return", "/payment/ipn", "/api/features",
                 "/login", "/logout", "/register", "/health", "/admin" -> path;
            default -> "other";
        };
    }
    public static Scope scope(String group) { return new Scope(CURRENT.get(),group); }
    public static final class Scope implements AutoCloseable {
        private final Sample sample; private final String group; private final long start=System.nanoTime();
        Scope(Sample sample,String group) { this.sample=sample;this.group=group; }
        @Override public void close() {
            if(sample==null)return;
            long elapsed=System.nanoTime()-start;
            switch(group) {
                case "view" -> sample.view+=elapsed;
                case "recommend" -> sample.recommendation+=elapsed;
                case "swap" -> sample.swap+=elapsed;
                default -> { }
            }
        }
    }
    public static void acquired(long start) {
        Sample s=CURRENT.get(); if(s!=null){s.connections++;s.acquisition+=System.nanoTime()-start;}
    }
    public static Connection instrument(Connection connection) {
        if(!active())return connection;
        return (Connection) Proxy.newProxyInstance(Performance.class.getClassLoader(),new Class<?>[]{Connection.class},(p,m,a)->{
            if(m.getName().equals("equals"))return p==a[0];
            if(m.getName().equals("hashCode"))return System.identityHashCode(p);
            Object result=invoke(connection,m,a);
            if(result instanceof Statement statement) {
                String group=a!=null && a.length>0 && a[0] instanceof String text ? group(text):"other";
                Class<?> type=result instanceof CallableStatement?CallableStatement.class:
                        result instanceof PreparedStatement?PreparedStatement.class:Statement.class;
                return Proxy.newProxyInstance(Performance.class.getClassLoader(),new Class<?>[]{type},(sp,sm,sa)->{
                    if(sm.getName().equals("equals"))return sp==sa[0];
                    if(sm.getName().equals("hashCode"))return System.identityHashCode(sp);
                    if(sm.getName().equals("getConnection"))return p;
                    if(!sm.getName().startsWith("execute"))return invoke(statement,sm,sa);
                    long start=System.nanoTime();
                    try{return invoke(statement,sm,sa);}
                    finally {
                        Sample s=CURRENT.get();
                        if(s!=null){long elapsed=System.nanoTime()-start;s.queries++;s.sql+=elapsed;
                            s.groups.merge(group,us(elapsed),Long::sum);}
                    }
                });
            }
            return result;
        });
    }
    private static Object invoke(Object target,Method m,Object[] args)throws Throwable {
        try{return m.invoke(target,args);}catch(InvocationTargetException e){throw e.getCause();}
    }
    private static String group(String sql) {
        String text=sql.toLowerCase(Locale.ROOT);
        if(text.contains("recipe")||text.contains("foods"))return "catalog";
        if(text.contains("meal"))return "journal";
        if(text.contains("workout"))return "workout";
        if(text.contains("userprofiles"))return "profile";
        if(text.contains("users"))return "user";
        if(text.contains("payment")||text.contains("subscription"))return "payment";
        return "other";
    }
}
