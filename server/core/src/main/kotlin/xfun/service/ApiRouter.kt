package xfun.service

import kotlinx.serialization.json.*

/**
 * 框架无关的 API 分发器：把 (method, path, query, body, token, user) 映射到对应 [ApiService] 方法。
 *
 * 用途：Android JS 桥（@JavascriptInterface）拿到前端 request() 发来的请求后调用它，
 * 从而与 Ktor HTTP 路由共用同一套 [ApiService] 业务逻辑，响应逐字节一致。
 * 不含任何 io.ktor 依赖，可被 Android 端安全引用。
 */
object ApiRouter {

    fun dispatch(
        method: String,
        path: String,
        query: Map<String, String>,
        body: JsonElement?,
        token: String?,
        user: String?,
    ): ApiResponse {
        // 去掉查询串与前导斜杠；剥离 /api/vN 前缀
        var seg = path.substringBefore('?').trimStart('/').split('/')
        if (seg.size >= 2 && seg[0] == "api") seg = seg.drop(2)
        val m = method.uppercase()

        return try {
            when {
                seg == listOf("tables") && m == "GET" ->
                    ApiService.listTables(token, user)

                seg.size == 3 && seg[0] == "tables" && seg[2] == "schema" && m == "GET" ->
                    ApiService.getSchema(token, user, seg[1])

                seg.size == 3 && seg[0] == "tables" && seg[2] == "entries" -> when (m) {
                    "GET" -> ApiService.queryEntries(token, user, seg[1], queryFrom(query))
                    "POST" -> ApiService.addEntries(token, user, seg[1], requireBody(body))
                    "PUT" -> ApiService.updateEntries(token, user, seg[1], requireBody(body))
                    "DELETE" -> ApiService.deleteEntries(token, user, seg[1], requireBody(body))
                    else -> notFound()
                }

                seg == listOf("db", "init") && m == "POST" -> ApiService.dbInit(token, user)
                seg == listOf("db", "backup") && m == "POST" -> ApiService.dbBackup(token, user)
                seg == listOf("db", "reset") && m == "POST" -> ApiService.dbReset(token, user, body)
                seg == listOf("db", "restore") && m == "POST" -> ApiService.dbRestore(token, user, requireBody(body))
                seg == listOf("db", "backups") && m == "GET" -> ApiService.listBackups(token, user)

                seg == listOf("tokens", "info") && m == "GET" -> ApiService.tokenInfo(token, user)
                seg == listOf("tokens", "exchange") && m == "POST" -> ApiService.tokenExchange(user, requireBody(body))

                else -> notFound()
            }
        } catch (e: Throwable) {
            errorToResponse(e)
        }
    }

    private fun queryFrom(q: Map<String, String>) = QueryParams(
        orderBy = q["order_by"] ?: "",
        limit = q["limit"]?.toIntOrNull() ?: -1,
        offset = q["offset"]?.toIntOrNull() ?: 0,
        view = q["view"] ?: "",
        filter = q["filter"] ?: "",
    )

    private fun requireBody(body: JsonElement?): JsonElement =
        body ?: throw ApiError(Http.UNPROCESSABLE, "缺少请求体")

    private fun notFound(): ApiResponse =
        ApiResponse(Http.NOT_FOUND, buildJsonObject {
            put("error", JsonPrimitive("Not Found"))
            put("detail", JsonPrimitive("未知路由"))
        })
}
