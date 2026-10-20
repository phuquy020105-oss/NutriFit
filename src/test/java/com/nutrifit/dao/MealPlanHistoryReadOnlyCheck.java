package com.nutrifit.dao;

import java.lang.reflect.Proxy;
import java.nio.file.Path;
import java.sql.Connection;
import java.time.LocalDate;
import java.util.*;

/** Opt-in MySQL SQL-semantic regression. CTEs shadow both real tables; SELECT only, no fixtures written. */
public final class MealPlanHistoryReadOnlyCheck {
    static final LocalDate TODAY=LocalDate.of(2026,10,20);
    static void require(boolean v,String code){if(!v)throw new AssertionError(code);}
    static String fixture(){
        List<String> plans=new ArrayList<>(),entries=new ArrayList<>();
        long[][] first={{1,42,-1},{2,42,-2},{3,42,-3},{4,99,-2},{5,42,0},{6,42,1}};
        for(var r:first)plans.add(row(r[0],r[1],TODAY.plusDays(r[2])));
        for(long id:new long[]{2,3,3,3,4,5,6})entries.add("SELECT "+id+" AS plan_id");
        for(int i=0;i<40;i++){
            plans.add(row(100+i,42,TODAY.minusDays(4+i)));
            if(i%7!=0)entries.add("SELECT "+(100+i)+" AS plan_id");
        }
        return "WITH mealplans AS ("+String.join(" UNION ALL ",plans)+"), mealentries AS ("+String.join(" UNION ALL ",entries)+") ";
    }
    static String row(long id,long user,LocalDate date){
        return "SELECT "+id+" AS plan_id,"+user+" AS user_id,CAST('"+date+"' AS DATE) AS plan_date,CAST('2026-01-01 12:00:00' AS DATETIME) AS created_at";
    }
    static Connection wrapped(Connection real,boolean emulateOld){
        return (Connection)Proxy.newProxyInstance(MealPlanHistoryReadOnlyCheck.class.getClassLoader(),new Class<?>[]{Connection.class},(p,m,a)->{
            require(m.getName().equals("prepareStatement"),"DAO_ATTEMPTED_NON_QUERY_OPERATION");
            String sql=(String)a[0];require(sql.startsWith("SELECT ")&&!sql.contains(";"),"SELECT_ONLY_REQUIRED");
            if(emulateOld)sql=sql.replace("AND EXISTS (SELECT 1 FROM mealentries e WHERE e.plan_id = p.plan_id) ","");
            return real.prepareStatement(fixture()+sql);
        });
    }
    public static void main(String[] args)throws Exception{
        require(args.length==1,"PRIVATE_ENV_PATH_REQUIRED_NO_SECRETS_IN_ARGS");
        // Existing vetted helper enforces exact Aiven host/database/CA/VERIFY_IDENTITY.
        var helper=Class.forName("com.nutrifit.config.FoodQualityReleaseSnapshot");
        try(var real=(Connection)helper.getMethod("openReadOnly",Path.class).invoke(null,Path.of(args[0]))){
            require(real.isReadOnly(),"READ_ONLY_CONNECTION_REQUIRED");real.setAutoCommit(false);
            var c=wrapped(real,false);var dao=new MealPlanDAO();
            var all=dao.findHistory(c,42,TODAY,100);require(all.size()==36,"EMPTY_OR_OTHER_OR_NONPAST_PLAN_INCLUDED");
            require(all.get(0).getPlanId()==2&&all.get(1).getPlanId()==3,"DATE_ORDER_OR_POPULATED_PLAN_MISSING");
            require(all.stream().filter(p->p.getPlanId()==3).count()==1,"MULTIPLE_ENTRIES_DUPLICATE_DATE");
            require(all.stream().allMatch(p->p.getUserId()==42&&p.getPlanDate().isBefore(TODAY)&&p.getPlanId()!=1),"OWNER_DATE_OR_EMPTY_FILTER_FAILED");
            var latest=dao.findHistory(c,42,TODAY,30);require(latest.size()==30,"LIMIT_MUST_APPLY_AFTER_EMPTY_FILTER");
            require(latest.stream().map(p->p.getPlanId()).toList().equals(all.subList(0,30).stream().map(p->p.getPlanId()).toList()),"LATEST30WRONG");
            require(dao.findHistory(c,42,TODAY,1).getFirst().getPlanId()==2,"LIMIT1WRONG");
            var other=dao.findHistory(c,99,TODAY,30);require(other.size()==1&&other.getFirst().getPlanId()==4,"CROSS_USER_LEAK");
            require(dao.findHistory(c,123,TODAY,30).isEmpty(),"UNKNOWN_USER_ROWS");
            require(dao.findHistory(c,42,TODAY.minusDays(2),30).getFirst().getPlanId()==3,"STRICT_BEFORE_BOUNDARY");
            require(dao.findHistory(c,42,LocalDate.of(2020,1,1),30).isEmpty(),"EMPTY_RANGE_FAILED");
            // Negative control proves the regression fixture catches the previous query.
            require(dao.findHistory(wrapped(real,true),42,TODAY,30).getFirst().getPlanId()==1,"NEGATIVE_CONTROL_DID_NOT_REPRODUCE_EMPTY_DAY_BUG");
            real.rollback();System.out.println("PASS MySQL read-only CTE regression:empty/populated/multiple/owner/past/latest30/limit/boundary/old-query-negative-control;0database writes");
        }
    }
}
