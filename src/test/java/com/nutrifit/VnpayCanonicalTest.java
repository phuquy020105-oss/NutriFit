package com.nutrifit;

import com.nutrifit.service.VnpayService;
import org.junit.jupiter.api.Test;
import java.util.LinkedHashMap;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.assertEquals;

/** Pure unit tests: no merchant secret, network or MySQL needed. */
class VnpayCanonicalTest {
    @Test void signsSortedAndEncodedParameters() {
        Map<String, String> params = new LinkedHashMap<>();
        params.put("vnp_TxnRef", "ABC");
        params.put("vnp_OrderInfo", "NutriFit Premium test");
        params.put("vnp_SecureHash", "SHOULD_NOT_BE_SIGNED");
        params.put("unrelated", "ignored");
        assertEquals("vnp_OrderInfo=NutriFit+Premium+test&vnp_TxnRef=ABC",
                VnpayService.canonical(params));
    }

    @Test void skipsNullAndEmptyValues() {
        assertEquals("vnp_TxnRef=1", VnpayService.canonical(Map.of("vnp_TxnRef", "1", "vnp_Command", "")));
    }
}
