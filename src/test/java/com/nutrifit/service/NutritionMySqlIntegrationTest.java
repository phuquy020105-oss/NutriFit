package com.nutrifit.service;

import com.nutrifit.config.DatabaseConfig;
import com.nutrifit.dao.FoodCatalogDAO;
import com.nutrifit.dao.JdbcRecipeReadAdapter;
import com.nutrifit.dao.MealEntryDAO;
import com.nutrifit.dao.MealPlanDAO;
import com.nutrifit.dto.IngredientNutritionLine;
import com.nutrifit.dto.NutritionFacts;
import com.nutrifit.dto.RecipeCandidate;
import com.nutrifit.dto.RecipeNutritionInput;
import com.nutrifit.model.MealEntry.MealType;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Clock;
import java.util.ArrayList;
import java.util.Base64;
import java.util.EnumMap;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;
import static org.junit.jupiter.api.Assertions.*;

/** Real DatabaseConfig/JDBC/DAO tests. No user fixtures, INSERT/UPDATE/DELETE or commit. */
@EnabledIfEnvironmentVariable(named = "NUTRIFIT_MYSQL_INTEGRATION", matches = "true")
class NutritionMySqlIntegrationTest {
    private static final Map<String, Food> FOODS = new LinkedHashMap<>();
    private static final Map<String, Recipe> RECIPES = new LinkedHashMap<>();
    private static final Map<String, List<Ingredient>> INGREDIENTS = new LinkedHashMap<>();
    private static final Map<String, Long> FOOD_IDS = new HashMap<>();
    private static final Map<String, Long> RECIPE_IDS = new HashMap<>();
    private static Path fixtures;
    private Connection connection;
    private final JdbcRecipeReadAdapter adapter = new JdbcRecipeReadAdapter();
    private final NutritionCalculator calculator = new NutritionCalculator();

    private record Food(String name, NutritionFacts facts) { }
    private record Recipe(String name, MealType type, BigDecimal base, int minutes, String instructions) { }
    private record Ingredient(String foodRef, BigDecimal grams) { }

