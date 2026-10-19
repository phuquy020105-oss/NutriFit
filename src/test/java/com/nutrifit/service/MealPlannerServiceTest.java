package com.nutrifit.service;

import com.nutrifit.dao.MealEntryDAO;
import com.nutrifit.dao.MealPlanDAO;
import com.nutrifit.dto.IngredientNutritionLine;
import com.nutrifit.dto.NutritionFacts;
import com.nutrifit.dto.RecipeCandidate;
import com.nutrifit.dto.RecipeNutritionInput;
import com.nutrifit.model.MealEntry;
import com.nutrifit.model.MealPlan;
import org.junit.jupiter.api.Test;
import java.lang.reflect.Proxy;
import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.SQLException;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import static org.junit.jupiter.api.Assertions.*;

/** Service tests with strict in-memory DAO/JDBC doubles. Never opens DatabaseConfig. */
class MealPlannerServiceTest {
    private static final long OWNER = 42L;
    private static final long RECIPE = 7L;
    private static final long PLAN = 10L;
    private static final long ENTRY = 20L;
    private static final LocalDate TODAY = LocalDate.of(2026, 10, 16);
    private static final Clock CLOCK = Clock.fixed(Instant.parse("2026-10-16T05:00:00Z"),
            ZoneId.of("Asia/Bangkok"));

    @Test
    void insertsCalculatedSnapshotAndCommits() throws Exception {
        Fixture f = new Fixture();
        MealEntry result = f.service.addMeal(OWNER, RECIPE, MealEntry.MealType.LUNCH, decimal("1.5"));
        assertEquals(ENTRY, result.getEntryId());
        assertEquals("Current recipe", result.getRecipeNameSnapshot());
        assertEquals(decimal("150.000"), result.getCaloriesKcal());
        assertEquals(1, f.inserts);
        assertEquals(List.of("autoCommit:false", "commit", "close"), f.transactions);
    }

    @Test
    void addingSameRecipeMergesServingsUsingOriginalSnapshot() throws Exception {
        Fixture f = new Fixture();
        f.stored = entry();
        f.recipeCalories = "9000"; // Recipe edited since this entry was recorded.
        MealEntry result = f.service.addMeal(OWNER, RECIPE, MealEntry.MealType.LUNCH, decimal("0.50"));
        assertEquals(decimal("1.50"), result.getServings());
        assertEquals(decimal("150.000"), result.getCaloriesKcal());
        assertEquals("Original snapshot", result.getRecipeNameSnapshot());
        assertEquals(0, f.inserts);
        assertEquals(1, f.updates);
        assertEquals(List.of("autoCommit:false", "commit", "close"), f.transactions);
    }

    @Test
    void changingServingsDoesNotReadEditedOrInactiveRecipe() throws Exception {
        Fixture f = new Fixture();
        f.stored = entry();
        f.recipeAvailable = false;
        MealEntry result = f.service.updateMeal(OWNER, ENTRY, RECIPE, MealEntry.MealType.LUNCH, decimal("2"));
        assertEquals(decimal("200.000"), result.getCaloriesKcal());
        assertEquals("Original snapshot", result.getRecipeNameSnapshot());
        assertEquals(0, f.recipeReads);
        assertEquals(1, f.updates);
        assertEquals(List.of("autoCommit:false", "commit", "close"), f.transactions);
    }

    @Test
    void historyAllowsOnlyPastDaysAndReturnsStoredTotals() throws Exception {
        Fixture f = new Fixture();
        assertEquals(TODAY, f.service.today());
        for (LocalDate day : new LocalDate[]{null, TODAY, TODAY.plusDays(1)}) {
            assertThrows(IllegalArgumentException.class, () -> f.service.getPastDay(OWNER, day));
        }
        assertEquals(0, f.opens);
        f.stored = entry();
        f.planDate = TODAY.minusDays(1);
        assertEquals(decimal("100.000"), f.service.getPastDay(OWNER, f.planDate).total().caloriesKcal());
        assertEquals(0, f.recipeReads);
    }

    @Test
    void updateAndDeleteRejectPastAndFutureEntriesAndRollback() {
        for (LocalDate day : List.of(TODAY.minusDays(1), TODAY.plusDays(1))) {
            for (boolean delete : new boolean[]{false, true}) {
                Fixture f = new Fixture();
                f.stored = entry();
                f.planDate = day;
                assertThrows(IllegalArgumentException.class, () -> {
                    if (delete) f.service.removeMeal(OWNER, ENTRY);
                    else f.service.updateMeal(OWNER, ENTRY, RECIPE, MealEntry.MealType.LUNCH, decimal("2"));
                });
                assertEquals(0, f.updates + f.deletes);
                assertEquals(List.of("autoCommit:false", "rollback", "close"), f.transactions);
            }
        }
    }

