package xfun

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.cio.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.server.plugins.cors.routing.*
import io.ktor.server.plugins.defaultheaders.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.json.*
import xfun.api.*
import java.nio.file.Files
import java.nio.file.Path
import kotlin.io.path.*

val API_PREFIX = "/api/v${VERSION.split(".")[0]}"

fun main() {
    val port = BACKEND_PORT
    val staticDir = PROJECT_ROOT.resolve("frontend").resolve("dist")

    println("Starting XFunNote server on port $port...")
    embeddedServer(CIO, port = port) {
        configureServer()
    }.start(wait = true)
}

fun Application.configureServer() {
    install(DefaultHeaders) {
        header("X-Frame-Options", "SAMEORIGIN")
        header("X-Content-Type-Options", "nosniff")
        header("Referrer-Policy", "strict-origin-when-cross-origin")
    }
    install(ContentNegotiation) {
        json(Json {
            prettyPrint = false
            isLenient = false
            ignoreUnknownKeys = true
            encodeDefaults = true
        })
    }
    install(CORS) {
        // No cross-origin allowed by default
        allowHost("localhost")
    }

    configureErrorHandling()

    routing {
        route(API_PREFIX) {
            tablesRoutes()
            manageDbRoutes()
            tokensRoutes()
        }

        // Static file serving + SPA fallback
        // Ktor 的 tailcard 语法为 "/{...}"，匹配任意剩余路径（含多级子目录与根路径）
        val distDir = PROJECT_ROOT.resolve("frontend").resolve("dist")
        get("/{...}") { serveStatic(call, distDir) }
    }
}

private suspend fun serveStatic(call: ApplicationCall, distDir: Path) {
    val path = call.request.local.uri
    if (path.startsWith("/api")) {
        call.respond(HttpStatusCode.NotFound)
        return
    }

    val index = distDir.resolve("index.html")
    if (!index.exists()) {
        call.respond(HttpStatusCode.NotFound, "前端未构建，请先执行 vite build")
        return
    }

    val relPath = path.trimStart('/').split("?")[0]
    val candidate = distDir.resolve(relPath).normalize()

    if (relPath.isNotEmpty() && candidate.isRegularFile() && candidate.startsWith(distDir)) {
        val contentType = guessContentType(candidate.toString())
        val bytes = Files.readAllBytes(candidate)
        call.respondBytes(bytes, ContentType.parse(contentType))
    } else {
        val bytes = Files.readAllBytes(index)
        call.respondBytes(bytes, ContentType.Text.Html.withParameter("charset", "utf-8"))
    }
}

private fun guessContentType(path: String): String {
    return when {
        path.endsWith(".html") -> "text/html; charset=utf-8"
        path.endsWith(".js") -> "application/javascript"
        path.endsWith(".mjs") -> "application/javascript"
        path.endsWith(".css") -> "text/css"
        path.endsWith(".json") -> "application/json"
        path.endsWith(".png") -> "image/png"
        path.endsWith(".jpg") || path.endsWith(".jpeg") -> "image/jpeg"
        path.endsWith(".svg") -> "image/svg+xml"
        path.endsWith(".ico") -> "image/x-icon"
        path.endsWith(".woff") -> "font/woff"
        path.endsWith(".woff2") -> "font/woff2"
        path.endsWith(".ttf") -> "font/ttf"
        path.endsWith(".wasm") -> "application/wasm"
        path.endsWith(".map") -> "application/json"
        else -> "application/octet-stream"
    }
}
