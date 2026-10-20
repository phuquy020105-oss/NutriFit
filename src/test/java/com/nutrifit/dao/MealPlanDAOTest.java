package com.nutrifit.dao;

import com.nutrifit.model.MealPlan;
import java.lang.reflect.Proxy;
import java.sql.*;
import java.time.LocalDate;
import java.util.*;
import java.sql.Date;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class MealPlanDAOTest {
    @Test void historyQueryIsReadOnlyCorrelatedAndKeepsOwnerDateAndLimitBound() throws Exception {
        var params=new TreeMap<Integer,Object>();var calls=new ArrayList<String>();
        Connection c=connection(params,calls,List.of());
        assertTrue(new MealPlanDAO().findHistory(c,42,LocalDate.of(2026,10,20),30).isEmpty());
        assertEquals(Map.of(1,42L,2,Date.valueOf("2026-10-20"),3,30),params);
        assertEquals(List.of("prepareStatement","executeQuery","resultClose","statementClose"),calls);
    }
    @Test void returnedDaysRetainStoredIdsOwnerDateAndCreationTime()throws Exception{
        var p=new MealPlan(12L,42L,LocalDate.of(2026,10,18),java.time.LocalDateTime.of(2026,10,18,12,0));
        var q=new MealPlan(11L,42L,LocalDate.of(2026,10,17),java.time.LocalDateTime.of(2026,10,17,12,0));
        var actual=new MealPlanDAO().findHistory(connection(new TreeMap<>(),new ArrayList<>(),List.of(p,q)),42,LocalDate.of(2026,10,20),30);
        assertEquals(List.of(12L,11L),actual.stream().map(MealPlan::getPlanId).toList());
        assertEquals(p.getPlanDate(),actual.getFirst().getPlanDate());assertEquals(p.getCreatedAt(),actual.getFirst().getCreatedAt());
        assertTrue(actual.stream().allMatch(r->r.getUserId()==42));
    }
    static Connection connection(Map<Integer,Object> params,List<String> calls,List<MealPlan> rows){
        return (Connection)Proxy.newProxyInstance(MealPlanDAOTest.class.getClassLoader(),new Class<?>[]{Connection.class},(p,m,a)->{
            assertEquals("prepareStatement",m.getName(),"No transaction, connection close or write is allowed");calls.add("prepareStatement");
            String sql=((String)a[0]).replaceAll("\\s+"," ").trim();
            assertTrue(sql.startsWith("SELECT p.plan_id, p.user_id, p.plan_date, p.created_at FROM mealplans p "));
            assertTrue(sql.contains("p.user_id = ? AND p.plan_date < ?"));
            assertTrue(sql.contains("EXISTS (SELECT 1 FROM mealentries e WHERE e.plan_id = p.plan_id)"));
            assertTrue(sql.endsWith("ORDER BY p.plan_date DESC LIMIT ?"));assertFalse(sql.contains("JOIN"));
            return Proxy.newProxyInstance(MealPlanDAOTest.class.getClassLoader(),new Class<?>[]{PreparedStatement.class},(p2,m2,a2)->switch(m2.getName()){
                case "setLong","setDate","setInt" -> {params.put((Integer)a2[0],a2[1]);yield null;}
                case "executeQuery" -> {
                    calls.add("executeQuery");int[] cursor={-1};
                    yield Proxy.newProxyInstance(MealPlanDAOTest.class.getClassLoader(),new Class<?>[]{ResultSet.class},(p3,m3,a3)->switch(m3.getName()){
                        case "next" -> ++cursor[0]<rows.size();
                        case "getLong" -> a3[0].equals("plan_id")?rows.get(cursor[0]).getPlanId():rows.get(cursor[0]).getUserId();
                        case "getDate" -> Date.valueOf(rows.get(cursor[0]).getPlanDate());
                        case "getTimestamp" -> Timestamp.valueOf(rows.get(cursor[0]).getCreatedAt());
                        case "close" -> {calls.add("resultClose");yield null;}
                        default -> throw new AssertionError(m3.getName());
                    });
                }
                case "close" -> {calls.add("statementClose");yield null;}
                default -> throw new AssertionError(m2.getName());
            });
        });
    }
}
