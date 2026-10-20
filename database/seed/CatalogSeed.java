import com.nutrifit.util.JsonLite;
import com.nutrifit.dao.JdbcRecipeReadAdapter;
import com.nutrifit.service.NutritionCalculator;
import java.math.BigDecimal;
import java.nio.file.*;
import java.sql.*;
import java.util.*;

/** Explicit local setup tool. Never invoked by the WAR, Docker build or startup. */
public final class CatalogSeed {
    static final Path ROOT=Path.of("").toAbsolutePath();
    static final List<String> N=List.of("calories_per_100g","protein_per_100g","carbs_per_100g","fat_per_100g","fiber_per_100g");
    static int writes,failAt=-1;
    static String phase="configuration";
    @SuppressWarnings("unchecked") static Map<String,Object> obj(Object v){return (Map<String,Object>)v;}
    @SuppressWarnings("unchecked") static List<Map<String,Object>> rows(Object v){return (List<Map<String,Object>>)v;}
    static void require(boolean ok,String code){if(!ok)throw new IllegalStateException(code);}
    static String env(String k,String fallback){return System.getenv().getOrDefault(k,fallback);}
    static BigDecimal d(Object v){return new BigDecimal(v.toString());}
    static void wrote(){if(++writes==failAt)throw new IllegalStateException("INJECTED_ROLLBACK");}
    static long count(Connection c,String t)throws SQLException{
        require(t.matches("[a-z_]+"),"UNSAFE_TABLE");
        try(var s=c.createStatement();var r=s.executeQuery("SELECT COUNT(*) FROM `"+t+"`")){r.next();return r.getLong(1);}
    }
    static long key(PreparedStatement p)throws SQLException{try(var r=p.getGeneratedKeys()){require(r.next(),"GENERATED_ID_MISSING");return r.getLong(1);}}
    // SQL files are trusted repository setup inputs, not remotely supplied content.
    static int sqlFile(Connection c,Path path)throws Exception{
        int workoutWrites=0;
        String text=Files.readString(path).replaceAll("(?m)^\\s*--[^\\r\\n]*","");
        var part=new StringBuilder();char quote=0;
        for(int i=0;i<text.length();i++){
            char ch=text.charAt(i);
            if(quote!=0){part.append(ch);if(ch=='\\'&&i+1<text.length()){part.append(text.charAt(++i));continue;}if(ch==quote){if(i+1<text.length()&&text.charAt(i+1)==quote)part.append(text.charAt(++i));else quote=0;}}
            else if(ch=='\''||ch=='"'||ch=='`'){quote=ch;part.append(ch);}
            else if(ch==';'){String q=part.toString().strip();part.setLength(0);if(q.isEmpty()||q.startsWith("USE ")||q.startsWith("CREATE DATABASE "))continue;try(var s=c.createStatement()){s.execute(q);if(q.startsWith("INSERT INTO workoutcategories")||q.startsWith("INSERT INTO workouts"))workoutWrites+=Math.max(0,s.getUpdateCount());}}
            else part.append(ch);
        }
        require(quote==0&&part.toString().isBlank(),"INCOMPLETE_SQL_FILE");return workoutWrites;
    }
    static void init(Connection c,String db)throws Exception{
        try(var p=c.prepareStatement("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=?")){p.setString(1,db);try(var r=p.executeQuery()){r.next();require(r.getInt(1)==0,"INIT_REQUIRES_EMPTY_DATABASE_NO_RECREATE");}}
        System.out.println("PASS empty database preflight:"+db+" has0tables");
        try(var s=c.createStatement()){s.executeUpdate("CREATE DATABASE IF NOT EXISTS `"+db+"` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");}
        c.setCatalog(db);sqlFile(c,ROOT.resolve("database/schema.sql"));
        schema(c);require(count(c,"workoutcategories")==0&&count(c,"workouts")==0,"SCHEMA_MUST_NOT_SEED_WORKOUTS");
        System.out.println("PASS schema-only:24tables/0workoutcategories/0workouts");
        require(sqlFile(c,ROOT.resolve("database/seed/workouts.sql"))==50,"FRESH_WORKOUT_SEED_COUNT_MISMATCH");
        sqlFile(c,ROOT.resolve("database/seed/premium-plans.sql"));
    }
    static void schema(Connection c)throws Exception{
        try(var s=c.createStatement();var r=s.executeQuery("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_type='BASE TABLE'")){r.next();require(r.getInt(1)==24,"EXPECTED_24_TABLES");}
        try(var p=c.prepareStatement("SELECT data_type,is_nullable,column_default,column_type FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='users' AND column_name='auth_version'");var r=p.executeQuery()){
            require(r.next()&&"bigint".equals(r.getString(1))&&"NO".equals(r.getString(2))&&"0".equals(r.getString(3))&&!r.getString(4).contains("unsigned")&&!r.next(),"AUTH_VERSION_SCHEMA_MISMATCH");
        }
        try(var p=c.prepareStatement("SELECT k.column_name,k.referenced_table_name,k.referenced_column_name,c.delete_rule FROM information_schema.key_column_usage k JOIN information_schema.referential_constraints c ON c.constraint_schema=k.constraint_schema AND c.table_name=k.table_name AND c.constraint_name=k.constraint_name WHERE k.table_schema=DATABASE() AND k.table_name='password_reset_otps'");var r=p.executeQuery()){
            require(r.next()&&"email".equals(r.getString(1))&&"users".equals(r.getString(2))&&"email".equals(r.getString(3))&&"CASCADE".equals(r.getString(4))&&!r.next(),"RESET_OTP_FOREIGN_KEY_MISMATCH");
        }
        try(var p=c.prepareStatement("SELECT column_name FROM information_schema.key_column_usage WHERE table_schema=DATABASE() AND table_name='password_reset_otps' AND constraint_name='PRIMARY'");var r=p.executeQuery()){
            require(r.next()&&"email".equals(r.getString(1))&&!r.next(),"RESET_OTP_PRIMARY_KEY_MISMATCH");
        }
        try(var s=c.createStatement();var r=s.executeQuery("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name IN ('foods','recipes','recipeingredients') AND engine='InnoDB'")){r.next();require(r.getInt(1)==3,"INNODB_REQUIRED");}
        try(var s=c.createStatement();var r=s.executeQuery("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table IN ('foods','recipes','recipeingredients')")){r.next();require(r.getInt(1)==0,"CATALOG_TRIGGER_REQUIRES_REVIEW");}
    }
    static int apply(Connection c,Map<String,Object> catalog,int inject)throws Exception{
        schema(c);writes=0;failAt=inject;c.setAutoCommit(false);
        try{
            Map<String,Long> foods=new HashMap<>();
            for(var f:rows(catalog.get("foods"))){
                var n=obj(f.get("nutrients"));long id;
                try(var p=c.prepareStatement("SELECT * FROM foods WHERE name=? FOR UPDATE")){
                    p.setString(1,f.get("name").toString());try(var r=p.executeQuery()){
                        if(r.next()){id=r.getLong("food_id");require(f.get("name").equals(r.getString("name"))&&r.getBoolean("active"),"FOOD_NAME_OR_ACTIVE_CONFLICT");for(String k:N)require(d(n.get(k)).compareTo(r.getBigDecimal(k))==0,"FOOD_VALUE_CONFLICT");require(!r.next(),"DUPLICATE_FOOD_NAME");}
                        else{
                            try(var insert=c.prepareStatement("INSERT INTO foods(name,calories_per_100g,protein_per_100g,carbs_per_100g,fat_per_100g,fiber_per_100g,active) VALUES(?,?,?,?,?,?,TRUE)",Statement.RETURN_GENERATED_KEYS)){
                                insert.setString(1,f.get("name").toString());for(int i=0;i<N.size();i++)insert.setBigDecimal(i+2,d(n.get(N.get(i))));require(insert.executeUpdate()==1,"FOOD_INSERT_FAILED");id=key(insert);wrote();
                            }
                        }
                    }
                }foods.put(f.get("ref").toString(),id);
            }
            for(var recipe:rows(catalog.get("recipes"))){
                long id;
                try(var p=c.prepareStatement("SELECT * FROM recipes WHERE name=? FOR UPDATE")){
                    p.setString(1,recipe.get("name").toString());try(var r=p.executeQuery()){
                        if(r.next()){
                            id=r.getLong("recipe_id");for(String k:List.of("name","meal_type","instructions","image_url"))require(Objects.equals(recipe.get(k),r.getString(k)),"RECIPE_VALUE_CONFLICT");
                            require(d(recipe.get("base_servings")).compareTo(r.getBigDecimal("base_servings"))==0&&((Number)recipe.get("prep_minutes")).intValue()==r.getInt("prep_minutes")&&r.getBoolean("active"),"RECIPE_PORTION_OR_ACTIVE_CONFLICT");require(!r.next(),"DUPLICATE_RECIPE_NAME");
                        }else{
                            try(var insert=c.prepareStatement("INSERT INTO recipes(name,meal_type,base_servings,instructions,prep_minutes,image_url,active) VALUES(?,?,?,?,?,?,TRUE)",Statement.RETURN_GENERATED_KEYS)){
                                insert.setString(1,recipe.get("name").toString());insert.setString(2,recipe.get("meal_type").toString());insert.setBigDecimal(3,d(recipe.get("base_servings")));insert.setString(4,recipe.get("instructions").toString());insert.setInt(5,((Number)recipe.get("prep_minutes")).intValue());insert.setString(6,recipe.get("image_url").toString());require(insert.executeUpdate()==1,"RECIPE_INSERT_FAILED");id=key(insert);wrote();
                            }
                        }
                    }
                }
                var expected=new TreeMap<Long,BigDecimal>();for(var i:rows(recipe.get("ingredients")))require(expected.put(foods.get(i.get("food_ref").toString()),d(i.get("quantity_grams")))==null,"DUPLICATE_INGREDIENT");
                var actual=new TreeMap<Long,BigDecimal>();try(var p=c.prepareStatement("SELECT food_id,quantity_grams FROM recipeingredients WHERE recipe_id=? FOR UPDATE")){p.setLong(1,id);try(var r=p.executeQuery()){while(r.next())require(actual.put(r.getLong(1),r.getBigDecimal(2))==null,"DUPLICATE_EXISTING_INGREDIENT");}}
                if(actual.isEmpty()){
                    try(var p=c.prepareStatement("INSERT INTO recipeingredients(recipe_id,food_id,quantity_grams) VALUES(?,?,?)")){
                        for(var i:rows(recipe.get("ingredients"))){p.setLong(1,id);p.setLong(2,foods.get(i.get("food_ref").toString()));p.setBigDecimal(3,d(i.get("quantity_grams")));require(p.executeUpdate()==1,"INGREDIENT_INSERT_FAILED");wrote();}
                    }
                }else{require(expected.keySet().equals(actual.keySet()),"INGREDIENT_SET_CONFLICT");for(long f:expected.keySet())require(expected.get(f).compareTo(actual.get(f))==0,"INGREDIENT_GRAMS_CONFLICT");}
            }
            verify(c,catalog);c.commit();return writes;
        }catch(Exception e){c.rollback();throw e;}finally{c.setAutoCommit(true);failAt=-1;}
    }
    static List<String> workoutSnapshot(Connection c)throws SQLException{
        var result=new ArrayList<String>();
        for(String table:List.of("workoutcategories","workouts")){
            result.add(table);try(var s=c.createStatement();var r=s.executeQuery("SELECT * FROM `"+table+"` ORDER BY 1")){
                int columns=r.getMetaData().getColumnCount();while(r.next())for(int i=1;i<=columns;i++)result.add(r.getString(i));
            }
        }return result;
    }
    static void verify(Connection c,Map<String,Object> catalog)throws Exception{
        schema(c);require(count(c,"workoutcategories")==3&&count(c,"workouts")==47&&count(c,"subscriptionplans")==2,"SAMPLE_WORKOUT_OR_PLANS_MISSING");
        try(var s=c.createStatement();var r=s.executeQuery("SELECT COUNT(*) FROM workouts w LEFT JOIN workoutcategories c ON c.category_id=w.category_id WHERE c.category_id IS NULL")){r.next();require(r.getInt(1)==0,"ORPHAN_WORKOUT");}
        require(count(c,"foods")==100&&count(c,"recipes")==60&&count(c,"recipeingredients")==607,"CATALOG_COUNTS_MISMATCH");
        Map<String,Long> foodIds=new HashMap<>();
        for(var f:rows(catalog.get("foods"))){
            try(var p=c.prepareStatement("SELECT * FROM foods WHERE name=?")){p.setString(1,f.get("name").toString());try(var r=p.executeQuery()){
                require(r.next()&&f.get("name").equals(r.getString("name"))&&r.getBoolean("active"),"FOOD_VERIFY_MISSING");foodIds.put(f.get("ref").toString(),r.getLong("food_id"));
                for(String key:N)require(d(obj(f.get("nutrients")).get(key)).compareTo(r.getBigDecimal(key))==0,"FOOD_VERIFY_VALUE");require(!r.next(),"FOOD_VERIFY_DUPLICATE");
            }}
        }
        for(var recipe:rows(catalog.get("recipes"))){
            long id;try(var p=c.prepareStatement("SELECT * FROM recipes WHERE name=?")){p.setString(1,recipe.get("name").toString());try(var r=p.executeQuery()){
                require(r.next()&&r.getBoolean("active"),"RECIPE_VERIFY_MISSING");id=r.getLong("recipe_id");
                for(String key:List.of("name","meal_type","instructions","image_url"))require(Objects.equals(recipe.get(key),r.getString(key)),"RECIPE_VERIFY_VALUE");
                require(d(recipe.get("base_servings")).compareTo(r.getBigDecimal("base_servings"))==0&&((Number)recipe.get("prep_minutes")).intValue()==r.getInt("prep_minutes"),"RECIPE_VERIFY_PORTION");require(!r.next(),"RECIPE_VERIFY_DUPLICATE");
            }}
            var expected=new TreeMap<Long,BigDecimal>();for(var i:rows(recipe.get("ingredients")))require(expected.put(foodIds.get(i.get("food_ref").toString()),d(i.get("quantity_grams")))==null,"DUPLICATE_INGREDIENT");
            var actual=new TreeMap<Long,BigDecimal>();try(var p=c.prepareStatement("SELECT food_id,quantity_grams FROM recipeingredients WHERE recipe_id=?")){p.setLong(1,id);try(var r=p.executeQuery()){while(r.next())require(actual.put(r.getLong(1),r.getBigDecimal(2))==null,"DUPLICATE_EXISTING_INGREDIENT");}}
            require(expected.keySet().equals(actual.keySet()),"INGREDIENT_VERIFY_SET");for(long f:expected.keySet())require(expected.get(f).compareTo(actual.get(f))==0,"INGREDIENT_VERIFY_GRAMS");
        }
        var adapter=new JdbcRecipeReadAdapter();var calculator=new NutritionCalculator();
        var candidates=adapter.listCandidates(c);require(candidates.size()==60,"CALCULATOR_REJECTED_RECIPE");
        for(var type:com.nutrifit.model.MealEntry.MealType.values())require(candidates.stream().filter(r->r.mealType()==type).count()==20,"MEAL_DISTRIBUTION_MISMATCH");
        Map<String,Map<String,Object>> byName=new HashMap<>();for(var r:rows(catalog.get("recipes")))byName.put(r.get("name").toString(),r);
        for(var r:candidates){var input=adapter.findNutritionInput(c,r.recipeId()).orElseThrow();require(input.ingredients().size()==rows(byName.get(r.name()).get("ingredients")).size(),"RECIPE_LINK_COUNT_MISMATCH");require(input.baseServings().compareTo(BigDecimal.ONE)==0&&input.imageUrl().equals(byName.get(r.name()).get("image_url")),"RECIPE_IMAGE_OR_PORTION_MISMATCH");calculator.calculate(input,BigDecimal.ONE);require(Files.isRegularFile(ROOT.resolve("src/main/webapp"+input.imageUrl())),"MISSING_IMAGE");}
        try(var s=c.createStatement();var r=s.executeQuery("SELECT COUNT(*) FROM recipeingredients i LEFT JOIN recipes r ON r.recipe_id=i.recipe_id LEFT JOIN foods f ON f.food_id=i.food_id WHERE r.recipe_id IS NULL OR f.food_id IS NULL")){r.next();require(r.getInt(1)==0,"ORPHAN_INGREDIENT");}
    }
    public static void main(String[] args){
        try{
            require(args.length==1&&Set.of("init","seed","verify","test","check").contains(args[0]),"ACTION_REQUIRED_INIT_SEED_VERIFY_TEST");
            String action=args[0],host=env("LOCAL_DB_HOST","127.0.0.1"),db=env("LOCAL_DB_NAME","nutrifitdb_java"),port=env("LOCAL_DB_PORT","3306");
            require(Set.of("127.0.0.1","localhost").contains(host)&&port.matches("[0-9]{1,5}")&&Integer.parseInt(port)>0&&Integer.parseInt(port)<=65535,"LOOPBACK_LOCAL_ONLY");
            require(db.equals("nutrifitdb_java")||db.matches("nutrifit_[a-z0-9_]+_test"),"LOCAL_DATABASE_NAME_REQUIRED");
            if(Set.of("test","check").contains(action))require(db.matches("nutrifit_[a-z0-9_]+_test"),"TEST_DATABASE_SUFFIX_REQUIRED");
            Properties props=new Properties();props.setProperty("user",env("LOCAL_DB_USER",env("NUTRIFIT_DB_USER","root")));props.setProperty("password",env("LOCAL_DB_PASSWORD",env("NUTRIFIT_DB_PASSWORD","")));props.setProperty("paranoid","true");
            String url="jdbc:mysql://"+host+":"+port+"/?useUnicode=true&characterEncoding=UTF-8&connectTimeout=10000";
            var catalog=obj(JsonLite.parse(Files.readString(ROOT.resolve("database/seed/catalog.json"))));
            try(var c=DriverManager.getConnection(url,props)){
                try(var p=c.prepareStatement("SELECT GET_LOCK(SHA2(?,256),0)")){p.setString(1,"nutrifit-local-seed:"+db);try(var result=p.executeQuery()){require(result.next()&&result.getInt(1)==1,"ANOTHER_SETUP_IS_RUNNING");}}
                phase="schema-init";if(Set.of("init","test").contains(action))init(c,db);else c.setCatalog(db);
                if(action.equals("test")){
                    phase="rollback-test";try{apply(c,catalog,20);throw new IllegalStateException("ROLLBACK_INJECTION_NOT_TRIGGERED");}catch(IllegalStateException e){require(e.getMessage().equals("INJECTED_ROLLBACK"),"UNEXPECTED_TEST_FAILURE");}
                    require(count(c,"foods")==0&&count(c,"recipes")==0&&count(c,"recipeingredients")==0,"ROLLBACK_LEFT_DATA");System.out.println("PASS injected failure after20writes rolled back all catalog rows");
                }
                phase="catalog-seed";if(!Set.of("verify","check").contains(action)){int changed=apply(c,catalog,-1);System.out.println("COMMIT catalog writes="+changed);phase="idempotency";require(apply(c,catalog,-1)==0,"IDEMPOTENCY_FAILED");}
                phase="read-only-verify";verify(c,catalog);
                if(Set.of("test","check").contains(action)){
                    require(count(c,"users")==0&&count(c,"mealentries")==0,"TEST_DATA_ONLY_REQUIRED");
                    phase="workout-seed-idempotency-test";var workoutBefore=workoutSnapshot(c);
                    require(sqlFile(c,ROOT.resolve("database/seed/workouts.sql"))==0,"WORKOUT_SEED_DUPLICATED_ROWS");
                    require(workoutBefore.equals(workoutSnapshot(c)),"WORKOUT_SEED_CHANGED_CONTENTS_OR_IDS");
                    System.out.println("PASS Workout seed rerun:0persistent writes,all columns and IDs unchanged");
                    phase="repeatable-idempotency-test";require(apply(c,catalog,-1)==0,"IDEMPOTENCY_FAILED");System.out.println("PASS idempotency:0writes");
                    phase="repeatable-rollback-test";
                    var trial=obj(JsonLite.parse(Files.readString(ROOT.resolve("database/seed/catalog.json"))));
                    String prefix="__rollback_test_"+UUID.randomUUID()+":";for(var food:rows(trial.get("foods")))food.put("name",prefix+food.get("name"));
                    try{apply(c,trial,20);throw new IllegalStateException("ROLLBACK_INJECTION_NOT_TRIGGERED");}catch(IllegalStateException e){require(e.getMessage().equals("INJECTED_ROLLBACK"),"UNEXPECTED_ROLLBACK_TEST_FAILURE");}
                    verify(c,catalog);System.out.println("PASS injected20writes rollback; canonical catalog unchanged");
                    phase="conflict-test";c.setAutoCommit(false);try(var s=c.createStatement()){s.executeUpdate("UPDATE foods SET protein_per_100g=protein_per_100g+0.001 ORDER BY food_id LIMIT 1");
                        // A separate connection is unnecessary: detect the conflicting row without committing.
                        var changed=obj(JsonLite.parse(Files.readString(ROOT.resolve("database/seed/catalog.json"))));
                        try{apply(c,changed,-1);throw new IllegalStateException("CONFLICT_NOT_REJECTED");}catch(IllegalStateException e){require(e.getMessage().equals("FOOD_VALUE_CONFLICT"),"UNEXPECTED_CONFLICT_FAILURE");}
                    }finally{if(!c.getAutoCommit()){c.rollback();c.setAutoCommit(true);}}verify(c,catalog);
                    System.out.println("PASS conflict rejection and rollback; original catalog preserved");
                    for(String t:List.of("users","userprofiles","mealplans","mealentries","foodpreferences","paymenttransactions","chatconversations","chatmessages"))require(count(c,t)==0,"UNEXPECTED_PRIVATE_DATA");
                    require(count(c,"workoutcategories")==3&&count(c,"workouts")==47&&count(c,"subscriptionplans")==2,"SAMPLE_WORKOUT_OR_PLANS_MISSING");
                }
                System.out.println("PASS "+db+":24tables/100foods/60recipes/607ingredients/20permeal/60images; action="+action+"; no production access");
            }
        }catch(SQLException e){System.err.println("FAILED phase="+phase+" SQL state="+e.getSQLState()+" code="+e.getErrorCode()+"; no automatic retry; connection details redacted");for(var frame:e.getStackTrace())if(frame.getClassName().equals("CatalogSeed"))System.err.println("  "+frame.getMethodName()+":"+frame.getLineNumber());System.exit(1);}
        catch(Exception e){String code=e.getMessage();System.err.println("FAILED "+(code!=null&&code.matches("[A-Z0-9_]+")?code:e.getClass().getSimpleName()));System.exit(1);}
    }
}
