package com.nutrifit.util;

/** Escape untrusted text before placing it in JSP HTML attributes or elements. */
public final class Html {
    private Html() { }
    public static String escape(Object value) {
        if (value == null) return "";
        String s = String.valueOf(value);
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace("\"", "&quot;").replace("'", "&#39;");
    }
}
