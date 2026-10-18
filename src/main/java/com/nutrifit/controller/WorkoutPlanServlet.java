package com.nutrifit.controller;

import com.nutrifit.dto.WorkoutPlanView;
import com.nutrifit.model.Workout;
import com.nutrifit.service.WorkoutPlanService;
import com.nutrifit.service.WorkoutService;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

import java.io.IOException;
import java.sql.SQLException;
import java.util.List;

@WebServlet(urlPatterns = {"/workout/plan", "/workout/plan/*"})
public class WorkoutPlanServlet extends HttpServlet {

    private static final String VIEW_PLAN = "/WEB-INF/views/workout/plan.jsp";

    private final WorkoutPlanService planService = new WorkoutPlanService();
    private final WorkoutService workoutService = new WorkoutService();

    /**
     * GET /workout/plan -> xem lộ trình mới nhất (plan = null nếu chưa có)
     */
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        Long userId = requireUserId(request, response);
        if (userId == null) {
            return;
        }

        String path = request.getPathInfo();
        if (path != null && !"/".equals(path)) {
            response.sendError(HttpServletResponse.SC_NOT_FOUND);
            return;
        }

        try {
            WorkoutPlanView plan = planService.getLatestPlan(userId);
            List<Workout> workouts = workoutService.listAvailableWorkouts(userId); // cho form "thêm bài"
            request.setAttribute("plan", plan);
            request.setAttribute("workouts", workouts);
            request.getRequestDispatcher(VIEW_PLAN).forward(request, response);
        } catch (SecurityException e) {
            response.sendError(HttpServletResponse.SC_FORBIDDEN, e.getMessage());
        } catch (SQLException e) {
            throw new ServletException("Lỗi tải lộ trình tập", e);
        }
    }

    /**
     * POST /workout/plan/generate                        -> tạo lộ trình 7 ngày mới
     * POST /workout/plan/duration (detailId, minutes)    -> đổi thời lượng một bài
     * POST /workout/plan/add (dayId, workoutId, minutes) -> thêm bài vào ngày
     * POST /workout/plan/remove (detailId)               -> xoá bài khỏi ngày
     */
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        Long userId = requireUserId(request, response);
        if (userId == null) {
            return;
        }

        String path = request.getPathInfo() == null ? "" : request.getPathInfo();

        try {
            switch (path) {
                case "/generate" -> {
                    planService.generateSevenDayPlan(userId);
                    redirectToPlan(request, response);
                }
                case "/duration" -> {
                    Long detailId = parseLong(request.getParameter("detailId"));
                    Integer minutes = parseInt(request.getParameter("minutes"));
                    if (detailId == null || minutes == null) {
                        badRequest(response);
                        return;
                    }
                    planService.changeDuration(userId, detailId, minutes);
                    redirectToPlan(request, response);
                }
                case "/add" -> {
                    Long dayId = parseLong(request.getParameter("dayId"));
                    Long workoutId = parseLong(request.getParameter("workoutId"));
                    Integer minutes = parseInt(request.getParameter("minutes"));
                    if (dayId == null || workoutId == null || minutes == null) {
                        badRequest(response);
                        return;
                    }
                    planService.addWorkout(userId, dayId, workoutId, minutes);
                    redirectToPlan(request, response);
                }
                case "/remove" -> {
                    Long detailId = parseLong(request.getParameter("detailId"));
                    if (detailId == null) {
                        badRequest(response);
                        return;
                    }
                    planService.removeWorkout(userId, detailId);
                    redirectToPlan(request, response);
                }
                default -> response.sendError(HttpServletResponse.SC_NOT_FOUND);
            }
        } catch (SecurityException e) {
            response.sendError(HttpServletResponse.SC_FORBIDDEN, e.getMessage());
        } catch (IllegalArgumentException | IllegalStateException e) {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, e.getMessage());
        } catch (SQLException e) {
            throw new ServletException("Lỗi cập nhật lộ trình tập", e);
        }
    }

    // ---- helper ----

    private void redirectToPlan(HttpServletRequest request, HttpServletResponse response)
            throws IOException {
        response.sendRedirect(request.getContextPath() + "/workout/plan");
    }

    private void badRequest(HttpServletResponse response) throws IOException {
        response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Thiếu hoặc sai tham số");
    }

    private Long requireUserId(HttpServletRequest request, HttpServletResponse response)
            throws IOException {
        HttpSession session = request.getSession(false);
        if (session != null && session.getAttribute("userId") instanceof Long userId) {
            return userId;
        }
        response.sendRedirect(request.getContextPath() + "/login");
        return null;
    }

    private Long parseLong(String s) {
        try {
            return s == null ? null : Long.valueOf(s.trim());
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private Integer parseInt(String s) {
        try {
            return s == null ? null : Integer.valueOf(s.trim());
        } catch (NumberFormatException e) {
            return null;
        }
    }
}
