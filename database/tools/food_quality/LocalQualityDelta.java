package com.nutrifit.service;

import com.nutrifit.dao.JdbcRecipeReadAdapter;
import com.nutrifit.util.JsonLite;
import com.nutrifit.util.RecipeImage;
import java.nio.file.*;
import java.security.MessageDigest;
import java.sql.*;
import java.util.*;
import static com.nutrifit.service.LocalFoodQualityTrial.*;

/** Existing LOCAL staging only. No schema/seed/recreation or Aiven configuration path. */
public final class LocalQualityDelta {
    static final Path BEFORE=STAGING.resolve("catalog-C-checkpoint-f04b2da.json");
    static final Path AFTER=STAGING.resolve("catalog-C-exploratory.json");
    static final String EXPECTED_BEFORE_SHA="afdaad645524f15c334e7c0f6dfcb5dc4b1335b06dbdc2adc1b332e702f9ad20";
    static String digest(Path p)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p)));}
    static Map<String,Long> checked(Connection c,Map<String,Object> catalog)throws Exception{
        var ids=new HashMap<String,Long>();
        for(var food:rows(catalog.get("foods"))){
            var actual=foodRow(c,string(food.get("name")));
            require(actual!=null&&sameFood(actual,food),"CATALOG_BEFORE_OR_AFTER_CONFLICT");
            ids.put(string(food.get("ref")),((Number)actual.get("id")).longValue());
        }
        verify(c,catalog,ids);return ids;
    }
    static boolean matches(Connection c,Map<String,Object> catalog)throws Exception{
        try{checked(c,catalog);return true;}catch(IllegalStateException e){return false;}
    }
    static void imageMappingRollback(Connection c,Map<String,Object> catalog,String expectedHash)throws Exception{
        var jobs=rows(read(STAGING.resolve("image-generation-jobs.json")).get("recipes"));
        var byRef=new HashMap<String,String>();
        for(var job:jobs){
            require("VISUALLY_REVIEWED_STAGING_ILLUSTRATION".equals(job.get("status")),"IMAGE_NOT_REVIEWED");
            var file=Path.of(string(job.get("staging_path"))).toAbsolutePath().normalize();
            require(file.startsWith(STAGING.resolve("images").toAbsolutePath().normalize())&&digest(file).equals(job.get("sha256")),"IMAGE_HASH_OR_PATH_REJECTED");
            byRef.put(string(job.get("recipe_ref")),string(job.get("filename")));
        }
        require(byRef.size()==30,"THIRTY_IMAGE_MAPPINGS_REQUIRED");
        var recipes=recipeIds(c,catalog);c.setAutoCommit(false);
        try{
            for(var e:byRef.entrySet()){
                String url="/assets/images/recipes/"+e.getValue();
                require(RecipeImage.url("/nutrifit",url).equals("/nutrifit"+url),"UNSAFE_IMAGE_URL");
                try(var p=c.prepareStatement("UPDATE recipes SET image_url=? WHERE recipe_id=? AND image_url IS NULL")){
                    p.setString(1,url);p.setLong(2,recipes.get(e.getKey()));require(p.executeUpdate()==1,"STAGING_IMAGE_CONFLICT");
                }
                require(url.equals(new JdbcRecipeReadAdapter().findNutritionInput(c,recipes.get(e.getKey())).orElseThrow().imageUrl()),"JDBC_IMAGE_MAPPING_MISMATCH");
            }
        }finally{c.rollback();c.setAutoCommit(true);}
        require(expectedHash.equals(fingerprint(c,List.of("foods","recipes","recipeingredients"))),"IMAGE_TRIAL_NOT_ROLLED_BACK");
    }
    public static void main(String[] args){try{
        boolean apply=args.length==3&&"--apply-local-delta".equals(args[2]);
        require(args.length==2||apply,"ARGS_ENV_AND_EXISTING_TEST_DB_OPTIONAL_APPLY_LOCAL_DELTA");
        db=args[1];require("nutrifit_fq_20261019_food_quality_test".equals(db),"EXACT_EXISTING_STAGING_TARGET_REQUIRED");
        require(digest(BEFORE).equals(EXPECTED_BEFORE_SHA),"CHECKPOINT_C_SHA_MISMATCH");
        Path beforePath=BEFORE;var before=read(BEFORE);var after=read(AFTER);var gate=obj(after.get("quality_gate"));
        require(Boolean.FALSE.equals(gate.get("production_write_permitted")),"EXPLORATORY_LOCAL_ONLY");
        require(digest(STAGING.resolve("food-provenance.json")).equals(gate.get("provenance_sha256")),"CURRENT_SOURCE_SHA_MISMATCH");
        require(rows(before.get("foods")).size()==100&&rows(after.get("foods")).size()==100,"DELTA_FOOD_COUNTS");
        require(rows(before.get("recipes")).equals(rows(after.get("recipes"))),"DELTA_MUST_NOT_CHANGE_RECIPE_METADATA_OR_GRAMS");
        var p=localConfig(Path.of(args[0]));stage="CONNECT_EXISTING_LOCAL_STAGING";
        try(var c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:3306/",p)){
            p.remove("password");c.setCatalog(db);c.setReadOnly(true);c.setAutoCommit(false);
            boolean isBefore=matches(c,before),isAfter=matches(c,after);
            if(!isBefore&&!isAfter){
                Path intermediate=STAGING.resolve("catalog-C-checkpoint-69-sources.json");
                require(digest(intermediate).equals("5523b9647bad68435b0f6ccbd07791d99915397ee108f71a962751e61ec7ad02"),"INTERMEDIATE_C_SHA_MISMATCH");
                before=read(intermediate);beforePath=intermediate;isBefore=matches(c,before);
                require(rows(before.get("recipes")).equals(rows(after.get("recipes"))),"INTERMEDIATE_RECIPE_CONFLICT");
            }
            require(isBefore||isAfter,"EXISTING_STAGING_UNEXPECTED_STATE_STOP");
            String version=c.getMetaData().getDatabaseProductVersion();
            String history=fingerprint(c,List.of("users","mealplans","mealentries"));
            String initial=fingerprint(c,List.of("foods","recipes","recipeingredients"));
            c.rollback();c.setAutoCommit(true);
            if(!apply){System.out.println("PASS SELECT_ONLY existing staging="+(isAfter?"CURRENT_C":"CHECKPOINT_C")+";100/60/607;MySQL "+version);return;}
            c.setReadOnly(false);stage="LOCAL_DELTA_ROLLBACK_AND_IDEMPOTENCY";
            Counts first=new Counts(0,0,0,0);boolean rollbackVerified=false;
            if(!isAfter){
                try{apply(c,after,before,false,1);throw new IllegalStateException("EXPECTED_INJECTED_FAILURE");}
                catch(InjectedFailure expected){rollbackVerified=true;}
                require(initial.equals(fingerprint(c,List.of("foods","recipes","recipeingredients")))&&history.equals(fingerprint(c,List.of("users","mealplans","mealentries"))),"DELTA_ROLLBACK_FAILED");
                first=apply(c,after,before,false,0);
            }
            String finalHash=fingerprint(c,List.of("foods","recipes","recipeingredients"));
            Counts second=apply(c,after,before,false,0);require(second.total()==0,"DELTA_IDEMPOTENCY_FAILED");
            c.setAutoCommit(false);
            long id=((Number)foodRow(c,string(rows(after.get("foods")).getFirst().get("name"))).get("id")).longValue();
            try(var q=c.prepareStatement("UPDATE foods SET calories_per_100g=calories_per_100g+0.001 WHERE food_id=?")){q.setLong(1,id);require(q.executeUpdate()==1,"CONFLICT_FIXTURE_FAILED");}
            boolean conflict=false;
            try{apply(c,after,before,false,0);}catch(IllegalStateException expected){conflict="FOOD_VALUE_CONFLICT_STOP".equals(expected.getMessage());}
            require(conflict&&finalHash.equals(fingerprint(c,List.of("foods","recipes","recipeingredients"))),"DELTA_CONFLICT_ROLLBACK_FAILED");
            imageMappingRollback(c,after,finalHash);checked(c,after);
            require(history.equals(fingerprint(c,List.of("users","mealplans","mealentries"))),"HISTORY_CHANGED_STOP");
            String report="{\"status\":\"PASS_EXISTING_LOCAL_STAGING_DELTA\",\"database\":"+JsonLite.quote(db)+
                ",\"mysql_version\":"+JsonLite.quote(version)+",\"before_sha256\":"+JsonLite.quote(digest(beforePath))+",\"after_sha256\":"+JsonLite.quote(digest(AFTER))+
                ",\"inserted_foods\":"+first.foods()+",\"inserted_recipes\":"+first.recipes()+",\"inserted_links\":"+first.ingredients()+",\"updated_foods\":"+first.updatedFoods()+
                ",\"injected_delta_rollback_tested_this_run\":"+rollbackVerified+",\"second_run_writes\":"+second.total()+
                ",\"conflict_rejected\":true,\"history_unchanged\":true,\"image_mappings_30_trial_rolled_back\":true,\"active_new_image_urls\":0,\"schema_recreated\":false,\"aiven_contacted\":false}";
            JsonLite.parse(report);Path out=Path.of("target/food-quality");Files.createDirectories(out);Files.writeString(out.resolve("local-delta-result.json"),report+"\n");
            System.out.println("PASS LOCAL DELTA updates="+first.updatedFoods()+";secondWrites="+second.total()+";rollback/conflict/history/30imageMappings/JDBC verified;no Aiven");
        }
    }catch(Exception e){System.err.println("FAILED stage="+stage+" type="+e.getClass().getSimpleName()+
        (e instanceof SQLException q?" SQLState="+q.getSQLState()+" code="+q.getErrorCode():e instanceof IllegalStateException?" reason="+e.getMessage():""));System.exit(1);}}
}
