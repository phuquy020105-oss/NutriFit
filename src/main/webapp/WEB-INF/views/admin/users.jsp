
<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.util.List" %>
<%@ page import="com.nutrifit.model.User" %>
<%!
    private String escapeHtml(String value) {
        if (value == null) return "";
        return value.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;")
                .replace("'", "&#39;");
    }
%>
<%
    String contextPath = request.getContextPath();

    @SuppressWarnings("unchecked")
    List<User> users =
            (List<User>) request.getAttribute("users");

    String keyword =
            (String) request.getAttribute("keyword");

    String result =
            (String) request.getAttribute("result");

    Long currentUserId =
            (Long) session.getAttribute("userId");
%>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1">
    <title>Quản lý người dùng - NutriFit</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            background: #f4f7f5;
            font-family: Arial, sans-serif;
            color: #24352b;
        }
        header {
            padding: 22px 30px;
            background: #176b45;
            color: white;
        }
        header a {
            color: white;
            text-decoration: none;
        }
        main {
            max-width: 1200px;
            margin: 30px auto;
            padding: 0 18px;
        }
        .search {
            display: flex;
            gap: 10px;
            margin: 20px 0;
        }
        input, select, button {
            padding: 10px;
            border: 1px solid #d7e0d9;
            border-radius: 7px;
        }
        .search input { flex: 1; }
        button {
            background: #176b45;
            color: white;
            border: 0;
            cursor: pointer;
        }
        .table-wrap {
            overflow-x: auto;
            background: white;
            border-radius: 12px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 14px;
            text-align: left;
            border-bottom: 1px solid #edf0ed;
        }
        th { background: #e8f3ec; }
        .role-form {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .message {
            padding: 13px;
            background: #e3f4e9;
            border-radius: 8px;
            margin: 15px 0;
        }
        .muted { color: #758279; }
    </style>
</head>
<body>
<header>
    <h2>NutriFit — Quản lý người dùng</h2>
    <a href="<%= contextPath %>/admin">← Về Dashboard</a>
</header>

<main>
    <h2>Danh sách tài khoản</h2>

    <% if ("updated".equals(result)) { %>
        <div class="message">Đã cập nhật quyền thành công.</div>
    <% } else if ("unchanged".equals(result)) { %>
        <div class="message">Vai trò tài khoản không thay đổi.</div>
    <% } %>

    <form class="search"
          method="get"
          action="<%= contextPath %>/admin/users">
        <input type="search" name="q"
               maxlength="100"
               placeholder="Tìm theo tên hoặc email"
               value="<%= escapeHtml(keyword) %>">
        <button type="submit">Tìm kiếm</button>
    </form>

    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Họ tên</th>
                    <th>Email</th>
                    <th>Vai trò</th>
                    <th>Gói</th>
                    <th>Thao tác</th>
                </tr>
            </thead>
            <tbody>
            <% if (users == null || users.isEmpty()) { %>
                <tr>
                    <td colspan="6">Không có tài khoản phù hợp.</td>
                </tr>
            <% } else {
                for (User user : users) {
                    boolean isSelf =
                            currentUserId != null
                            && currentUserId.equals(user.getUserId());
            %>
                <tr>
                    <td><%= user.getUserId() %></td>
                    <td><%= escapeHtml(user.getFullName()) %></td>
                    <td><%= escapeHtml(user.getEmail()) %></td>
                    <td><%= user.getRole() %></td>
                    <td><%= user.getSubscriptionStatus() %></td>
                    <td>
                        <% if (isSelf) { %>
                            <span class="muted">
                                Tài khoản hiện tại
                            </span>
                        <% } else { %>
                            <form class="role-form"
                                  method="post"
                                  action="<%= contextPath %>/admin/users/change-role">
                                <input type="hidden"
                                       name="_csrf"
                                       value="${sessionScope.csrfToken}">
                                <input type="hidden"
                                       name="userId"
                                       value="<%= user.getUserId() %>">
                                <select name="role">
                                    <option value="USER"
                                        <%= "USER".equals(user.getRole().name())
                                                ? "selected" : "" %>>
                                        USER
                                    </option>
                                    <option value="ADMIN"
                                        <%= "ADMIN".equals(user.getRole().name())
                                                ? "selected" : "" %>>
                                        ADMIN
                                    </option>
                                </select>
                                <button type="submit">
                                    Lưu
                                </button>
                            </form>
                        <% } %>
                    </td>
                </tr>
            <%  }
               } %>
            </tbody>
        </table>
    </div>
    <p class="muted">
        Hiển thị tối đa 100 tài khoản mỗi lần tìm kiếm.
    </p>
</main>
</body>
</html>
