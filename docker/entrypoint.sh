#!/bin/sh
set -eu

PORT="${PORT:-8080}"
case "$PORT" in
    *[!0-9]*|'')
        printf '%s\n' 'PORT must be an integer between 1 and 65535.' >&2
        exit 1
        ;;
esac
if [ "${#PORT}" -gt 5 ] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    printf '%s\n' 'PORT must be an integer between 1 and 65535.' >&2
    exit 1
fi

if [ -n "${NUTRIFIT_DB_CA_FILE:-}" ] && [ ! -r "$NUTRIFIT_DB_CA_FILE" ]; then
    printf '%s\n' 'NUTRIFIT_DB_CA_FILE must identify a readable mounted CA certificate.' >&2
    exit 1
fi

# server.xml resolves Java system properties, not the PORT environment variable.
CATALINA_OPTS="${CATALINA_OPTS:-} -Dnutrifit.http.port=$PORT"
export CATALINA_OPTS
exec "$CATALINA_HOME/bin/catalina.sh" run
