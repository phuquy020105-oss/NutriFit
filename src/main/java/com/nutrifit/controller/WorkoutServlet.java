package com.nutrifit.controller;

import com.nutrifit.model.Workout;
import com.nutrifit.model.WorkoutLog;
import com.nutrifit.service.WorkoutService;
import com.nutrifit.dao.WorkoutCategoryDAO;

import jakarta.servlet.ServletException;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpSession;

import java.io.IOException;
import java.sql.SQLException;
import java.util.List;

@WebServlet(urlPatterns = {"/workout", "/workout/*"})
public class WorkoutServlet extends HttpServlet {

    private static final String VIEW_LIST = "/WEB-INF/views/workout/workout-list.jsp";
    private static final String VIEW_DETAIL = "/WEB-INF/views/workout/workout-detail.jsp";

    private final WorkoutService workoutService = new WorkoutService();
    private final WorkoutCategoryDAO categoryDAO = new WorkoutCategoryDAO();

    /**
     * GET /workout             -> danh sách bài tập
     * GET /workout/detail?id=5 -> chi tiết một bài
     */
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        Long userId = requireUserId(request, response);
        if (userId == null) {
            return;
        }

        String path = request.getPathInfo();
        try {
            if (path == null || "/".equals(path)) {
                List<Workout> workouts = workoutService.listAvailableWorkouts(userId);

                request.setAttribute("workouts", workouts);
                request.setAttribute("categories", categoryDAO.findAll());

                request.getRequestDispatcher(VIEW_LIST).forward(request, response);

            } else if ("/detail".equals(path)) {
                Long workoutId = parseLong(request.getParameter("id"));
                if (workoutId == null) {
                    response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Thiếu hoặc sai id bài tập");
                    return;
                }
                Workout workout = workoutService.getWorkoutDetail(userId, workoutId);
                request.setAttribute("workout", workout);
                request.getRequestDispatcher(VIEW_DETAIL).forward(request, response);

            } else {
                response.sendError(HttpServletResponse.SC_NOT_FOUND);
            }
        } catch (SecurityException e) {
            response.sendError(HttpServletResponse.SC_FORBIDDEN, e.getMessage());
        } catch (IllegalArgumentException e) {
            response.sendError(HttpServletResponse.SC_NOT_FOUND, e.getMessage());
        } catch (SQLException e) {
            throw new ServletException("Lỗi truy vấn dữ liệu bài tập", e);
        }
    }

    /**
     * POST /workout/log  (workoutId, minutes) -> ghi log tập luyện
     */
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        Long userId = requireUserId(request, response);
        if (userId == null) {
            return;
        }

        if (!"/log".equals(request.getPathInfo())) {
            response.sendError(HttpServletResponse.SC_NOT_FOUND);
            return;
        }

        Long workoutId = parseLong(request.getParameter("workoutId"));
        Integer minutes = parseInt(request.getParameter("minutes"));
        if (workoutId == null || minutes == null) {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Thiếu hoặc sai tham số");
            return;
        }

        try {
            WorkoutLog log = workoutService.recordWorkout(userId, workoutId, minutes);
            response.sendRedirect(request.getContextPath()
                + "/workout/detail?id=" + workoutId
                + "&kcal=" + log.getEstimatedCalories());
        } catch (SecurityException e) {
            response.sendError(HttpServletResponse.SC_FORBIDDEN, e.getMessage());
        } catch (IllegalArgumentException e) {
            response.sendError(HttpServletResponse.SC_BAD_REQUEST, e.getMessage());
        } catch (SQLException e) {
            throw new ServletException("Lỗi ghi log tập luyện", e);
        }
    }

    // ---- helper ----

    /** Lấy userId từ session; chưa đăng nhập thì chuyển về /login và trả null. */
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
