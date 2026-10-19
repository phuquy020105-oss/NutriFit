package com.nutrifit.controller;

import com.nutrifit.dto.*;
import com.nutrifit.model.MealEntry.MealType;
import com.nutrifit.service.*;
import com.nutrifit.util.Csrf;
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
            MealSuggestion suggestion = service.recommendDay(user);
            Draft draft = new Draft(UUID.randomUUID().toString(), suggestion, Instant.now());
            HttpSession session = req.getSession(false);
            synchronized (session) { session.setAttribute(DRAFT, draft); }
            req.setAttribute("suggestion", suggestion);
            req.setAttribute("suggestionToken", draft.token);
            req.setAttribute("csrf", Csrf.token(req));
            req.getRequestDispatcher("/WEB-INF/views/nutrition/meal-recommendations.jsp").forward(req, resp);
        } catch (Exception e) { fail(req, resp, e); }
    }

    @Override protected void doPost(HttpServletRequest req, HttpServletResponse resp)
            throws ServletException, IOException {
        req.setCharacterEncoding("UTF-8");
        Long user = requireUser(req, resp);
        if (user == null || !requireCsrf(req, resp)) return;
        try {
            String action = required(req.getParameter("action"));
            if (!Set.of("preview", "save").contains(action)) throw new IllegalArgumentException("Invalid action");
            HttpSession session = req.getSession(false);
            // Serializes duplicate submits for this session, including the database commit.
            synchronized (session) {
                Object value = session.getAttribute(DRAFT);
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
                Map<MealType, BigDecimal> amounts = new EnumMap<>(MealType.class);
                for (MealType type : MealType.values()) {
                    amounts.put(type, parseServings(req.getParameter("servings_" + type.name())));
                }
                if ("preview".equals(action)) {
                    draft.suggestion = service.refresh(user, draft.suggestion, amounts);
                    resp.setContentType("application/json;charset=UTF-8");
                    resp.getWriter().write(json(draft.suggestion));
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
        resp.sendRedirect(req.getContextPath() + "/nutrition/meal-planner?message=suggested");
    }

    private static String facts(NutritionFacts f) {
        return "{\"caloriesKcal\":\"" + f.caloriesKcal().toPlainString()
                + "\",\"proteinG\":\"" + f.proteinG().toPlainString()
                + "\",\"carbsG\":\"" + f.carbsG().toPlainString()
                + "\",\"fatG\":\"" + f.fatG().toPlainString()
                + "\",\"fiberG\":\"" + f.fiberG().toPlainString() + "\"}";
    }
    private static String json(MealSuggestion s) {
        List<String> meals = new ArrayList<>();
        for (SuggestedMeal m : s.meals()) meals.add("{\"mealType\":\"" + m.mealType().name()
                + "\",\"nutrition\":" + facts(m.nutrition()) + "}");
        return "{\"meals\":[" + String.join(",", meals) + "],\"total\":" + facts(s.total())
                + ",\"targetKcal\":\"" + s.targetKcal().toPlainString()
                + "\",\"differenceKcal\":\"" + s.differenceKcal().toPlainString()
                + "\",\"personalized\":" + s.personalized() + "}";
    }

    static final class Draft {
        final String token;
        final Instant created;
        MealSuggestion suggestion;
        boolean attempted;
        boolean saved;
        Draft(String token, MealSuggestion suggestion, Instant created) {
            this.token = token; this.suggestion = suggestion; this.created = created;
        }
    }
}
