// :app —— 桌面/Docker 的 Ktor HTTP 壳，依赖 :core，打 fat jar。
plugins {
    kotlin("jvm")
    application
    id("com.gradleup.shadow")
}

group = "com.xfunnote"
version = "0.1.0"

repositories {
    mavenCentral()
}

java {
    toolchain {
        languageVersion.set(JavaLanguageVersion.of(21))
    }
}

kotlin {
    jvmToolchain(21)
}

// 与 :core 一致，产物降到 Java 17 字节码。
tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile>().configureEach {
    compilerOptions.jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
}
tasks.withType<JavaCompile>().configureEach {
    options.release.set(17)
}

application {
    mainClass.set("xfun.MainKt")
}

val ktorVersion = "3.0.1"

dependencies {
    implementation(project(":core"))

    implementation("io.ktor:ktor-server-core:$ktorVersion")
    implementation("io.ktor:ktor-server-cio:$ktorVersion")
    implementation("io.ktor:ktor-server-content-negotiation:$ktorVersion")
    implementation("io.ktor:ktor-serialization-kotlinx-json:$ktorVersion")
    implementation("io.ktor:ktor-server-cors:$ktorVersion")
    implementation("io.ktor:ktor-server-status-pages:$ktorVersion")
    implementation("io.ktor:ktor-server-default-headers:$ktorVersion")

    // SQLite 驱动仅在桌面运行时提供；Android 端用 Willena fork（各自 runtime 依赖，:core 不关心）
    runtimeOnly("org.xerial:sqlite-jdbc:3.47.0.0")
}

tasks.named<com.github.jengelman.gradle.plugins.shadow.tasks.ShadowJar>("shadowJar") {
    archiveBaseName.set("xfunnote-server")
    archiveClassifier.set("all")
    mergeServiceFiles()
    manifest {
        attributes(mapOf("Main-Class" to "xfun.MainKt"))
    }
}
