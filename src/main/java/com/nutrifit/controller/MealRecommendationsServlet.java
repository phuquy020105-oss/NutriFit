package com.nutrifit.controller;

import com.nutrifit.dto.*;
import com.nutrifit.model.MealEntry.MealType;
import com.nutrifit.service.*;
import com.nutrifit.util.Csrf;
import com.nutrifit.util.JsonLite;
import com.nutrifit.util.RecipeImage;
import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.*;
import java.io.IOException;
import java.math.BigDecimal;
import java.time.Instant;
import java.time.Duration;
import java.util.*;

@WebServlet("/nutrition/recommendations")
public class MealRecommendationsServlet extends NutritionServletSupport {
    static final String DRAFT = "nutrifit.nutrition.suggestion";
    private final MealRecommendationService service;
    private final MealPlannerService planner;

    public MealRecommendationsServlet() { this(new MealRecommendationService(), new MealPlannerService()); }
    MealRecommendationsServlet(MealRecommendationService service, MealPlannerService planner) {
        this.service = service; this.planner = planner;
    }

    @Override protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        Long user = requireUser(req, resp);
        if (user == null) return;
        try {
            req.setAttribute("today", planner.getToday(user));
            req.setAttribute("recipes", planner.listAvailableRecipes());
            req.setAttribute("csrf", Csrf.token(req));
            HttpSession session = req.getSession(false);
            synchronized (session) {
                Object value = session.getAttribute(DRAFT);
                Draft draft = value instanceof Draft d && active(d, user) ? d : null;
                try {
                    if (draft == null) {
                        draft = new Draft(UUID.randomUUID().toString(), service.recommendDay(user), Instant.now());
                        session.setAttribute(DRAFT, draft);
                    } else if (!draft.attempted) {
                        draft.suggestion = service.refresh(user, draft.suggestion, standardAmounts());
                    }
                    req.setAttribute("suggestion", draft.suggestion);
                    req.setAttribute("suggestionToken", draft.token);
                    req.setAttribute("suggestionSaved", draft.saved);
                    req.setAttribute("saveBlocked", draft.attempted);
                } catch (RecommendationUnavailableException e) {
                    req.setAttribute("suggestionError", e.getMessage());
                }
            }
            req.setAttribute("notice", notice(req.getParameter("message")));
            req.getRequestDispatcher("/WEB-INF/views/nutrition/meal-recommendations.jsp").forward(req, resp);
        } catch (Exception e) { fail(req, resp, e); }
    }

    private boolean active(Draft draft, long user) {
        return draft.suggestion.userId() == user && draft.suggestion.date().equals(planner.today())
                && !draft.created.isBefore(Instant.now().minus(Duration.ofMinutes(30)));
    }
    private static Map<MealType, BigDecimal> standardAmounts() {
        Map<MealType, BigDecimal> amounts = new EnumMap<>(MealType.class);
        for (MealType type : MealType.values()) amounts.put(type, new BigDecimal("1.00"));
        return amounts;
    }
    private static String notice(String message) {
        return switch (message == null ? "" : message) {
            case "suggested" -> "Đã lưu thực đơn ba bữa vào nhật ký hôm nay.";
            case "swapped" -> "Đã đổi một món trong bản xem trước; nhật ký chưa thay đổi.";
            case "swap-unavailable" -> "Chưa có món thay thế phù hợp; món hiện tại được giữ nguyên.";
            case "added" -> "Đã ghi nhận món ăn.";
            case "updated" -> "Đã đổi món trong nhật ký hôm nay.";
            case "deleted" -> "Đã xóa món khỏi nhật ký hôm nay.";
            case "regenerated" -> "Đã tạo thực đơn mới cho bạn.";
            case "unchanged" -> "Chưa tìm được tổ hợp khác có chất lượng tương đương từ dữ liệu hiện có.";
            default -> null;
        };
    }

    @Override protected void doPost(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        req.setCharacterEncoding("UTF-8");
        Long user = requireUser(req, resp);
        if (user == null || !requireCsrf(req, resp)) return;
        try {
            String action = required(req.getParameter("action"));
            if (!Set.of("preview", "save", "regenerate", "swap").contains(action)) throw new IllegalArgumentException("Invalid action");
            HttpSession session = req.getSession(false);
            // Serializes duplicate submits for this session, including the database commit.
            synchronized (session) {
                Object value = session.getAttribute(DRAFT);
                if ("regenerate".equals(action)) {
                    MealSuggestion previous = value instanceof Draft d && active(d, user) ? d.suggestion : null;
                    List<List<Long>> recent = value instanceof Draft d && active(d,user) ? d.recent : List.of();
                    MealSuggestion next = service.recommendDay(user, previous, recent);
                    session.setAttribute(DRAFT, new Draft(UUID.randomUUID().toString(), next, Instant.now(), recent));
                    boolean same = previous != null && previous.meals().stream().map(SuggestedMeal::recipeId).toList()
                            .equals(next.meals().stream().map(SuggestedMeal::recipeId).toList());
                    resp.sendRedirect(req.getContextPath() + "/nutrition/recommendations?message="
                            + (same ? "unchanged" : "regenerated"));
                    return;
                }
                if (!(value instanceof Draft draft) || draft.suggestion.userId() != user
                        || !draft.token.equals(required(req.getParameter("suggestionToken")))) {
                    throw new SecurityException("Preview does not belong to this account");
                }
                if (!draft.suggestion.date().equals(planner.today())
                        || draft.created.isBefore(Instant.now().minus(Duration.ofMinutes(30)))) {
                    throw new RecommendationUnavailableException("Gợi ý đã hết hạn. Hãy tạo thực đơn mới cho hôm nay.");
                }
                if (draft.saved && "save".equals(action)) {
                    redirect(req, resp);
                    return;
                }
                if (draft.attempted) throw new RecommendationUnavailableException(
                        "Thực đơn này đã được gửi lưu. Hãy kiểm tra nhật ký trước khi tạo gợi ý mới.");
                if ("swap".equals(action)) {
                    MealType type = MealType.valueOf(required(req.getParameter("mealType")));
                    List<Long> recent = draft.swaps.get(type);
                    MealSuggestion next = service.swap(user, draft.suggestion, type, List.copyOf(recent));
                    boolean changed = !MealRecommendationService.recipeIds(next).equals(MealRecommendationService.recipeIds(draft.suggestion));
                    String message = changed ? "Đã đổi món; nhật ký chưa thay đổi."
                            : "Đã hết món thay thế phù hợp trong lần xem trước này. Món hiện tại được giữ nguyên.";
                    boolean revised = !next.equals(draft.suggestion);
                    draft.suggestion = next;
                    if (changed) {
                        recent.add(next.meals().stream().filter(m -> m.mealType() == type).findFirst().orElseThrow().recipeId());
                        if (recent.size() > 30) recent.removeFirst();
                    }
                    if (revised) draft.token = UUID.randomUUID().toString(); // Reject stale saves/swaps from another tab.
                    if ("json".equals(req.getParameter("format"))) {
                        resp.setContentType("application/json;charset=UTF-8");
                        resp.getWriter().write("{\"changed\":" + changed + ",\"message\":" + JsonLite.quote(message)
                                + ",\"suggestionToken\":" + JsonLite.quote(draft.token)
                                + ",\"suggestion\":" + json(next, req.getContextPath()) + "}");
                    } else {
                        resp.sendRedirect(req.getContextPath() + "/nutrition/recommendations?message=" + (changed ? "swapped" : "swap-unavailable"));
                    }
                    return;
                }
                // Portions, recipe IDs and nutrition are owned by the server, never the posted fields.
                Map<MealType, BigDecimal> amounts = standardAmounts();
                if ("preview".equals(action)) {
                    draft.suggestion = service.refresh(user, draft.suggestion, amounts);
                    resp.setContentType("application/json;charset=UTF-8");
                    resp.getWriter().write(json(draft.suggestion, req.getContextPath()));
                } else {
                    // Preserve attempted state on uncertain commit failures; never retry automatically.
                    draft.attempted = true;
                    planner.saveSuggestion(user, draft.suggestion, amounts);
                    draft.saved = true;
                    redirect(req, resp);
                }
            }
        } catch (Exception e) { fail(req, resp, e); }
    }

    private void redirect(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        resp.sendRedirect(req.getContextPath() + "/nutrition/recommendations?message=suggested");
    }

    private static String facts(NutritionFacts f) {
        return "{\"caloriesKcal\":\"" + f.caloriesKcal().toPlainString()
                + "\",\"proteinG\":\"" + f.proteinG().toPlainString()
                + "\",\"carbsG\":\"" + f.carbsG().toPlainString()
                + "\",\"fatG\":\"" + f.fatG().toPlainString()
                + "\",\"fiberG\":\"" + f.fiberG().toPlainString() + "\"}";
    }
    private static String json(MealSuggestion s, String context) {
        List<String> meals = new ArrayList<>();
        for (SuggestedMeal m : s.meals()) meals.add("{\"mealType\":\"" + m.mealType().name()
                + "\",\"recipeId\":" + m.recipeId() + ",\"name\":" + JsonLite.quote(m.name())
                + ",\"imageUrl\":" + JsonLite.quote(RecipeImage.url(context, m.imageUrl()))
                + ",\"nutrition\":" + facts(m.nutrition()) + "}");
        return "{\"meals\":[" + String.join(",", meals) + "],\"total\":" + facts(s.total())
                + ",\"targetKcal\":\"" + s.targetKcal().toPlainString()
                + "\",\"differenceKcal\":\"" + s.differenceKcal().toPlainString()
                + "\",\"recordedToday\":" + facts(s.recordedToday())
                + ",\"projectedDay\":" + facts(s.projectedDay())
                + ",\"recordedMealCount\":" + s.recordedMealCount()
                + ",\"projectedDifferenceKcal\":\"" + s.projectedDifferenceKcal().toPlainString()
                + "\",\"exceedsTarget\":" + s.exceedsTarget()
                + ",\"personalized\":" + s.personalized()
                + ",\"warnings\":[" + String.join(",", s.warnings().stream().map(JsonLite::quote).toList()) + "]}";
    }

    static final class Draft {
        String token;
        final Instant created;
        MealSuggestion suggestion;
        boolean attempted;
        boolean saved;
        final List<List<Long>> recent;
        final Map<MealType,List<Long>> swaps = new EnumMap<>(MealType.class);
        Draft(String token, MealSuggestion suggestion, Instant created) { this(token,suggestion,created,List.of()); }
        Draft(String token, MealSuggestion suggestion, Instant created, List<List<Long>> previous) {
            this.token = token; this.suggestion = suggestion; this.created = created;
            for (var m : suggestion.meals()) swaps.put(m.mealType(), new ArrayList<>(List.of(m.recipeId())));
            List<List<Long>> history = new ArrayList<>(previous);
            history.add(MealRecommendationService.recipeIds(suggestion));
            recent = List.copyOf(history.subList(Math.max(0,history.size()-5),history.size()));
        }
    }
}
