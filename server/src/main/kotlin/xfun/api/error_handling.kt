package xfun.api

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.response.*
import xfun.service.errorToResponse

// 兜底错误处理：正常情况下 ApiService 已在内部把异常转成 ApiResponse，
// 这里仅捕获极个别逃逸异常（如 body 解析失败），复用同一套映射保证行为一致。
fun Application.configureErrorHandling() {
    install(StatusPages) {
        exception<Throwable> { call, cause ->
            val r = errorToResponse(cause)
            call.respond(HttpStatusCode.fromValue(r.status), r.body)
        }
    }
}
