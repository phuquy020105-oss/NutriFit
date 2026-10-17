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
    List<RecipeCandidate> listCandidates(Connection connection) throws SQLException;
}
