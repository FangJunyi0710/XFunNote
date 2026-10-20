package xfun.service

import kotlinx.serialization.json.*
import xfun.core.XFunError
import java.sql.SQLException

// ---------------------------------------------------------------------------
// 传输无关的 API 结果模型（Ktor HTTP 与 Android JS 桥都产出/消费同样的结构）
// ---------------------------------------------------------------------------

/** 一次 API 调用的结果：状态码 + JSON 响应体。 */
data class ApiResponse(val status: Int, val body: JsonElement)

/** 业务错误：携带 HTTP 语义的状态码，但不依赖任何网络框架。 */
class ApiError(val status: Int, message: String) : Exception(message)

/** 本项目用到的 HTTP 状态码常量与 reason phrase（替代 io.ktor.http.HttpStatusCode）。 */
object Http {
    const val OK = 200
    const val CREATED = 201
    const val BAD_REQUEST = 400
    const val UNAUTHORIZED = 401
    const val FORBIDDEN = 403
    const val NOT_FOUND = 404
    const val CONFLICT = 409
    const val GONE = 410
    const val UNPROCESSABLE = 422
    const val INTERNAL = 500

    fun phrase(status: Int): String = when (status) {
        OK -> "OK"
        CREATED -> "Created"
        BAD_REQUEST -> "Bad Request"
        UNAUTHORIZED -> "Unauthorized"
        FORBIDDEN -> "Forbidden"
        NOT_FOUND -> "Not Found"
        CONFLICT -> "Conflict"
        GONE -> "Gone"
        UNPROCESSABLE -> "Unprocessable Content"
        INTERNAL -> "Internal Server Error"
        else -> "Error"
    }
}

private fun errorJson(error: String, detail: String? = null): JsonObject = buildJsonObject {
    put("error", JsonPrimitive(error))
    if (detail != null) put("detail", JsonPrimitive(detail))
}

/**
 * 异常 → ApiResponse。映射规则与原 Ktor StatusPages 完全一致，
 * 保证 HTTP 传输与 JS 桥传输下错误响应体逐字节相同。
 */
fun errorToResponse(e: Throwable): ApiResponse = when (e) {
    is ApiError -> ApiResponse(e.status, errorJson(Http.phrase(e.status), e.message ?: ""))
    // XFunError 及其子类（EntryInvalid / SQLInvalid / FilterInvalid / UsernameInvalid）统一 422
    is XFunError -> ApiResponse(Http.UNPROCESSABLE, errorJson("Unprocessable Content", e.message ?: ""))
    is SQLException -> {
        val msg = e.message ?: ""
        when {
            "UNIQUE constraint failed" in msg ->
                ApiResponse(Http.CONFLICT, errorJson("Conflict", "数据已存在: $msg"))
            "NOT NULL constraint failed" in msg ->
                ApiResponse(Http.UNPROCESSABLE, errorJson("Unprocessable Content", "缺少必填字段: $msg"))
            else ->
                ApiResponse(Http.BAD_REQUEST, errorJson("Bad Request", "数据完整性错误: $msg"))
        }
    }
    else -> ApiResponse(Http.INTERNAL, errorJson("Internal Server Error"))
}

/** 在服务方法外层统一捕获异常，转成 ApiResponse。 */
inline fun api(block: () -> ApiResponse): ApiResponse =
    try {
        block()
    } catch (e: Throwable) {
        errorToResponse(e)
    }
