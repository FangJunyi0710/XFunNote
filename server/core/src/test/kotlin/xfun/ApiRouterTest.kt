package xfun

import xfun.service.ApiRouter
import xfun.service.Http
import kotlin.test.Test
import kotlin.test.assertEquals

/**
 * 只验证路由匹配逻辑：token=null 时，任何"已知路由"都会命中对应 ApiService 方法并在鉴权处返回 422，
 * 而"未知路由/方法不匹配"才返回 404。这样无需真实数据库即可确认分发正确性。
 */
class ApiRouterTest {

    private fun d(method: String, path: String) =
        ApiRouter.dispatch(method, path, emptyMap(), null, null, null)

    @Test
    fun `已知路由命中ApiService返回422而非404`() {
        val routes = listOf(
            "GET" to "/api/v0/tables",
            "GET" to "/api/v0/tables/plan/schema",
            "GET" to "/api/v0/tables/plan/entries",
            "POST" to "/api/v0/tables/plan/entries",
            "PUT" to "/api/v0/tables/plan/entries",
            "DELETE" to "/api/v0/tables/plan/entries",
            "POST" to "/api/v0/db/init",
            "POST" to "/api/v0/db/backup",
            "POST" to "/api/v0/db/reset",
            "POST" to "/api/v0/db/restore",
            "GET" to "/api/v0/db/backups",
            "GET" to "/api/v0/tokens/info",
            "POST" to "/api/v0/tokens/exchange",
        )
        for ((m, p) in routes) {
            assertEquals(Http.UNPROCESSABLE, d(m, p).status, "$m $p 应命中端点(422 鉴权)，而非 404")
        }
    }

    @Test
    fun `未知路径返回404`() {
        assertEquals(Http.NOT_FOUND, d("GET", "/api/v0/nonexistent").status)
        assertEquals(Http.NOT_FOUND, d("GET", "/api/v0/tables/plan/unknown").status)
    }

    @Test
    fun `方法不匹配返回404`() {
        // /tables 只支持 GET；POST 落到未匹配分支
        assertEquals(Http.NOT_FOUND, d("POST", "/api/v0/tables").status)
        // schema 只支持 GET
        assertEquals(Http.NOT_FOUND, d("DELETE", "/api/v0/tables/plan/schema").status)
    }

    @Test
    fun `剥离前缀与保留前缀等价`() {
        // 去掉 /api/vN 前缀也应能匹配
        assertEquals(Http.UNPROCESSABLE, d("GET", "/tables").status)
    }
}
