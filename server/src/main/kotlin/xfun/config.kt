package xfun

import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import kotlin.io.path.*

const val VERSION = "0.1.0"

val PROJECT_ROOT: Path = Paths.get("").toAbsolutePath().normalize()

fun resolveDataDir(): Path {
    val env = System.getenv("XFUN_DATA_DIR")
    return if (!env.isNullOrBlank()) Paths.get(env) else PROJECT_ROOT.resolve("data")
}

val DATA_DIR: Path = resolveDataDir().also { Files.createDirectories(it) }

val SSL_CERT_PATH: String = System.getenv("SSL_CERT_PATH") ?: ""
val SSL_KEY_PATH: String = System.getenv("SSL_KEY_PATH") ?: ""

val SHOW_DOCS: Boolean = (System.getenv("SHOW_DOCS") ?: "false").equals("true", ignoreCase = true)
val BACKEND_PORT: Int = (System.getenv("BACKEND_PORT") ?: "8000").toInt()

val VITE_HTTP_PORT: Int = (System.getenv("VITE_HTTP_PORT") ?: "80").toInt()
val VITE_HTTPS_PORT: Int = (System.getenv("VITE_HTTPS_PORT") ?: "443").toInt()

val ROOT_TOKEN: String = System.getenv("ROOT_TOKEN") ?: ""

val PID_FILE: Path = DATA_DIR.resolve(".xfunnote.pid")
val LOG_FILE: Path = DATA_DIR.resolve(".xfunnote.log")
