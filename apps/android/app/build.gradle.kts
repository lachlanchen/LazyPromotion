plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
}

android {
    namespace = "art.lazying.promotion.preview"
    compileSdk = 36
    defaultConfig {
        applicationId = "art.lazying.promotion.preview"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
    }
    buildFeatures { compose = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    sourceSets["main"].assets.srcDir("../../shared")
    sourceSets["test"].resources.srcDir("../../shared")
    packaging { resources.excludes += "/META-INF/{AL2.0,LGPL2.1}" }
}

// This is a local debug preview, not a signed customer release.
gradle.taskGraph.whenReady {
    check(allTasks.none { it.project == project && it.name.contains("release", ignoreCase = true) }) {
        "Release disabled: complete product, privacy and device qualification first."
    }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2025.09.00"))
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")
    testImplementation("junit:junit:4.13.2")
}
