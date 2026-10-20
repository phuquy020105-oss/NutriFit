package com.nutrifit.service;

import com.nutrifit.util.JsonLite;
import com.nutrifit.util.RecipeImage;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class RecipeImageAssetsTest {
    @Test @SuppressWarnings("unchecked") void everyCurrentRecipeHasUniquePackagedVerifiedWebpAndCatalogMapping()throws Exception{
        var catalog=(Map<String,Object>)JsonLite.parse(Files.readString(Path.of("database/seed/catalog.json")));
        var source=(Map<String,Object>)JsonLite.parse(Files.readString(Path.of("database/seed/provenance.json")));
        var recipes=(List<Map<String,Object>>)catalog.get("recipes");var images=(List<Map<String,Object>>)source.get("images");
        assertEquals(recipes.size(),images.size());assertEquals(60,images.size());
        Set<String> urls=new HashSet<>(),digests=new HashSet<>();
        for(var recipe:recipes){
            var matches=images.stream().filter(i->i.get("recipe_ref").equals(recipe.get("ref"))).toList();assertEquals(1,matches.size());var image=matches.getFirst();
            String url=(String)recipe.get("image_url");assertEquals(url,RecipeImage.url("",url));assertTrue(urls.add(url));
            Path path=Path.of("src/main/webapp"+url);byte[] bytes=Files.readAllBytes(path);
            assertTrue(bytes.length>1000&&bytes.length<150000);assertEquals("RIFF",new String(bytes,0,4,java.nio.charset.StandardCharsets.US_ASCII));assertEquals("WEBP",new String(bytes,8,4,java.nio.charset.StandardCharsets.US_ASCII));
            String hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));assertEquals(image.get("sha256"),hash);assertTrue(digests.add(hash));
        }
        assertTrue(Files.isRegularFile(Path.of("src/main/webapp"+RecipeImage.FALLBACK)));
    }
}
