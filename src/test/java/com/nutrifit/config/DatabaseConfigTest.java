package com.nutrifit.config;
import java.lang.reflect.*;
import java.sql.SQLException;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class DatabaseConfigTest {
 @Test void customUrlsCannotDisableTlsOrReplaceCredentialsOrTrustStore()throws Exception {
  Method validator=DatabaseConfig.class.getDeclaredMethod("validateUrl",String.class);validator.setAccessible(true);
  for(String suffix:new String[]{"sslMode=DISABLED","sslMode=PREFERRED","useSSL=false","verifyServerCertificate=false","allowPublicKeyRetrieval=true","password=hidden","user=hidden","trustCertificateKeyStoreUrl=file:other","fallbackToSystemTrustStore=true"}) {
   var failure=assertThrows(InvocationTargetException.class,()->validator.invoke(null,"jdbc:mysql://example.invalid:27047/nutrifitdb?"+suffix));
   assertInstanceOf(SQLException.class,failure.getCause());assertFalse(failure.getCause().getMessage().contains("hidden"));
  }
  assertDoesNotThrow(()->validator.invoke(null,"jdbc:mysql://example.invalid:27047/nutrifitdb?sslMode=VERIFY_IDENTITY"));
 }
}
