package com.nutrifit.util;

public final class HtmlEscaper {
    private HtmlEscaper() {}
    public static String escape(Object value) {
        if (value == null) return "";
        String t = value.toString();
        return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace("\"", "&quot;").replace("'", "&#39;");
    }
}
