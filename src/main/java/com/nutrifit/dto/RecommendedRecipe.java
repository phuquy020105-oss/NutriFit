package com.nutrifit.dto;

public record RecommendedRecipe(RecipeCandidate recipe, double score, String reason) { }
