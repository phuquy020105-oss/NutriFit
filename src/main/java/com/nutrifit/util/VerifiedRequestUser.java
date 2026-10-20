package com.nutrifit.util;
import com.nutrifit.dao.UserDAO;
import com.nutrifit.model.User;
import jakarta.servlet.http.*;
import java.sql.SQLException;
import java.util.Optional;

/** Current DB identity, reused ONLY in this request, independent of annotation filter order. */
public final class VerifiedRequestUser {
    private static final String KEY=VerifiedRequestUser.class.getName();
    private record Verified(long id,long version,Optional<User> user) { }
    private VerifiedRequestUser() { }
    public static Optional<User> find(HttpServletRequest request,UserDAO users)throws SQLException {
        HttpSession session=request.getSession(false);
        if(session==null || !(session.getAttribute("userId") instanceof Long id)
                || !(session.getAttribute("authVersion") instanceof Long version))return Optional.empty();
        if(request.getAttribute(KEY) instanceof Verified known && known.id()==id && known.version()==version)
            return known.user();
        Optional<User> found=users.findById(id).filter(u->id.equals(u.getUserId())&&u.getAuthVersion()==version);
        request.setAttribute(KEY,new Verified(id,version,found));
        return found;
    }
}
