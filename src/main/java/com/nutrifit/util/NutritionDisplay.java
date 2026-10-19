package com.nutrifit.util;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.util.Locale;

/** Presentation only: round each original value independently, never write the result back. */
public final class NutritionDisplay {
    private NutritionDisplay() { }
    public static String integer(BigDecimal value) {
        if (value==null) return "—";
        DecimalFormatSymbols symbols=DecimalFormatSymbols.getInstance(Locale.forLanguageTag("vi-VN"));
        symbols.setGroupingSeparator('.');
        DecimalFormat format=new DecimalFormat("#,##0",symbols);
        return format.format(value.setScale(0,RoundingMode.HALF_UP));
    }
}
