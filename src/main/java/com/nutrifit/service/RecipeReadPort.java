package com.nutrifit.service;

import com.nutrifit.dto.RecipeCandidate;
import com.nutrifit.dto.RecipeNutritionInput;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.List;
import java.util.Optional;

/** Integration boundary; replace implementation when the Recipe module exposes a shared API. */
public interface RecipeReadPort {
    Optional<RecipeNutritionInput> findNutritionInput(Connection connection, long recipeId)
            throws SQLException;
    /** Batch boundary; existing Food/Recipe implementations remain source compatible. */
    default java.util.Map<Long, RecipeNutritionInput> findNutritionInputs(Connection connection, java.util.Collection<Long> ids)
            throws SQLException {
        java.util.Map<Long, RecipeNutritionInput> result = new java.util.LinkedHashMap<>();
        for (Long id : ids) findNutritionInput(connection, id).ifPresent(value -> result.put(id, value));
        return result;
    }
    List<RecipeCandidate> listCandidates(Connection connection) throws SQLException;
}
