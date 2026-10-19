// :core —— 传输无关的可复用库（Android 与桌面 app 都依赖它）。
// 关键：不含任何 io.ktor；sqlite 驱动不在这里依赖（db.kt 只用 java.sql，驱动由运行端提供）。
plugins {
    kotlin("jvm")
    kotlin("plugin.serialization")
    `java-library`
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

dependencies {
    // 对外暴露（api）：ApiResponse/ApiRouter 的签名用到 JsonElement，消费方需可见
    api("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")

    testImplementation(kotlin("test"))
}

tasks.test {
    useJUnitPlatform()
}
