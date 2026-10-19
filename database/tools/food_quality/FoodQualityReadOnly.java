package com.nutrifit.config;
import com.nutrifit.util.JsonLite;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.sql.*;
import java.util.*;
public final class FoodQualityReadOnly {
 static final String HOST="nutrifit-mysql-buihaidagggg-d131.g.aivencloud.com";
 static Path ENV;

 static String tlsVersion="",stage="CONFIGURATION";
 static String hash(String s)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8)));}
 static Connection connect()throws Exception{
  var e=loadEnv();if(!HOST.equals(required(e,"AIVEN_DB_HOST"))||!"27047".equals(required(e,"AIVEN_DB_PORT"))||!"nutrifitdb".equals(required(e,"AIVEN_DB_NAME")))throw new IllegalStateException("TARGET_REJECTED");
  var ca=Path.of(required(e,"AIVEN_DB_CA_FILE"));
  if(!HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(ca))).equalsIgnoreCase("624DBC53A7D3DCF8C773EB69A8B181B8EA12ADC9A8967293A51235DB433573D8"))throw new IllegalStateException("CA_REJECTED");
  var p=new Properties();p.setProperty("user",required(e,"AIVEN_DB_USER"));p.setProperty("password",required(e,"AIVEN_DB_PASSWORD"));
  p.setProperty("sslMode","VERIFY_IDENTITY");p.setProperty("allowPublicKeyRetrieval","false");p.setProperty("paranoid","true");p.setProperty("connectTimeout","10000");p.setProperty("socketTimeout","30000");p.setProperty("autoReconnect","false");p.setProperty("characterEncoding","UTF-8");
  DatabaseTrustStore.configure(p,ca.toString());e.clear();stage="AIVEN_CONNECTION";
  var c=DriverManager.getConnection("jdbc:mysql://"+HOST+":27047/nutrifitdb",p);p.remove("password");verifyTarget(c);return c;
 }
 record Snap(String table,List<String> columns,List<List<String>> rows,String ddl){
  String canonical(boolean omitImage){var s=new StringBuilder();for(var row:rows){for(int i=0;i<columns.size();i++){if(omitImage&&columns.get(i).equals("image_url"))continue;s.append(row.get(i)==null?"null":JsonLite.quote(row.get(i))).append('|');}s.append('\n');}return s.toString();}
  String json(){var s=new StringBuilder("{\"table\":"+JsonLite.quote(table)+",\"ddl\":"+JsonLite.quote(ddl)+",\"columns\":[");s.append(String.join(",",columns.stream().map(JsonLite::quote).toList())).append("],\"rows\":[");for(int k=0;k<rows.size();k++){if(k>0)s.append(',');s.append('[').append(String.join(",",rows.get(k).stream().map(v->v==null?"null":JsonLite.quote(v)).toList())).append(']');}return s.append("]}").toString();}
 }
 static Snap snap(Connection c,String table)throws Exception{
  if(!Set.of("foods","recipes","recipeingredients").contains(table))throw new IllegalArgumentException();
  var cols=new ArrayList<String>();var rows=new ArrayList<List<String>>();String ddl;
  try(var s=c.createStatement();var r=s.executeQuery("SHOW CREATE TABLE `"+table+"`")){if(!r.next())throw new IllegalStateException("SCHEMA_MISSING");ddl=r.getString(2);}
  try(var s=c.createStatement();var r=s.executeQuery("SELECT * FROM `"+table+"` ORDER BY 1")){
   var m=r.getMetaData();for(int i=1;i<=m.getColumnCount();i++)cols.add(m.getColumnName(i));
   while(r.next()){var row=new ArrayList<String>();for(int i=1;i<=cols.size();i++)row.add(r.getString(i));rows.add(row);}
  }return new Snap(table,cols,rows,ddl);
 }
 static void schema(Connection c)throws Exception{
  try(var s=c.createStatement();var r=s.executeQuery("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_type='BASE TABLE'")){r.next();if(r.getInt(1)!=24)throw new IllegalStateException("EXPECTED_24_TABLES");}
  try(var s=c.createStatement();var r=s.executeQuery("SELECT data_type,character_maximum_length FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='recipes' AND column_name='image_url'")){if(!r.next()||!"varchar".equals(r.getString(1))||r.getInt(2)!=1000)throw new IllegalStateException("IMAGE_SCHEMA_MISMATCH");}
  try(var s=c.createStatement();var r=s.executeQuery("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name IN ('foods','recipes','recipeingredients') AND engine='InnoDB'")){r.next();if(r.getInt(1)!=3)throw new IllegalStateException("INNODB_REQUIRED");}
 }
 static List<Snap> snapshots(Connection c)throws Exception{return List.of(snap(c,"foods"),snap(c,"recipes"),snap(c,"recipeingredients"));}
 @SuppressWarnings("unchecked")
 public static void main(String[] args){try{
  if(args.length!=3)throw new IllegalArgumentException("ENV_PATH_BACKUP_DIRECTORY_REPORT_PATH_REQUIRED");
  ENV=Path.of(args[0]);Path backup=Path.of(args[1]),reportPath=Path.of(args[2]);
  var baseline=new ArrayList<Snap>();
  for(String table:List.of("foods","recipes","recipeingredients")){
   String text=Files.readString(backup.resolve(table+".json"));
   if(!hash(text).equalsIgnoreCase(Files.readString(backup.resolve(table+".sha256")).strip()))throw new IllegalStateException("BACKUP_CHECKSUM_MISMATCH");
   var json=(Map<String,Object>)JsonLite.parse(text);
   baseline.add(new Snap(table,(List<String>)json.get("columns"),(List<List<String>>)json.get("rows"),(String)json.get("ddl")));
  }
  String sql=Files.readString(backup.resolve("catalog-data-before.sql"));
  if(!hash(sql).equalsIgnoreCase(Files.readString(backup.resolve("catalog-data-before.sha256")).strip()))throw new IllegalStateException("SQL_BACKUP_CHECKSUM_MISMATCH");
  try(var c=connect()){
   c.setReadOnly(true);c.setAutoCommit(false);schema(c);var actual=snapshots(c);
   for(int i=0;i<3;i++)if(!actual.get(i).columns.equals(baseline.get(i).columns)
     ||!actual.get(i).canonical(false).equals(baseline.get(i).canonical(false)))throw new IllegalStateException("CATALOG_DIFFERS_FROM_SAVED_SNAPSHOT");
   int images=0;var recipes=actual.get(1);int col=recipes.columns.indexOf("image_url");
   for(var row:recipes.rows)if(row.get(col)!=null&&!row.get(col).isBlank())images++;
   String report="{\"status\":\"PASS_AIVEN_SELECT_ONLY_UNCHANGED_CATALOG\",\"database\":\"nutrifitdb\",\"tables\":24,\"foods\":"+actual.get(0).rows.size()+
       ",\"recipes\":"+recipes.rows.size()+",\"links\":"+actual.get(2).rows.size()+",\"images\":"+images+
       ",\"tls_mode\":\"VERIFY_IDENTITY\",\"tls_version\":"+JsonLite.quote(tlsVersion)+
       ",\"catalog_matches_checked_backup\":true,\"backup_sha_roundtrip_checked\":true,\"restore_rehearsal_performed\":false,\"persistent_writes\":0}";
   JsonLite.parse(report);c.rollback();Files.createDirectories(reportPath.toAbsolutePath().getParent());Files.writeString(reportPath,report+"\n");
   System.out.println("PASS AIVEN SELECT_ONLY nutrifitdb24tables;"+actual.get(0).rows.size()+"/"+recipes.rows.size()+"/"+actual.get(2).rows.size()+";TLS VERIFY_IDENTITY "+tlsVersion+";catalog unchanged;backup SHA checked;restore NOT rehearsed");
  }
 }catch(Exception e){System.err.println("FAILED stage="+stage+" type="+e.getClass().getSimpleName()+(e instanceof SQLException q?" SQLState="+q.getSQLState()+" code="+q.getErrorCode():e instanceof IllegalStateException?" reason="+e.getMessage():""));System.exit(1);}}
    private static Map<String,String> loadEnv() throws Exception {
        Map<String,String> result = new HashMap<>();
        for (String original : Files.readAllLines(ENV,StandardCharsets.UTF_8)) {
            String line = original.strip();
            if (line.isEmpty() || line.startsWith("#")) continue;
            if (line.startsWith("export ")) line = line.substring(7).stripLeading();
            int equal = line.indexOf('=');
            if (equal < 1) throw new IllegalStateException("ENV_FORMAT_REJECTED");
            String key = line.substring(0,equal).strip();
            String value = line.substring(equal+1).strip();
            if (value.startsWith("\"") || value.startsWith("'")) {
                if (value.length() < 2 || value.charAt(value.length()-1) != value.charAt(0))
                    throw new IllegalStateException("ENV_QUOTES_REJECTED");
                value = value.substring(1,value.length()-1);
            }
            if (result.putIfAbsent(key,value) != null) throw new IllegalStateException("ENV_DUPLICATE_KEY");
        }
        return result;
    }
    private static String required(Map<String,String> env,String key) {
        String value = env.get(key);
        if (value == null || value.isEmpty()) throw new IllegalStateException("REQUIRED_ENV_MISSING");
        return value;
    }
    private static void verifyTarget(Connection c) throws SQLException {
        try (Statement s = c.createStatement(); ResultSet r = s.executeQuery("SELECT DATABASE(),@@version")) {
            if (!r.next() || !"nutrifitdb".equals(r.getString(1)) || !r.getString(2).startsWith("8.4."))
                throw new IllegalStateException("AIVEN_DATABASE_IDENTITY_REJECTED");
        }
        try (Statement s = c.createStatement(); ResultSet r = s.executeQuery("SHOW SESSION STATUS LIKE 'Ssl_version'")) {
            if (!r.next() || !Set.of("TLSv1.2","TLSv1.3").contains(r.getString(2)))
                throw new IllegalStateException("TLS_VERSION_REJECTED");
            tlsVersion = r.getString(2);
        }
        try (Statement s = c.createStatement(); ResultSet r = s.executeQuery("SHOW SESSION STATUS LIKE 'Ssl_cipher'")) {
            if (!r.next() || r.getString(2) == null || r.getString(2).isEmpty())
                throw new IllegalStateException("TLS_CIPHER_MISSING");
        }
    }
}
