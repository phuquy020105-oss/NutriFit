package com.nutrifit.config;

import com.nutrifit.util.JsonLite;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.sql.*;
import java.util.*;

/** Aiven SELECT/SHOW only. Private catalog backup plus full DDL, never user rows. */
public final class FoodQualityReleaseSnapshot {
    public static Connection openReadOnly(Path env) throws Exception {
        FoodQualityReadOnly.ENV=env;
        Connection c=FoodQualityReadOnly.connect();c.setReadOnly(true);return c;
    }
    static String sha(Path p)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p)));}
    static String stage="CONFIGURATION";
    public static void main(String[] args){try{
        if(args.length!=2)throw new IllegalArgumentException("ENV_AND_NEW_PRIVATE_BACKUP_DIRECTORY_REQUIRED");
        Path out=Path.of(args[1]).toAbsolutePath().normalize();
        if(!out.startsWith(Path.of("D:/NutriFit-backups"))||Files.exists(out))throw new IllegalStateException("NEW_PRIVATE_BACKUP_DIRECTORY_REQUIRED");
        stage="READ_ONLY_AIVEN_BACKUP";
        try(var c=openReadOnly(Path.of(args[0]))){
            c.setAutoCommit(false);FoodQualityReadOnly.schema(c);
            List<String> tables=new ArrayList<>();
            try(var s=c.createStatement();var r=s.executeQuery("SELECT table_name FROM information_schema.tables WHERE table_schema=DATABASE() AND table_type='BASE TABLE' ORDER BY table_name")){while(r.next())tables.add(r.getString(1));}
            if(tables.size()!=24)throw new IllegalStateException("EXPECTED24TABLES");
            List<String> ddl=new ArrayList<>();
            for(String table:tables){if(!table.matches("[a-z_]+"))throw new IllegalStateException("UNSAFE_TABLE");
                try(var s=c.createStatement();var r=s.executeQuery("SHOW CREATE TABLE `"+table+"`")){if(!r.next())throw new IllegalStateException("SCHEMA_MISSING");ddl.add("{\"table\":"+JsonLite.quote(table)+",\"ddl\":"+JsonLite.quote(r.getString(2))+"}");}}
            var snapshots=FoodQualityReadOnly.snapshots(c);c.rollback();
            if(snapshots.get(0).rows().size()!=82||snapshots.get(1).rows().size()!=30||snapshots.get(2).rows().size()!=383)
                throw new IllegalStateException("PRODUCTION_BASELINE_COUNTS_CHANGED");
            stage="WRITE_PRIVATE_BACKUP_FILES";
            Files.createDirectories(out.getParent());
            Files.createDirectory(out);
            Files.writeString(out.resolve("schema.json"),"{\"tables\":["+String.join(",",ddl)+"]}\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
            for(var snap:snapshots)Files.writeString(out.resolve(snap.table()+".json"),snap.json()+"\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
            List<String> files=new ArrayList<>();
            for(String file:List.of("schema.json","foods.json","recipes.json","recipeingredients.json")){
                String digest=sha(out.resolve(file));Files.writeString(out.resolve(file+".sha256"),digest+"\n",StandardOpenOption.CREATE_NEW);
                files.add(JsonLite.quote(file)+":"+JsonLite.quote(digest));
            }
            Files.writeString(out.resolve("backup-manifest.json"),"{\"database\":\"nutrifitdb\",\"tables_schema\":24,\"catalog_only_data\":true,\"tls\":\"VERIFY_IDENTITY\",\"persistent_database_writes\":0,\"files\":{"+String.join(",",files)+"}}\n",StandardOpenOption.CREATE_NEW);
            System.out.println("PASS AIVEN READ_ONLY: private catalog82/30/383 +24tableDDL backup created; no user rows exported; no database writes");
        }
    }catch(Exception e){System.err.println("SNAPSHOT_FAILED stage="+stage+" type="+e.getClass().getSimpleName()+(e instanceof SQLException q?" SQLState="+q.getSQLState()+" code="+q.getErrorCode():e instanceof IllegalStateException?" "+e.getMessage():""));System.exit(1);}}
}
