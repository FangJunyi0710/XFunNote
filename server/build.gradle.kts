// 根工程只声明插件版本（apply false），由 :core / :app 各自应用。
plugins {
    kotlin("jvm") version "2.0.21" apply false
    kotlin("plugin.serialization") version "2.0.21" apply false
    id("com.gradleup.shadow") version "8.3.5" apply false
}