    @Test
    void updateAndDeletePassAuthenticatedOwnerToLookupAndRejectOtherUsers() {
        for (boolean delete : new boolean[]{false, true}) {
            Fixture f = new Fixture();
            f.stored = entry();
            assertThrows(IllegalArgumentException.class, () -> {
                if (delete) f.service.removeMeal(OWNER + 1, ENTRY);
                else f.service.updateMeal(OWNER + 1, ENTRY, RECIPE, MealEntry.MealType.LUNCH, decimal("2"));
            });
            assertEquals(OWNER + 1, f.lookupUser);
            assertEquals(0, f.updates + f.deletes);
            assertEquals(List.of("autoCommit:false", "rollback", "close"), f.transactions);
        }
    }

    @Test
    void deleteChecksOwnerAndCurrentDayBeforeCommitting() throws Exception {
        Fixture f = new Fixture();
        f.stored = entry();
        f.service.removeMeal(OWNER, ENTRY);
        assertEquals(1, f.deletes);
        assertEquals(OWNER, f.lookupUser);
        assertEquals(List.of("autoCommit:false", "commit", "close"), f.transactions);
    }

    @Test
    void changingToDuplicateRecipeIsRejectedWithoutWriting() {
        Fixture f = new Fixture();
        f.stored = entry();
        f.duplicate = entry();
        f.duplicate.setEntryId(ENTRY + 1);
        f.duplicate.setRecipeId(RECIPE + 1);
        assertThrows(IllegalArgumentException.class, () -> f.service.updateMeal(
                OWNER, ENTRY, RECIPE + 1, MealEntry.MealType.LUNCH, BigDecimal.ONE));
        assertEquals(0, f.updates);
        assertEquals(List.of("autoCommit:false", "rollback", "close"), f.transactions);
    }

    @Test
    void invalidIdentityAndServingsAreRejectedBeforeOpeningConnection() {
        Fixture f = new Fixture();
        assertThrows(SecurityException.class,
                () -> f.service.addMeal(0, RECIPE, MealEntry.MealType.LUNCH, BigDecimal.ONE));
        assertThrows(SecurityException.class, () -> f.service.removeMeal(0, ENTRY));
        assertThrows(IllegalArgumentException.class,
                () -> f.service.addMeal(OWNER, RECIPE, null, BigDecimal.ONE));
        assertThrows(IllegalArgumentException.class,
                () -> f.service.addMeal(OWNER, RECIPE, MealEntry.MealType.LUNCH, decimal("1000000")));
        assertEquals(0, f.opens);
    }

    @Test
    void overflowRollsBackBeforeEntryInsertOrUpdate() {
        for (boolean existing : new boolean[]{false, true}) {
            Fixture f = new Fixture();
            if (existing) {
                f.stored = entry();
                f.stored.setCaloriesKcal(decimal("999999999.999"));
            } else {
                f.recipeCalories = "1000000000";
            }
            assertThrows(IllegalArgumentException.class,
                    () -> f.service.addMeal(OWNER, RECIPE, MealEntry.MealType.LUNCH, BigDecimal.ONE));
            assertEquals(0, f.inserts + f.updates);
            assertEquals(List.of("autoCommit:false", "rollback", "close"), f.transactions);
        }
    }

    @Test
    void mergedServingsCannotExceedDecimalEightTwo() {
        Fixture f = new Fixture();
        f.stored = entry();
        f.stored.setServings(decimal("999999.99"));
        assertThrows(IllegalArgumentException.class,
                () -> f.service.addMeal(OWNER, RECIPE, MealEntry.MealType.LUNCH, decimal("0.01")));
        assertEquals(0, f.updates);
        assertEquals(List.of("autoCommit:false", "rollback", "close"), f.transactions);
    }

    @Test
    void databaseFailureRollsBackAndPreservesOriginalFailureIfRollbackFails() {
        Fixture f = new Fixture();
        f.insertFailure = new SQLException("insert failed");
        f.rollbackFailure = new SQLException("rollback failed");
        SQLException thrown = assertThrows(SQLException.class,
                () -> f.service.addMeal(OWNER, RECIPE, MealEntry.MealType.LUNCH, BigDecimal.ONE));
        assertSame(f.insertFailure, thrown);
        assertArrayEquals(new Throwable[]{f.rollbackFailure}, thrown.getSuppressed());
        assertEquals(List.of("autoCommit:false", "rollback", "close"), f.transactions);
    }

    @Test
    void commitFailureAlsoAttemptsRollbackAndClosesConnection() {
        Fixture f = new Fixture();
        f.commitFailure = new SQLException("commit failed");
        assertSame(f.commitFailure, assertThrows(SQLException.class,
                () -> f.service.addMeal(OWNER, RECIPE, MealEntry.MealType.LUNCH, BigDecimal.ONE)));
        assertEquals(List.of("autoCommit:false", "commit", "rollback", "close"), f.transactions);
    }

