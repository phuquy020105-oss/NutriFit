
package com.nutrifit.controller;

import com.nutrifit.config.DatabaseConfig;
import jakarta.servlet.annotation.WebServlet;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import java.io.IOException;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;

@WebServlet("/health/db")
public class DatabaseHealthServlet extends HttpServlet {

    @Override
    protected void doGet(
            HttpServletRequest request,
            HttpServletResponse response
    ) throws IOException {

        response.setContentType("application/json;charset=UTF-8");

        try (
            Connection conn = DatabaseConfig.getConnection();
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery("SELECT DATABASE()")
        ) {
            rs.next();

            response.getWriter().write(
                "{\"status\":\"connected\",\"database\":\""
                + rs.getString(1) + "\"}"
            );

        } catch (Exception e) {
            getServletContext().log("Database check failed", e);

            response.setStatus(503);
            response.getWriter().write(
                "{\"status\":\"error\","
                + "\"message\":\"Database unavailable\"}"
            );
        }
    }
}
