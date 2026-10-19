# syntax=docker/dockerfile:1
FROM maven:3.9.16-eclipse-temurin-21 AS build
WORKDIR /build
COPY pom.xml ./
COPY src/main/ ./src/main/
RUN mvn --batch-mode --no-transfer-progress -Dmaven.test.skip=true package

FROM tomcat:10.1.61-jdk21-temurin-noble
ENV PORT=8080 \
    CATALINA_OPTS="-XX:MaxRAMPercentage=60.0 -XX:InitialRAMPercentage=10.0 -Duser.timezone=Asia/Ho_Chi_Minh -Dfile.encoding=UTF-8"
WORKDIR /usr/local/tomcat
# Run the application as an unprivileged user; all runtime files are ephemeral.
RUN groupadd --system --gid 10001 nutrifit \
    && useradd --system --uid 10001 --gid nutrifit --home-dir /usr/local/tomcat --shell /usr/sbin/nologin nutrifit \
    && rm -rf /usr/local/tomcat/webapps.dist \
    && chown -R nutrifit:nutrifit /usr/local/tomcat
COPY --chown=10001:10001 docker/server.xml conf/server.xml
COPY --chmod=755 docker/entrypoint.sh /usr/local/bin/nutrifit-entrypoint
COPY --from=build --chown=10001:10001 /build/target/nutrifit.war webapps/nutrifit.war
USER 10001:10001
EXPOSE 8080
STOPSIGNAL SIGTERM
ENTRYPOINT ["/usr/local/bin/nutrifit-entrypoint"]
