package xfun

import java.nio.file.Path
import java.nio.file.Paths

const val VERSION = "0.1.0"

val PROJECT_ROOT: Path = Paths.get("").toAbsolutePath().normalize()

fun resolveDataDir(): Path {
    val env = System.getenv("XFUN_DATA_DIR")
    return if (!env.isNullOrBlank()) Paths.get(env) else PROJECT_ROOT.resolve("data")
}

/**
 * 运行期可注入的应用配置。
 * - 桌面/Linux：用默认值（env XFUN_DATA_DIR / CWD、env ROOT_TOKEN），行为与重构前一致。
 * - Android：进程启动时（服务器/桥开始服务前）用 Context 覆盖：
 *     AppConfig.dataDir = File(context.filesDir, "data").toPath()
 *     AppConfig.rootToken = <本机生成的 bootstrap token>
 * 注意：默认值只计算路径对象、不做任何 I/O，避免 Android 上按 env/CWD 误建目录。
 */
object AppConfig {
    var dataDir: Path = resolveDataDir()
    var rootToken: String = System.getenv("ROOT_TOKEN") ?: ""
}

// 兼容既有引用：读取当前 AppConfig（可在启动时被覆盖）。
// 实际目录创建下沉到 DB.createConnection（按 dbPath 的父目录创建），此处不再 eager mkdir。
val DATA_DIR: Path get() = AppConfig.dataDir
val ROOT_TOKEN: String get() = AppConfig.rootToken

val SSL_CERT_PATH: String = System.getenv("SSL_CERT_PATH") ?: ""
val SSL_KEY_PATH: String = System.getenv("SSL_KEY_PATH") ?: ""

val SHOW_DOCS: Boolean = (System.getenv("SHOW_DOCS") ?: "false").equals("true", ignoreCase = true)
val BACKEND_PORT: Int = (System.getenv("BACKEND_PORT") ?: "8000").toInt()

val VITE_HTTP_PORT: Int = (System.getenv("VITE_HTTP_PORT") ?: "80").toInt()
val VITE_HTTPS_PORT: Int = (System.getenv("VITE_HTTPS_PORT") ?: "443").toInt()

val PID_FILE: Path get() = AppConfig.dataDir.resolve(".xfunnote.pid")
val LOG_FILE: Path get() = AppConfig.dataDir.resolve(".xfunnote.log")