    @BeforeAll
    static void loadIndependentExpectationsAndGeneratedIds() throws Exception {
        String directory = System.getenv("NUTRIFIT_CATALOG_FIXTURES");
        assertNotNull(directory, "Prepare fixtures using docs/nutrition/mysql-integration-setup.md");
        fixtures = Path.of(directory);
        String actualHash = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                .digest(Files.readAllBytes(Path.of("database/seed/vietnamese_catalog.json"))));
        assertEquals(Files.readString(fixtures.resolve("catalog.sha256")).trim(), actualHash,
                "Generated expectations are stale");
        for (String[] f : lines("foods.tsv")) FOODS.put(f[0], new Food(decode(f[1]), facts(f, 2)));
        for (String[] r : lines("recipes.tsv")) {
            RECIPES.put(r[0], new Recipe(decode(r[1]), MealType.valueOf(r[2]),
                    new BigDecimal(r[3]), Integer.parseInt(r[4]), decode(r[5])));
        }
        for (String[] i : lines("ingredients.tsv")) {
            INGREDIENTS.computeIfAbsent(i[0], key -> new ArrayList<>())
                    .add(new Ingredient(i[1], new BigDecimal(i[2])));
        }
        assertEquals(82, FOODS.size());
        assertEquals(30, RECIPES.size());
        assertEquals(383, INGREDIENTS.values().stream().mapToInt(List::size).sum());
        try (Connection c = openReadOnly()) {
            for (var f : FOODS.entrySet()) FOOD_IDS.put(f.getKey(), findId(c, "foods", "food_id", f.getValue().name()));
            for (var r : RECIPES.entrySet()) RECIPE_IDS.put(r.getKey(), findId(c, "recipes", "recipe_id", r.getValue().name()));
            c.rollback();
        }
    }

    @BeforeEach
    void connect() throws SQLException { connection = openReadOnly(); }

    @AfterEach
    void closeWithoutCommit() throws SQLException {
        if (connection != null) {
            try { connection.rollback(); } finally { connection.close(); }
        }
    }

    private static Connection openReadOnly() throws SQLException {
        Connection c = DatabaseConfig.getConnection();
        try {
            c.setReadOnly(true);
            c.setAutoCommit(false);
            return c;
        } catch (SQLException e) {
            c.close();
            throw e;
        }
    }

    @Test
    void databaseConfigAndCompleteFoodCatalogMatchJson() throws Exception {
        assertTrue(connection.isReadOnly());
        assertFalse(connection.getAutoCommit());
        try (var s = connection.createStatement(); var rs = s.executeQuery("SELECT DATABASE(), VERSION(), @@session.transaction_read_only")) {
            assertTrue(rs.next());
            assertEquals("nutrifitdb_java", rs.getString(1));
            assertEquals(1, rs.getInt(3), "Server must enforce read-only sessions");
            System.out.println("Real JDBC database=" + rs.getString(1) + ", MySQL=" + rs.getString(2)
                    + ", driver=" + connection.getMetaData().getDriverVersion());
        }
        assertEquals(82, count("SELECT COUNT(*) FROM foods"));
        assertEquals(30, count("SELECT COUNT(*) FROM recipes"));
        assertEquals(383, count("SELECT COUNT(*) FROM recipeingredients"));
        assertEquals(0, count("SELECT COUNT(*) FROM recipeingredients i LEFT JOIN foods f ON f.food_id=i.food_id "
                + "LEFT JOIN recipes r ON r.recipe_id=i.recipe_id WHERE f.food_id IS NULL OR r.recipe_id IS NULL"));
        var options = new FoodCatalogDAO().listActive(connection);
        assertEquals(82, options.size());
        assertEquals(FOODS.values().stream().map(Food::name).collect(Collectors.toSet()),
                options.stream().map(x -> x.name()).collect(Collectors.toSet()));
        for (var f : FOODS.entrySet()) {
            try (var ps = connection.prepareStatement("SELECT * FROM foods WHERE food_id=?")) {
                ps.setLong(1, FOOD_IDS.get(f.getKey()));
                try (var rs = ps.executeQuery()) {
                    assertTrue(rs.next());
                    assertTrue(rs.getBoolean("active"));
                    assertNumericFacts(f.getValue().facts(), foodFacts(rs));
                }
            }
        }
    }

    @Test
    void adapterReadsAllThirtyRecipesAnd383ExactIngredientLines() throws Exception {
        var candidates = adapter.listCandidates(connection);
        assertEquals(30, candidates.size());
        Map<MealType, Long> counts = candidates.stream().collect(Collectors.groupingBy(
                RecipeCandidate::mealType, () -> new EnumMap<>(MealType.class), Collectors.counting()));
        for (MealType type : MealType.values()) assertEquals(10L, counts.get(type));
        int total = 0;
        for (var r : RECIPES.entrySet()) {
            RecipeNutritionInput input = input(r.getKey());
            assertEquals(r.getValue().name(), input.name());
            assertEquals(r.getValue().type(), input.mealType());
            assertEquals(0, r.getValue().base().compareTo(input.baseServings()));
            Map<Long, IngredientNutritionLine> byFood = input.ingredients().stream().collect(
                    Collectors.toMap(IngredientNutritionLine::foodId, x -> x));
            assertEquals(INGREDIENTS.get(r.getKey()).size(), byFood.size());
            for (Ingredient expected : INGREDIENTS.get(r.getKey())) {
                var actual = byFood.get(FOOD_IDS.get(expected.foodRef()));
                assertNotNull(actual, r.getKey() + "/" + expected.foodRef());
                assertTrue(actual.foodId() > 0);
                assertEquals(0, expected.grams().compareTo(actual.quantityGrams()));
                assertNumericFacts(FOODS.get(expected.foodRef()).facts(), actual.nutrientsPer100g());
            }
            try (var ps = connection.prepareStatement("SELECT active,instructions,prep_minutes,image_url FROM recipes WHERE recipe_id=?")) {
                ps.setLong(1, input.recipeId());
                try (var rs = ps.executeQuery()) {
                    assertTrue(rs.next());
                    assertTrue(rs.getBoolean(1));
                    assertEquals(r.getValue().instructions(), rs.getString(2));
                    assertEquals(r.getValue().minutes(), rs.getInt(3));
                    assertNull(rs.getString(4));
                }
            }
            var candidate = candidates.stream().filter(x -> x.recipeId() == input.recipeId()).findFirst().orElseThrow();
            assertEquals(byFood.keySet(), candidate.foodIds());
            assertEquals(calculator.calculate(input, BigDecimal.ONE), candidate.perServing());
            total += byFood.size();
        }
        assertEquals(383, total);
        assertFalse(connection.isClosed(), "Adapter must not close caller-owned Connection");
        assertTrue(adapter.findNutritionInput(connection, 0).isEmpty());
    }

    static Stream<Arguments> nutritionCases() throws Exception {
        return lines("totals.tsv").stream().map(row -> Arguments.of(row[0], row[1], facts(row, 2)));
    }

    @ParameterizedTest(name = "{0} at {1} servings")
    @MethodSource("nutritionCases")
    void calculatorMatchesIndependentDecimalExpectations(String ref, String servings, NutritionFacts expected) throws Exception {
        NutritionFacts actual = calculator.calculate(input(ref), new BigDecimal(servings));
        assertEquals(expected, actual, "All five nutrients, HALF_UP scale 3, final rounding only");
    }

    @Test
    void catalogRecipeSupportsServingBoundsAndRejectsInvalidValues() throws Exception {
        RecipeNutritionInput recipe = input(RECIPES.keySet().iterator().next());
        for (String value : List.of("0", "-1", "0.001", "1.001", "1000000")) {
            assertThrows(IllegalArgumentException.class, () -> calculator.calculate(recipe, new BigDecimal(value)));
        }
        assertThrows(IllegalArgumentException.class, () -> calculator.calculate(recipe, null));
        for (String value : List.of("0.01", "999999.99")) {
            var result = calculator.calculate(recipe, new BigDecimal(value));
            assertTrue(result.caloriesKcal().signum() > 0);
            assertTrue(result.caloriesKcal().compareTo(new BigDecimal("999999999.999")) <= 0);
        }
    }

    @Test
    void mealPlannerServiceListsRealCandidatesUsingReadOnlyConnections() throws Exception {
        MealPlannerService service = new MealPlannerService(new MealPlanDAO(), new MealEntryDAO(),
                adapter, calculator, Clock.systemDefaultZone(), NutritionMySqlIntegrationTest::openReadOnly);
        var actual = service.listAvailableRecipes();
        assertEquals(30, actual.size());
        assertEquals(RECIPES.values().stream().map(Recipe::name).collect(Collectors.toSet()),
                actual.stream().map(RecipeCandidate::name).collect(Collectors.toSet()));
    }

    private RecipeNutritionInput input(String ref) throws SQLException {
        return adapter.findNutritionInput(connection, RECIPE_IDS.get(ref)).orElseThrow();
    }

    private long count(String sql) throws SQLException {
        try (var s = connection.createStatement(); var rs = s.executeQuery(sql)) { assertTrue(rs.next()); return rs.getLong(1); }
    }

    private static long findId(Connection c, String table, String column, String name) throws SQLException {
        // table/column are constants above, name is always parameterized; IDs are never guessed.
        try (var ps = c.prepareStatement("SELECT " + column + ",name FROM " + table + " WHERE name=?")) {
            ps.setString(1, name);
            try (var rs = ps.executeQuery()) {
                assertTrue(rs.next(), "Missing catalog name");
                long id = rs.getLong(1);
                assertTrue(id > 0);
                assertEquals(name, rs.getString(2));
                assertFalse(rs.next(), "Ambiguous catalog name");
                return id;
            }
        }
    }

    private static NutritionFacts foodFacts(ResultSet rs) throws SQLException {
        return new NutritionFacts(rs.getBigDecimal("calories_per_100g"), rs.getBigDecimal("protein_per_100g"),
                rs.getBigDecimal("carbs_per_100g"), rs.getBigDecimal("fat_per_100g"), rs.getBigDecimal("fiber_per_100g"));
    }

    private static void assertNumericFacts(NutritionFacts expected, NutritionFacts actual) {
        assertEquals(expected.rounded(), actual.rounded());
    }

    private static NutritionFacts facts(String[] cells, int offset) {
        return new NutritionFacts(new BigDecimal(cells[offset]), new BigDecimal(cells[offset + 1]),
                new BigDecimal(cells[offset + 2]), new BigDecimal(cells[offset + 3]), new BigDecimal(cells[offset + 4]));
    }

    private static List<String[]> lines(String name) throws Exception {
        return Files.readAllLines(fixtures.resolve(name), StandardCharsets.UTF_8).stream()
                .filter(s -> !s.isBlank()).map(s -> s.split("\t", -1)).toList();
    }

    private static String decode(String value) { return new String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8); }
}
