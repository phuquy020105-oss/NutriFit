package com.nutrifit.service;

import com.nutrifit.dao.JdbcRecipeReadAdapter;
import com.nutrifit.dto.*;
import com.nutrifit.model.MealEntry;
import com.nutrifit.util.JsonLite;
import java.math.BigDecimal;
import java.nio.file.*;
import java.security.MessageDigest;
import java.sql.*;
import java.util.*;
import java.util.regex.*;

/** Opt-in LOCAL trial: fresh test DB for writes, existing test DB only for explicit read-only verification. */
public final class LocalFoodQualityTrial {
    static final Path STAGING=Path.of("database/staging/food-quality-v1");
    static final List<String> N=List.of("calories_per_100g","protein_per_100g","carbs_per_100g","fat_per_100g","fiber_per_100g");
    static final Set<String> TABLES=Set.of("users","foods","recipes","recipeingredients","mealplans","mealentries");
    static String stage="CONFIGURATION";
    static String db;
    static int writes, failAt;
    record Counts(int foods,int recipes,int ingredients,int updatedFoods) {
        int total(){return foods+recipes+ingredients+updatedFoods;}
    }
    static final class InjectedFailure extends RuntimeException { }
    static void require(boolean condition,String code){if(!condition)throw new IllegalStateException(code);}
    static void wrote(){if(++writes==failAt)throw new InjectedFailure();}
    @SuppressWarnings("unchecked") static Map<String,Object> obj(Object o){return (Map<String,Object>)o;}
    @SuppressWarnings("unchecked") static List<Map<String,Object>> rows(Object o){return (List<Map<String,Object>>)o;}
    static Map<String,Object> read(Path p)throws Exception{return obj(JsonLite.parse(Files.readString(p)));}
    static String string(Object o){return o==null?null:o.toString();}
    static BigDecimal decimal(Object o){return new BigDecimal(string(o));}
    static NutritionFacts facts(Map<String,Object> food){
        var n=obj(food.get("nutrients"));return new NutritionFacts(decimal(n.get(N.get(0))),decimal(n.get(N.get(1))),
                decimal(n.get(N.get(2))),decimal(n.get(N.get(3))),decimal(n.get(N.get(4))));
    }
    static long key(PreparedStatement p)throws Exception{
        try(var r=p.getGeneratedKeys()){require(r.next(),"GENERATED_ID_MISSING");return r.getLong(1);}
    }
    static int count(Connection c,String table)throws Exception{
        require(TABLES.contains(table),"TABLE_REJECTED");
        try(var s=c.createStatement();var r=s.executeQuery("SELECT COUNT(*) FROM `"+table+"`")){r.next();return r.getInt(1);}
    }
    static String fingerprint(Connection c,List<String> tables)throws Exception{
        var text=new StringBuilder();
        for(String table:tables){require(TABLES.contains(table),"TABLE_REJECTED");text.append(table);
            try(var s=c.createStatement();var r=s.executeQuery("SELECT * FROM `"+table+"` ORDER BY 1")){
                int n=r.getMetaData().getColumnCount();while(r.next())for(int i=1;i<=n;i++){
                    String value=r.getString(i);text.append(value==null?"null":JsonLite.quote(value)).append('|');
                }
            }
        }
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(text.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }
    static Properties localConfig(Path envFile)throws Exception{
        Map<String,String> env=new HashMap<>();
        for(String raw:Files.readAllLines(envFile)){
            String line=raw.strip();if(line.startsWith("\ufeff"))line=line.substring(1);
            if(line.isBlank()||line.startsWith("#"))continue;
            if(line.startsWith("export "))line=line.substring(7).stripLeading();
            int equal=line.indexOf('=');require(equal>0,"ENV_FORMAT_REJECTED");
            String key=line.substring(0,equal).strip();if(!key.startsWith("LOCAL_DB_"))continue;
            String value=line.substring(equal+1).strip();
            if(value.startsWith("\"")||value.startsWith("'")){
                require(value.length()>1&&value.charAt(value.length()-1)==value.charAt(0),"ENV_QUOTES_REJECTED");
                value=value.substring(1,value.length()-1);
            }
            require(env.putIfAbsent(key,value)==null,"ENV_DUPLICATE_KEY");
        }
        require(Set.of("127.0.0.1","localhost").contains(env.get("LOCAL_DB_HOST"))&&"3306".equals(env.get("LOCAL_DB_PORT")),"ONLY_LOOPBACK_3306_ALLOWED");
        require(env.get("LOCAL_DB_USER")!=null&&env.get("LOCAL_DB_PASSWORD")!=null,"LOCAL_CREDENTIALS_MISSING");
        var p=new Properties();p.setProperty("user",env.get("LOCAL_DB_USER"));p.setProperty("password",env.get("LOCAL_DB_PASSWORD"));
        // Local-only encrypted connection; Aiven/VERIFY_IDENTITY configuration is never loaded or changed.
        p.setProperty("sslMode","REQUIRED");p.setProperty("paranoid","true");p.setProperty("characterEncoding","UTF-8");
        p.setProperty("connectTimeout","5000");p.setProperty("socketTimeout","30000");p.setProperty("autoReconnect","false");
        env.clear();return p;
    }
    static void createFreshSchema(Connection c)throws Exception{
        try(var p=c.prepareStatement("SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name=?")){
            p.setString(1,db);try(var r=p.executeQuery()){r.next();require(r.getInt(1)==0,"DATABASE_ALREADY_EXISTS_STOP");}
        }
        try(var s=c.createStatement()){
            s.executeUpdate("CREATE DATABASE `"+db+"` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");
        }
        c.setCatalog(db);require(db.equals(c.getCatalog()),"WRONG_DATABASE");
        var matcher=Pattern.compile("CREATE TABLE IF NOT EXISTS (\\w+) \\(.*?ENGINE=InnoDB;",Pattern.DOTALL)
                .matcher(Files.readString(Path.of("database/schema.sql")));
        Set<String> created=new HashSet<>();
        while(matcher.find())if(TABLES.contains(matcher.group(1))){
            try(var s=c.createStatement()){s.executeUpdate(matcher.group().replace("IF NOT EXISTS ",""));}
            created.add(matcher.group(1));
        }
        require(created.equals(TABLES),"EXPECTED_SIX_TRIAL_TABLES");
        try(var s=c.createStatement()){
            s.executeUpdate("ALTER TABLE foods AUTO_INCREMENT=1001");
            s.executeUpdate("ALTER TABLE recipes AUTO_INCREMENT=2001");
            s.executeUpdate("ALTER TABLE recipeingredients AUTO_INCREMENT=3001");
        }
    }
    static Map<String,Object> foodRow(Connection c,String name)throws Exception{
        try(var p=c.prepareStatement("SELECT * FROM foods WHERE CAST(name AS BINARY)=CAST(? AS BINARY)"+(c.isReadOnly()?"":" FOR UPDATE"))){
            p.setString(1,name);try(var r=p.executeQuery()){
                if(!r.next())return null;var out=new HashMap<String,Object>();out.put("id",r.getLong("food_id"));
                out.put("active",r.getBoolean("active"));for(String n:N)out.put(n,r.getBigDecimal(n));
                require(!r.next(),"DUPLICATE_FOOD_NAME");return out;
            }
        }
    }
    static boolean sameFood(Map<String,Object> actual,Map<String,Object> desired){
        if(!Boolean.TRUE.equals(actual.get("active")))return false;
        var nutrients=obj(desired.get("nutrients"));
        return N.stream().allMatch(n->decimal(actual.get(n)).compareTo(decimal(nutrients.get(n)))==0);
    }
    static Map<String,Long> recipeIds(Connection c,Map<String,Object> catalog)throws Exception{
        var map=new LinkedHashMap<String,Long>();
        for(var recipe:rows(catalog.get("recipes")))try(var p=c.prepareStatement("SELECT recipe_id FROM recipes WHERE CAST(name AS BINARY)=CAST(? AS BINARY) AND meal_type=?")){
            p.setString(1,string(recipe.get("name")));p.setString(2,string(recipe.get("meal_type")));
            try(var r=p.executeQuery()){require(r.next(),"RECIPE_MAPPING_MISSING");map.put(string(recipe.get("ref")),r.getLong(1));require(!r.next(),"DUPLICATE_RECIPE_NAME");}
        }
        return map;
    }
    static Counts apply(Connection c,Map<String,Object> desired,Map<String,Object> baseline,boolean initial,int failure)throws Exception{
        require(db.equals(c.getCatalog())&&db.matches("nutrifit_fq_[a-z0-9_]+_test"),"TEST_TARGET_REQUIRED");
        writes=0;failAt=failure;c.setAutoCommit(false);
        int insertedFoods=0,insertedRecipes=0,insertedIngredients=0,updatedFoods=0;
        try{
            Map<String,Map<String,Object>> old=new HashMap<>();
            for(var f:rows(baseline.get("foods")))old.put(string(f.get("ref")),f);
            var ids=new HashMap<String,Long>();
            for(var food:rows(desired.get("foods"))){
                String ref=string(food.get("ref"));var actual=foodRow(c,string(food.get("name")));long id;
                if(actual==null){
                    require(initial||!old.containsKey(ref),"ORIGINAL_FOOD_MISSING");
                    try(var p=c.prepareStatement("INSERT INTO foods(name,calories_per_100g,protein_per_100g,carbs_per_100g,fat_per_100g,fiber_per_100g,active) VALUES(?,?,?,?,?,?,TRUE)",Statement.RETURN_GENERATED_KEYS)){
                        p.setString(1,string(food.get("name")));var nutrients=obj(food.get("nutrients"));
                        for(int i=0;i<5;i++)p.setBigDecimal(i+2,decimal(nutrients.get(N.get(i))));
                        require(p.executeUpdate()==1,"FOOD_INSERT_FAILED");id=key(p);insertedFoods++;wrote();
                    }
                }else{
                    id=((Number)actual.get("id")).longValue();
                    if(!sameFood(actual,food)){
                        require(old.containsKey(ref)&&sameFood(actual,old.get(ref)),"FOOD_VALUE_CONFLICT_STOP");
                        try(var p=c.prepareStatement("UPDATE foods SET calories_per_100g=?,protein_per_100g=?,carbs_per_100g=?,fat_per_100g=?,fiber_per_100g=? WHERE food_id=?")){
                            var nutrients=obj(food.get("nutrients"));for(int i=0;i<5;i++)p.setBigDecimal(i+1,decimal(nutrients.get(N.get(i))));
                            p.setLong(6,id);require(p.executeUpdate()==1,"FOOD_UPDATE_FAILED");updatedFoods++;wrote();
                        }
                    }
                }
                ids.put(ref,id);
            }
            for(var recipe:rows(desired.get("recipes"))){
                long id=0;boolean added=false;
                try(var p=c.prepareStatement("SELECT * FROM recipes WHERE CAST(name AS BINARY)=CAST(? AS BINARY) AND meal_type=? FOR UPDATE")){
                    p.setString(1,string(recipe.get("name")));p.setString(2,string(recipe.get("meal_type")));
                    try(var r=p.executeQuery()){if(r.next()){
                        id=r.getLong("recipe_id");
                        require(r.getBoolean("active")&&r.getBigDecimal("base_servings").compareTo(decimal(recipe.get("base_servings")))==0
                                &&Objects.equals(r.getString("instructions"),recipe.get("instructions"))&&Objects.equals(r.getString("image_url"),recipe.get("image_url"))
                                &&r.getInt("prep_minutes")==((Number)recipe.get("prep_minutes")).intValue(),"RECIPE_VALUE_CONFLICT_STOP");
                        require(!r.next(),"DUPLICATE_RECIPE_NAME");
                    }}
                }
                if(id==0){
                    require(initial||Integer.parseInt(string(recipe.get("ref")).substring(1))>30,"ORIGINAL_RECIPE_MISSING");
                    try(var p=c.prepareStatement("INSERT INTO recipes(name,meal_type,base_servings,instructions,image_url,prep_minutes,active) VALUES(?,?,?,?,?,?,TRUE)",Statement.RETURN_GENERATED_KEYS)){
                        p.setString(1,string(recipe.get("name")));p.setString(2,string(recipe.get("meal_type")));p.setBigDecimal(3,decimal(recipe.get("base_servings")));
                        p.setString(4,string(recipe.get("instructions")));p.setString(5,string(recipe.get("image_url")));p.setInt(6,((Number)recipe.get("prep_minutes")).intValue());
                        require(p.executeUpdate()==1,"RECIPE_INSERT_FAILED");id=key(p);added=true;insertedRecipes++;wrote();
                    }
                }
                var expected=new HashMap<Long,BigDecimal>();for(var i:rows(recipe.get("ingredients")))
                    require(expected.put(ids.get(string(i.get("food_ref"))),decimal(i.get("quantity_grams")))==null,"DUPLICATE_DESIGN_INGREDIENT");
                var actual=new HashMap<Long,BigDecimal>();
                try(var p=c.prepareStatement("SELECT food_id,quantity_grams FROM recipeingredients WHERE recipe_id=? FOR UPDATE")){
                    p.setLong(1,id);try(var r=p.executeQuery()){while(r.next())require(actual.put(r.getLong(1),r.getBigDecimal(2))==null,"DUPLICATE_STORED_INGREDIENT");}
                }
                if(added){
                    for(var i:expected.entrySet())try(var p=c.prepareStatement("INSERT INTO recipeingredients(recipe_id,food_id,quantity_grams) VALUES(?,?,?)")){
                        p.setLong(1,id);p.setLong(2,i.getKey());p.setBigDecimal(3,i.getValue());require(p.executeUpdate()==1,"INGREDIENT_INSERT_FAILED");insertedIngredients++;wrote();
                    }
                }else{
                    require(actual.keySet().equals(expected.keySet())&&expected.entrySet().stream()
                            .allMatch(e->actual.get(e.getKey()).compareTo(e.getValue())==0),"INGREDIENT_VALUE_CONFLICT_STOP");
                }
            }
            verify(c,desired,ids);c.commit();return new Counts(insertedFoods,insertedRecipes,insertedIngredients,updatedFoods);
        }catch(Exception e){c.rollback();throw e;}finally{c.setAutoCommit(true);}
    }
    static void verify(Connection c,Map<String,Object> catalog,Map<String,Long> ids)throws Exception{
        var foods=rows(catalog.get("foods"));var recipes=rows(catalog.get("recipes"));
        require(count(c,"foods")==foods.size()&&count(c,"recipes")==recipes.size()
                &&count(c,"recipeingredients")==recipes.stream().mapToInt(r->rows(r.get("ingredients")).size()).sum(),"CATALOG_COUNTS_MISMATCH");
        try(var s=c.createStatement();var r=s.executeQuery("SELECT COUNT(*) FROM recipeingredients i LEFT JOIN foods f ON f.food_id=i.food_id LEFT JOIN recipes r ON r.recipe_id=i.recipe_id WHERE f.food_id IS NULL OR r.recipe_id IS NULL")){
            r.next();require(r.getInt(1)==0,"BROKEN_FK");
        }
        var adapter=new JdbcRecipeReadAdapter();require(adapter.listCandidates(c).size()==recipes.size(),"JDBC_ADAPTER_REJECTED_RECIPE");
        var byRef=new HashMap<String,Map<String,Object>>();for(var f:foods)byRef.put(string(f.get("ref")),f);
        var actualRecipes=recipeIds(c,catalog);
        for(var recipe:recipes){
            var lines=new ArrayList<IngredientNutritionLine>();for(var i:rows(recipe.get("ingredients")))
                lines.add(new IngredientNutritionLine(ids.get(string(i.get("food_ref"))),decimal(i.get("quantity_grams")),facts(byRef.get(string(i.get("food_ref"))))));
            long id=actualRecipes.get(string(recipe.get("ref")));
            var expected=new RecipeNutritionInput(id,string(recipe.get("name")),MealEntry.MealType.valueOf(string(recipe.get("meal_type"))),decimal(recipe.get("base_servings")),lines);
            try(var p=c.prepareStatement("SELECT instructions,image_url,prep_minutes,active FROM recipes WHERE recipe_id=?")){
                p.setLong(1,id);try(var r=p.executeQuery()){
                    require(r.next()&&r.getBoolean("active")&&Objects.equals(r.getString("instructions"),recipe.get("instructions"))
                        &&Objects.equals(r.getString("image_url"),recipe.get("image_url"))
                        &&r.getInt("prep_minutes")==((Number)recipe.get("prep_minutes")).intValue(),"RECIPE_METADATA_MISMATCH");
                }
            }
            var read=adapter.findNutritionInput(c,id).orElseThrow();var calculator=new NutritionCalculator();
            require(calculator.calculate(expected,BigDecimal.ONE).equals(calculator.calculate(read,BigDecimal.ONE)),"NUTRITION_CALCULATOR_DB_MISMATCH");
        }
    }
    static void historicalFixture(Connection c,Map<String,Object> baseline)throws Exception{
        c.setAutoCommit(false);
        try{
            long user,plan;
            try(var p=c.prepareStatement("INSERT INTO users(email,password_hash,full_name,role,subscription_status) VALUES(?,?,?,'USER','FREE')",Statement.RETURN_GENERATED_KEYS)){
                p.setString(1,"food-quality-fixture@example.invalid");p.setString(2,"DISABLED_TEST_FIXTURE_NO_LOGIN");p.setString(3,"Disposable Nutrition fixture");p.executeUpdate();user=key(p);
            }
            try(var p=c.prepareStatement("INSERT INTO mealplans(user_id,plan_date) VALUES(?,?)",Statement.RETURN_GENERATED_KEYS)){
                p.setLong(1,user);p.setDate(2,java.sql.Date.valueOf("2026-10-18"));p.executeUpdate();plan=key(p);
            }
            long recipe=recipeIds(c,baseline).get("R003");var input=new JdbcRecipeReadAdapter().findNutritionInput(c,recipe).orElseThrow();
            var nutrition=new NutritionCalculator().calculate(input,new BigDecimal("1.32"));
            try(var p=c.prepareStatement("INSERT INTO mealentries(plan_id,recipe_id,recipe_name_snapshot,meal_type,servings,calories_kcal,protein_g,carbs_g,fat_g,fiber_g) VALUES(?,?,?,'BREAKFAST',?,?,?,?,?,?)")){
                p.setLong(1,plan);p.setLong(2,recipe);p.setString(3,input.name());p.setBigDecimal(4,new BigDecimal("1.32"));
                var n=List.of(nutrition.caloriesKcal(),nutrition.proteinG(),nutrition.carbsG(),nutrition.fatG(),nutrition.fiberG());for(int i=0;i<5;i++)p.setBigDecimal(i+5,n.get(i));p.executeUpdate();
            }
            c.commit();
        }catch(Exception e){c.rollback();throw e;}finally{c.setAutoCommit(true);}
    }
    public static void main(String[] args){try{
        boolean verifyOnly=args.length==3&&"--verify-existing".equals(args[2]);
        require(args.length==2||verifyOnly,"ARGUMENTS_ENV_FILE_AND_LOCAL_TEST_DB");db=args[1];
        require(db.length()<=64&&db.matches("nutrifit_fq_[a-z0-9_]+_test"),"TEST_DATABASE_NAME_REJECTED");
        var baseline=read(Path.of("database/seed/vietnamese_catalog.json"));var expanded=read(STAGING.resolve("catalog-C-exploratory.json"));
        require(Boolean.FALSE.equals(obj(expanded.get("quality_gate")).get("production_write_permitted")),"TRIAL_ONLY_CATALOG_REQUIRED");
        var gate=obj(expanded.get("quality_gate"));
        require(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(Path.of("database/seed/vietnamese_catalog.json"))))
                .equals(gate.get("baseline_sha256")),"BASELINE_SHA_MISMATCH");
        require(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(STAGING.resolve("food-provenance.json"))))
                .equals(gate.get("provenance_sha256")),"PROVENANCE_SHA_MISMATCH");
        var imageMap=new HashMap<String,String>();for(var image:rows(read(Path.of("docs/nutrition/recipe-image-sources.json")).get("images")))imageMap.put(string(image.get("ref")),string(image.get("image_url")));
        for(var recipe:rows(baseline.get("recipes")))recipe.put("image_url",imageMap.get(string(recipe.get("ref"))));
        var properties=localConfig(Path.of(args[0]));stage="LOCAL_CONNECTION";
        try(var c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:3306/",properties)){
            properties.remove("password");
            if(verifyOnly){
                stage="READ_ONLY_EXISTING_LOCAL_TEST_DATABASE";c.setCatalog(db);c.setReadOnly(true);c.setAutoCommit(false);
                var ids=new HashMap<String,Long>();
                for(var food:rows(expanded.get("foods"))){
                    var actual=foodRow(c,string(food.get("name")));
                    require(actual!=null&&sameFood(actual,food),"READ_ONLY_FOOD_MISMATCH");
                    ids.put(string(food.get("ref")),((Number)actual.get("id")).longValue());
                }
                verify(c,expanded,ids);
                require(count(c,"users")==1&&count(c,"mealplans")==1&&count(c,"mealentries")==1,"TRIAL_FIXTURE_COUNT_MISMATCH");
                String version=c.getMetaData().getDatabaseProductVersion();
                String report="{\"status\":\"PASS_READ_ONLY_LOCAL_CATALOG_VERIFICATION\",\"database\":"+JsonLite.quote(db)
                    +",\"mysql_version\":"+JsonLite.quote(version)+",\"catalog_sha256\":"
                    +JsonLite.quote(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(STAGING.resolve("catalog-C-exploratory.json")))))
                    +",\"foods\":100,\"recipes\":60,\"links\":607,\"read_only\":true}";
                JsonLite.parse(report);c.rollback();Path out=Path.of("target/food-quality");Files.createDirectories(out);
                Files.writeString(out.resolve("local-trial-readonly.json"),report+"\n");
                System.out.println("PASS READ_ONLY_LOCAL_VERIFY:100foods/60recipes/607links;exact nutrients/recipe metadata/JDBC-calculator;MySQL "+version);
                return;
            }
            stage="CREATE_NEW_LOCAL_TEST_SCHEMA";createFreshSchema(c);
            System.out.println("LOCAL_TEST_DATABASE_CREATED "+db+" six schema-derived tables; existing databases untouched");
            stage="BASELINE_FIXTURE";apply(c,baseline,baseline,true,0);historicalFixture(c,baseline);
            var catalogs=List.of("foods","recipes","recipeingredients");var protectedTables=List.of("users","mealplans","mealentries");
            String before=fingerprint(c,catalogs),history=fingerprint(c,protectedTables);
            stage="INJECTED_ROLLBACK_TRIAL";boolean rolledBack=false;
            try{apply(c,expanded,baseline,false,99);}catch(InjectedFailure expected){rolledBack=true;}
            require(rolledBack&&before.equals(fingerprint(c,catalogs))&&history.equals(fingerprint(c,protectedTables)),"ROLLBACK_INVARIANT_FAILED");
            stage="APPLY_EXPLORATORY_CATALOG";var first=apply(c,expanded,baseline,false,0);String after=fingerprint(c,catalogs);
            stage="IDEMPOTENCY_TRIAL";var second=apply(c,expanded,baseline,false,0);
            require(second.total()==0&&after.equals(fingerprint(c,catalogs))&&history.equals(fingerprint(c,protectedTables)),"IDEMPOTENCY_OR_HISTORY_FAILED");
            stage="CONFLICT_TRIAL";c.setAutoCommit(false);
            long conflictFoodId=((Number)foodRow(c,string(rows(baseline.get("foods")).getFirst().get("name"))).get("id")).longValue();
            try(var p=c.prepareStatement("UPDATE foods SET calories_per_100g=calories_per_100g+0.001 WHERE food_id=?")){
                p.setLong(1,conflictFoodId);require(p.executeUpdate()==1,"CONFLICT_FIXTURE_UPDATE_FAILED");
            }
            boolean conflict=false;try{apply(c,expanded,baseline,false,0);}catch(IllegalStateException e){conflict="FOOD_VALUE_CONFLICT_STOP".equals(e.getMessage());}
            require(conflict&&after.equals(fingerprint(c,catalogs))&&history.equals(fingerprint(c,protectedTables)),"CONFLICT_REJECTION_FAILED");
            String report="{\"status\":\"PASS_LOCAL_MECHANICS_ONLY_NOT_DATA_APPROVAL\",\"database\":"+JsonLite.quote(db)+
                ",\"tables\":6,\"foods\":100,\"recipes\":60,\"links\":607,\"original_recipe_ids_shifted\":true,\"rollback_trial\":true,\"conflict_rejected\":true,\"history_unchanged\":true,"+
                "\"second_run_new_foods\":0,\"second_run_new_recipes\":0,\"second_run_new_links\":0,\"second_run_updates\":0,"+
                "\"first_run_new_foods\":"+first.foods()+",\"first_run_new_recipes\":"+first.recipes()+",\"first_run_new_links\":"+first.ingredients()+",\"first_run_updated_foods\":"+first.updatedFoods()+"}";
            JsonLite.parse(report);Path out=Path.of("target/food-quality");Files.createDirectories(out);Files.writeString(out.resolve("local-trial-result.json"),report+"\n");
            System.out.println("PASS LOCAL ONLY:100foods/60recipes/607links;rollback/conflict/idempotency/history/JDBC-calculator verified; NOT production approval");
        }
    }catch(Exception e){System.err.println("FAILED stage="+stage+" type="+e.getClass().getSimpleName()+
        (e instanceof SQLException q?" SQLState="+q.getSQLState()+" code="+q.getErrorCode():e instanceof IllegalStateException?" reason="+e.getMessage():""));System.exit(1);}}
}
