package xfun.api

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.response.*
import xfun.service.ApiResponse

// HTTP 传输专用的取值辅助：仅负责把 Ktor 请求头拆成纯字符串交给 service 层。
// 缺失/非法 token 一律返回 null，由 service 统一按契约报错（与 JS 桥行为一致）。

/** 从 Authorization 头解析 Bearer token；不符合 "Bearer xxx" 则返回 null。 */
fun ApplicationCall.bearerToken(): String? =
    request.headers["Authorization"]
        ?.takeIf { it.startsWith("Bearer ") }
        ?.removePrefix("Bearer ")

/** User 头（决定操作哪个用户数据库）。 */
fun ApplicationCall.userHeader(): String? = request.headers["User"]

/** 把传输无关的 ApiResponse 渲染为 HTTP 响应。 */
suspend fun ApplicationCall.respondApi(r: ApiResponse) {
    respond(HttpStatusCode.fromValue(r.status), r.body)
}
