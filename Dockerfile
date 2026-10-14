# ---------- 构建阶段 ----------
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /build

# 先只拷 pom，利用镜像层缓存复用依赖
COPY pom.xml .
RUN mvn -B -q -DskipTests dependency:go-offline || true

COPY src ./src
RUN mvn -B -q clean package -DskipTests

# ---------- 运行阶段 ----------
FROM eclipse-temurin:21-jre
WORKDIR /app

# 非 root 运行
RUN groupadd --system app && useradd --system --gid app app
COPY --from=build /build/target/diet-agent-1.0-SNAPSHOT.jar /app/app.jar
USER app

ENV TZ=Asia/Shanghai \
    JAVA_OPTS=""
EXPOSE 8080

ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar /app/app.jar"]
