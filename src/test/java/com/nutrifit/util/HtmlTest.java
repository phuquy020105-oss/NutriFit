package com.nutrifit.util;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class HtmlTest {
    @Test void sharedEscapingPreservesNullQuotesUnicodeAndSingleEncoding() {
        assertEquals("",Html.escape(null));assertEquals("",HtmlEscaper.escape(null));
        assertEquals("&amp;&lt;&gt;&quot;&#39; Quý",Html.escape("&<>\"' Quý"));
        for(Object input:new Object[]{"&<>\"' Quý",42,"&amp;",new StringBuilder("<b>"),""})
            assertEquals(Html.escape(input),HtmlEscaper.escape(input));
    }
}
