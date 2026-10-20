package com.nutrifit.util;

/** Compatibility entry point sharing the HTML escaping policy used by all views. */
public final class HtmlEscaper {
    private HtmlEscaper() { }
    public static String escape(Object value) {
        return Html.escape(value);
    }
}
