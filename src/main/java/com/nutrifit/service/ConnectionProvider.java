package com.nutrifit.service;

import java.sql.Connection;
import java.sql.SQLException;

/** Package-local connection seam for isolated tests; production uses DatabaseConfig. */
@FunctionalInterface
interface ConnectionProvider {
    Connection open() throws SQLException;
}
