package com.nutrifit.service;

import com.nutrifit.config.FoodQualityReleaseSnapshot;
import com.nutrifit.util.JsonLite;
import java.nio.file.*;
import java.math.BigDecimal;
import java.security.MessageDigest;
import java.sql.*;
import java.util.*;
import java.util.regex.*;
import static com.nutrifit.service.LocalFoodQualityTrial.*;

/** Versioned catalog DML. Local trial is opt-in; production requires an approved exact manifest digest. */
public final class CatalogReleaseMigration {
    static boolean productionApproved;
    static final Path RELEASE=STAGING.resolve("release");
    static String digest(Path p)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p)));}
    static void checkedFile(Path p)throws Exception{
        require(Files.isRegularFile(p)&&digest(p).equals(Files.readString(Path.of(p+".sha256")).strip()),"BACKUP_CHECKSUM_REJECTED");
    }
    static List<String> tables(Connection c)throws Exception{
        var out=new ArrayList<String>();try(var s=c.createStatement();var r=s.executeQuery("SELECT table_name FROM information_schema.tables WHERE table_schema=DATABASE() AND table_type='BASE TABLE' ORDER BY table_name")){while(r.next())out.add(r.getString(1));}return out;
    }
    static String protectedHash(Connection c)throws Exception{
        var text=new StringBuilder();
        for(String t:tables(c))if(!Set.of("foods","recipes","recipeingredients").contains(t)){
            require(t.matches("[a-z_]+"),"UNSAFE_TABLE");text.append(t);
            try(var s=c.createStatement();var r=s.executeQuery("SELECT * FROM `"+t+"` ORDER BY 1")){
                int cols=r.getMetaData().getColumnCount();while(r.next()){for(int i=1;i<=cols;i++){String v=r.getString(i);text.append(v==null?"null":JsonLite.quote(v)).append('|');}text.append('\n');}
            }
        }
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(text.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    }
    static void schema(Connection c)throws Exception{
        require(tables(c).size()==24,"EXPECTED24TABLES");
        try(var s=c.createStatement();var r=s.executeQuery("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name IN ('foods','recipes','recipeingredients') AND engine='InnoDB'")){r.next();require(r.getInt(1)==3,"INNODB_REQUIRED");}
        for(String t:List.of("foods","recipes","recipeingredients")){
            try(var s=c.createStatement();var r=s.executeQuery("SHOW CREATE TABLE `"+t+"`")){require(r.next(),"TABLE_MISSING");String ddl=r.getString(2);require(!ddl.contains("TRIGGER"),"UNEXPECTED_TABLE_DEFINITION");}
        }
        try(var s=c.createStatement();var r=s.executeQuery("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table IN ('foods','recipes','recipeingredients')")){r.next();require(r.getInt(1)==0,"CATALOG_TRIGGER_REQUIRES_REVIEW");}
    }
    static void restoreFreshLocal(Connection c,Path backup,boolean resumeEmpty)throws Exception{
        require(db.matches("nutrifit_fq_[a-z0-9_]+_test"),"LOCAL_TEST_NAME_REQUIRED");
        for(String f:List.of("schema.json","foods.json","recipes.json","recipeingredients.json"))checkedFile(backup.resolve(f));
        boolean exists;
        try(var p=c.prepareStatement("SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name=?")){p.setString(1,db);try(var r=p.executeQuery()){r.next();exists=r.getInt(1)!=0;}}
        if(exists){
            require(resumeEmpty,"TEST_DATABASE_EXISTS_STOP_NO_RECREATE");c.setCatalog(db);schema(c);
            for(String t:tables(c)){require(t.matches("[a-z_]+"),"UNSAFE_TABLE");try(var st=c.createStatement();var r=st.executeQuery("SELECT COUNT(*) FROM `"+t+"`")){r.next();require(r.getLong(1)==0,"RESUME_REQUIRES_ALL24TABLES_EMPTY");}}
        }else {
        try(var s=c.createStatement()){s.executeUpdate("CREATE DATABASE `"+db+"` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci");}
        c.setCatalog(db);
        // Aiven SHOW CREATE uses ANSI_QUOTES; keep quoted identifiers as returned, without rewriting DDL.
        try(var st=c.createStatement()){st.execute("SET SESSION sql_mode='ANSI_QUOTES,STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION'");}
        var definitions=new ArrayList<>(rows(read(backup.resolve("schema.json")).get("tables")));
        Set<String> made=new HashSet<>();
        while(!definitions.isEmpty()){
            boolean progress=false;
            for(var it=definitions.iterator();it.hasNext();){var row=it.next();String name=string(row.get("table")),ddl=string(row.get("ddl"));
                require(name.matches("[a-z_]+")&&(ddl.startsWith("CREATE TABLE `"+name+"`")||ddl.startsWith("CREATE TABLE \""+name+"\"")),"UNTRUSTED_BACKUP_DDL");
                Set<String> deps=new HashSet<>();var m=Pattern.compile("REFERENCES [`\"]([a-z_]+)[`\"]").matcher(ddl);while(m.find())deps.add(m.group(1));deps.remove(name);
                if(!made.containsAll(deps))continue;
                try(var s=c.createStatement()){s.executeUpdate(ddl);}made.add(name);it.remove();progress=true;
            }
            require(progress,"DDL_DEPENDENCY_CYCLE_STOP");
        }
        require(made.size()==24,"BACKUP_SCHEMA_COUNT_MISMATCH");
        }
        c.setAutoCommit(false);
        try{
            for(String t:List.of("foods","recipes","recipeingredients")){
                var snapshot=read(backup.resolve(t+".json"));@SuppressWarnings("unchecked")var columns=(List<String>)snapshot.get("columns");
                require(columns.stream().allMatch(n->n.matches("[a-z][a-z0-9_]*")),"UNSAFE_COLUMN");
                String sql="INSERT INTO `"+t+"` (`"+String.join("`,`",columns)+"`) VALUES("+String.join(",",Collections.nCopies(columns.size(),"?"))+")";
                try(var p=c.prepareStatement(sql)){
                    @SuppressWarnings("unchecked") var data=(List<List<String>>)snapshot.get("rows");
                    for(var row:data){for(int i=0;i<columns.size();i++)p.setString(i+1,row.get(i));p.addBatch();}p.executeBatch();
                }
            }
            c.commit();
        }catch(Exception e){c.rollback();throw e;}finally{c.setAutoCommit(true);}
        for(String t:List.of("foods","recipes","recipeingredients"))require(backupRowsMatch(c,t,read(backup.resolve(t+".json"))),"RESTORED_BACKUP_CONTENTS_MISMATCH");
        schema(c);
    }
    static boolean backupRowsMatch(Connection c,String table,Map<String,Object> snapshot)throws Exception{
        require(Set.of("foods","recipes","recipeingredients").contains(table),"BACKUP_TABLE_REJECTED");
        @SuppressWarnings("unchecked")var columns=(List<String>)snapshot.get("columns");
        @SuppressWarnings("unchecked")var expected=(List<List<String>>)snapshot.get("rows");
        var actual=new ArrayList<List<String>>();
        try(var s=c.createStatement();var r=s.executeQuery("SELECT * FROM `"+table+"` ORDER BY 1")){
            require(r.getMetaData().getColumnCount()==columns.size(),"BACKUP_COLUMNS_CHANGED");
            for(int i=0;i<columns.size();i++)require(columns.get(i).equals(r.getMetaData().getColumnName(i+1)),"BACKUP_COLUMN_NAME_CHANGED");
            while(r.next()){var values=new ArrayList<String>();for(int i=1;i<=columns.size();i++)values.add(r.getString(i));actual.add(values);}
        }
        return actual.equals(expected);
    }
    static Counts apply(Connection c,Map<String,Object> desired,Map<String,Object> baseline,boolean initial,int failure)throws Exception{
        require(db.equals(c.getCatalog()) && (db.matches("nutrifit_fq_[a-z0-9_]+_test") || (productionApproved && "nutrifitdb".equals(db))),"APPROVED_TARGET_REQUIRED");
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

    static Map<String,Long> checked(Connection c,Map<String,Object> desired)throws Exception{
        var ids=new HashMap<String,Long>();for(var food:rows(desired.get("foods"))){var actual=foodRow(c,string(food.get("name")));
            require(actual!=null&&sameFood(actual,food),"FINAL_FOOD_MISMATCH");ids.put(string(food.get("ref")),((Number)actual.get("id")).longValue());}
        verify(c,desired,ids);return ids;
    }
    static void verifyManifest(String expected)throws Exception{
        Path file=RELEASE.resolve("final-manifest.json");require(digest(file).equals(expected),"EXACT_APPROVED_MANIFEST_SHA_REQUIRED");
        var manifest=read(file);require(Boolean.TRUE.equals(manifest.get("production_ready")),"PRODUCTION_NOT_READY");
        for(var item:rows(manifest.get("files"))){Path path=Path.of(string(item.get("path"))).toAbsolutePath().normalize();
            require(path.startsWith(Path.of("").toAbsolutePath().normalize())&&digest(path).equals(item.get("sha256")),"RELEASE_FILE_CHECKSUM_MISMATCH");}
    }
    public static void main(String[] args){try{
        require(args.length>=4,"MODE_ENV_DATABASE_OR_BACKUP_ARGUMENTS_REQUIRED");
        String mode=args[0];Path env=Path.of(args[1]);var before=read(RELEASE.resolve("catalog-A-baseline.json"));var after=read(RELEASE.resolve("catalog-C-qualified.json"));
        if("--local-trial".equals(mode)){
            require(args.length==4||(args.length==5&&"--resume-empty-local".equals(args[4])),"LOCAL_TRIAL_ARGS");db=args[2];Path backup=Path.of(args[3]);
            var p=localConfig(env);try(var c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:3306/",p)){
                p.remove("password");stage="LOCAL_RESTORE_REHEARSAL";restoreFreshLocal(c,backup,args.length==5);
                checked(c,before);String restored=fingerprint(c,List.of("foods","recipes","recipeingredients"));
                historicalFixture(c,before);String history=protectedHash(c);var oldIds=recipeIds(c,before);
                // Generated IDs are deliberately moved away from catalog reference numbers.
                try(var s=c.createStatement()){s.executeUpdate("ALTER TABLE foods AUTO_INCREMENT=1001");s.executeUpdate("ALTER TABLE recipes AUTO_INCREMENT=2001");s.executeUpdate("ALTER TABLE recipeingredients AUTO_INCREMENT=3001");}
                stage="RELEASE_ROLLBACK";boolean rollback=false;
                try{apply(c,after,before,false,99);}catch(InjectedFailure expected){rollback=true;}
                require(rollback&&restored.equals(fingerprint(c,List.of("foods","recipes","recipeingredients")))&&history.equals(protectedHash(c)),"ROLLBACK_OR_HISTORY_CHANGED");
                stage="LOCAL_RELEASE_APPLY";var first=apply(c,after,before,false,0);String finalHash=fingerprint(c,List.of("foods","recipes","recipeingredients"));
                var second=apply(c,after,before,false,0);require(second.total()==0&&finalHash.equals(fingerprint(c,List.of("foods","recipes","recipeingredients"))),"IDEMPOTENCY_FAILED");
                require(history.equals(protectedHash(c))&&oldIds.equals(recipeIds(c,before)),"HISTORY_OR_OLD_IDS_CHANGED");
                c.setAutoCommit(false);long id=checked(c,after).get("F001");
                try(var q=c.prepareStatement("UPDATE foods SET calories_per_100g=calories_per_100g+0.001 WHERE food_id=?")){q.setLong(1,id);q.executeUpdate();}
                boolean rejected=false;try{apply(c,after,before,false,0);}catch(IllegalStateException expected){rejected=expected.getMessage().equals("FOOD_VALUE_CONFLICT_STOP");}
                require(rejected&&finalHash.equals(fingerprint(c,List.of("foods","recipes","recipeingredients"))),"CONFLICT_NOT_REJECTED_OR_ROLLED_BACK");
                checked(c,after);schema(c);String report="{\"status\":\"PASS\",\"database\":"+JsonLite.quote(db)+",\"tables\":24,\"foods\":100,\"recipes\":60,\"links\":607,\"restored_backup_rows_exact\":true,\"rollback\":true,\"idempotency_writes\":"+second.total()+",\"conflict_rejected\":true,\"protected_tables_unchanged\":true,\"old_recipe_ids_preserved\":true,\"jdbc_calculator_60\":true,\"first_food_inserts\":"+first.foods()+",\"first_recipe_inserts\":"+first.recipes()+",\"first_link_inserts\":"+first.ingredients()+",\"first_food_updates\":"+first.updatedFoods()+",\"catalog_sha256\":"+JsonLite.quote(digest(RELEASE.resolve("catalog-C-qualified.json")))+",\"backup_manifest_sha256\":"+JsonLite.quote(digest(backup.resolve("backup-manifest.json")))+",\"aiven_writes\":0}";
                JsonLite.parse(report);Files.createDirectories(Path.of("target/food-quality"));Files.writeString(Path.of("target/food-quality/demo-local-trial.json"),report+"\n");
                System.out.println("PASS LOCAL24table backup/restore;100/60/607;injected rollback,idempotency0writes,conflict,history,stableIDs,60JDBCcalculator/images; Aiven writes0");
            }
        } else if("--apply-aiven".equals(mode)){
            require(args.length==5&&"--go-live-approved-manifest".equals(args[3]),"EXPLICIT_GO_LIVE_MANIFEST_APPROVAL_REQUIRED");
            verifyManifest(args[4]);Path backup=Path.of(args[2]);
            for(String f:List.of("schema.json","foods.json","recipes.json","recipeingredients.json"))checkedFile(backup.resolve(f));
            require(digest(backup.resolve("backup-manifest.json")).equals(read(RELEASE.resolve("demo-local-trial.json")).get("backup_manifest_sha256")),"RESTORE_TESTED_BACKUP_REQUIRED");
            db="nutrifitdb";try(var c=FoodQualityReleaseSnapshot.openReadOnly(env)){
                schema(c);c.setAutoCommit(false);
                boolean already=false;try{checked(c,after);already=true;}catch(IllegalStateException expected){/* Baseline path is checked exactly below. */}
                if(already){c.rollback();System.out.println("ALREADY_APPLIED verified100/60/607;0writes");return;}
                for(String t:List.of("foods","recipes","recipeingredients"))require(backupRowsMatch(c,t,read(backup.resolve(t+".json"))),"PRODUCTION_CHANGED_SINCE_BACKUP_STOP");
                checked(c,before);c.rollback();c.setAutoCommit(true);c.setReadOnly(false);productionApproved=true;
                stage="APPROVED_AIVEN_CATALOG_TRANSACTION";
                var result=apply(c,after,before,false,0);System.out.println("COMMITTED catalog release: foods+"+result.foods()+",recipes+"+result.recipes()+",links+"+result.ingredients()+",foodUpdates="+result.updatedFoods());
                // No automatic retry: a failure after commit is reported for read-only review.
            }
        }else throw new IllegalArgumentException("SUPPORTED_MODES_LOCAL_TRIAL_OR_APPROVED_AIVEN_ONLY");
    }catch(Exception e){System.err.println("RELEASE_FAILED stage="+stage+" type="+e.getClass().getSimpleName()+(e instanceof SQLException q?" SQLState="+q.getSQLState()+" code="+q.getErrorCode():e instanceof IllegalStateException?" reason="+e.getMessage():""));System.exit(1);}}
}