    @Test void changeRecipePreservesLegacyFractionAndEnforcesTodayAndOwner() throws Exception {
        Fixture f=new Fixture();f.stored=entry();f.stored.setServings(decimal("0.89"));
        MealEntry result=f.service.changeRecipe(OWNER,ENTRY,RECIPE+1,MealEntry.MealType.LUNCH);
        assertEquals(decimal("0.89"),result.getServings());
        assertEquals(decimal("89.000"),result.getCaloriesKcal());
        assertEquals(List.of("autoCommit:false","commit","close"),f.transactions);
        for (boolean wrongOwner:List.of(false,true)) {
            Fixture denied=new Fixture();denied.stored=entry();
            if (!wrongOwner) denied.planDate=TODAY.minusDays(1);
            assertThrows(IllegalArgumentException.class,()->denied.service.changeRecipe(wrongOwner?OWNER+1:OWNER,ENTRY,RECIPE+1,MealEntry.MealType.LUNCH));
            assertEquals(0,denied.updates);assertEquals(List.of("autoCommit:false","rollback","close"),denied.transactions);
        }
    }
    private static BigDecimal decimal(String value) { return new BigDecimal(value); }

    private static MealEntry entry() {
        MealEntry e = new MealEntry(PLAN, RECIPE, "Original snapshot", MealEntry.MealType.LUNCH,
                decimal("1.00"), decimal("100.000"), decimal("10.000"),
                decimal("20.000"), decimal("5.000"), decimal("2.000"));
        e.setEntryId(ENTRY);
        return e;
    }

    private static class Fixture {
        final List<String> transactions = new ArrayList<>();
        MealEntry stored;
        MealEntry duplicate;
        LocalDate planDate = TODAY;
        int opens, inserts, updates, deletes, recipeReads;
        long lookupUser;
        String recipeCalories = "100";
        boolean recipeAvailable = true;
        SQLException insertFailure, rollbackFailure, commitFailure;

        final Connection connection = (Connection) Proxy.newProxyInstance(
                getClass().getClassLoader(), new Class<?>[]{Connection.class}, (p, method, args) -> {
                    switch (method.getName()) {
                        case "setAutoCommit" -> transactions.add("autoCommit:" + args[0]);
                        case "commit" -> {
                            transactions.add("commit");
                            if (commitFailure != null) throw commitFailure;
                        }
                        case "rollback" -> {
                            transactions.add("rollback");
                            if (rollbackFailure != null) throw rollbackFailure;
                        }
                        case "close" -> transactions.add("close");
                        default -> throw new AssertionError("Unexpected JDBC access: " + method.getName());
                    }
                    return null;
                });

        final MealPlanDAO plans = new MealPlanDAO() {
            @Override public long findOrCreateForUpdate(Connection c, long user, LocalDate date) {
                assertSame(connection, c);
                assertEquals(OWNER, user);
                assertEquals(TODAY, date);
                return PLAN;
            }
            @Override public Optional<MealPlan> findByUserAndDate(Connection c, long user, LocalDate date) {
                assertSame(connection, c);
                return user == OWNER && date.equals(planDate)
                        ? Optional.of(new MealPlan(PLAN, OWNER, planDate, null)) : Optional.empty();
            }
        };

        final MealEntryDAO entries = new MealEntryDAO() {
            @Override public Optional<MealEntry> findByPlanMealRecipe(Connection c, long plan,
                    MealEntry.MealType type, long recipe) {
                assertSame(connection, c);
                assertEquals(PLAN, plan);
                assertEquals(MealEntry.MealType.LUNCH, type);
                return Optional.ofNullable(recipe == RECIPE ? stored : duplicate);
            }
            @Override public Optional<MealEntry> findByIdAndUser(Connection c, long id, long user) {
                assertSame(connection, c);
                assertEquals(ENTRY, id);
                lookupUser = user;
                return user == OWNER ? Optional.ofNullable(stored) : Optional.empty();
            }
            @Override public List<MealEntry> findByPlan(Connection c, long plan) {
                assertEquals(PLAN, plan);
                return stored == null ? List.of() : List.of(stored);
            }
            @Override public long insert(Connection c, MealEntry e) throws SQLException {
                assertSame(connection, c);
                if (insertFailure != null) throw insertFailure;
                inserts++;
                return ENTRY;
            }
            @Override public void update(Connection c, MealEntry e) {
                assertSame(connection, c);
                updates++;
            }
            @Override public void delete(Connection c, long id, long plan) {
                assertEquals(ENTRY, id);
                assertEquals(PLAN, plan);
                deletes++;
            }
        };

        final RecipeReadPort recipes = new RecipeReadPort() {
            @Override public Optional<RecipeNutritionInput> findNutritionInput(Connection c, long recipe) {
                assertSame(connection, c);
                recipeReads++;
                return recipeAvailable ? Optional.of(new RecipeNutritionInput(recipe, "Current recipe",
                        MealEntry.MealType.LUNCH, BigDecimal.ONE, List.of(new IngredientNutritionLine(1,
                        decimal("100"), new NutritionFacts(decimal(recipeCalories), decimal("10"),
                        decimal("20"), decimal("5"), decimal("2")))))) : Optional.empty();
            }
            @Override public List<RecipeCandidate> listCandidates(Connection c) {
                throw new AssertionError("Mutations must not scan the catalog");
            }
        };

        final MealPlannerService service = new MealPlannerService(plans, entries, recipes,
                new NutritionCalculator(), CLOCK, () -> { opens++; return connection; });
    }
}
