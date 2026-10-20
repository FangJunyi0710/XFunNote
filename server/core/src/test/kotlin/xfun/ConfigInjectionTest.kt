package xfun

import java.nio.file.Files
import java.nio.file.Paths
import kotlin.io.path.pathString
import kotlin.test.Test
import kotlin.test.assertEquals

/**
 * 验证配置可注入：切换 AppConfig 后，依赖 DATA_DIR / ROOT_TOKEN 的逻辑立即反映新值。
 * 每个用例在 finally 中恢复原值，避免污染其他测试。
 */
class ConfigInjectionTest {

    @Test
    fun `注入 dataDir 后 getDbPath 指向新目录`() {
        val saved = AppConfig.dataDir
        try {
            val tmp = Files.createTempDirectory("xfun-cfg-")
            AppConfig.dataDir = tmp
            assertEquals(tmp.resolve("alice.db").pathString, getDbPath("alice"))
        } finally {
            AppConfig.dataDir = saved
        }
    }

    @Test
    fun `DATA_DIR 委托读取当前 AppConfig`() {
        val saved = AppConfig.dataDir
        try {
            AppConfig.dataDir = Paths.get("/tmp/xfun-delegate-check")
            assertEquals("/tmp/xfun-delegate-check", DATA_DIR.toString())
        } finally {
            AppConfig.dataDir = saved
        }
    }

    @Test
    fun `rootToken 可注入并被动态读取`() {
        val saved = AppConfig.rootToken
        try {
            AppConfig.rootToken = "injected-token-xyz"
            assertEquals("injected-token-xyz", ROOT_TOKEN)
        } finally {
            AppConfig.rootToken = saved
        }
    }
}
