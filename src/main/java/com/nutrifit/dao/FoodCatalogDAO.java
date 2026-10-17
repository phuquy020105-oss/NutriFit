package com.nutrifit.dao;

import com.nutrifit.dto.FoodOption;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

/** Read-only integration boundary to Foods, until Food module publishes its own DAO/service. */
public class FoodCatalogDAO {
    public List<FoodOption> listActive(Connection c) throws SQLException {
        List<FoodOption> results = new ArrayList<>();
        try (PreparedStatement ps = c.prepareStatement(
                "SELECT food_id,name FROM foods WHERE active=TRUE ORDER BY name,food_id")) {
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) results.add(new FoodOption(rs.getLong(1), rs.getString(2)));
            }
        }
        return results;
    }
}
