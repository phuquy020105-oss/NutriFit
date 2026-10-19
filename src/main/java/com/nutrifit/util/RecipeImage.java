package com.nutrifit.util;

/** Only packaged local recipe assets are accepted; database text cannot inject a URL scheme. */
public final class RecipeImage {
    public static final String FALLBACK = "/assets/images/recipes/placeholder.svg";
    private RecipeImage() { }
    public static String url(String contextPath,String stored) {
        String path=stored!=null && stored.matches("/assets/images/recipes/[a-z0-9-]+\\.(webp|jpg|png|svg)") ? stored : FALLBACK;
        return (contextPath==null?"":contextPath)+path;
    }
}
