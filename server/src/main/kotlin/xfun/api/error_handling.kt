package xfun.api

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.plugins.statuspages.*
import io.ktor.server.response.*
import kotlinx.serialization.json.*
import xfun.core.*
import java.sql.SQLException

fun Application.configureErrorHandling() {
    install(StatusPages) {
        exception<AuthException> { call, cause ->
            call.respond(
                cause.statusCode,
                buildJsonObject {
                    put("error", JsonPrimitive(cause.statusCode.description))
                    put("detail", JsonPrimitive(cause.message ?: ""))
                }
            )
        }

        exception<XFunError> { call, cause ->
            call.respond(
                HttpStatusCode.UnprocessableEntity,
                buildJsonObject {
                    put("error", JsonPrimitive("Unprocessable Content"))
                    put("detail", JsonPrimitive(cause.message ?: ""))
                }
            )
        }

        exception<SQLException> { call, cause ->
            val msg = cause.message ?: ""
            when {
                "UNIQUE constraint failed" in msg -> {
                    call.respond(
                        HttpStatusCode.Conflict,
                        buildJsonObject {
                            put("error", JsonPrimitive("Conflict"))
                            put("detail", JsonPrimitive("数据已存在: $msg"))
                        }
                    )
                }
                "NOT NULL constraint failed" in msg -> {
                    call.respond(
                        HttpStatusCode.UnprocessableEntity,
                        buildJsonObject {
                            put("error", JsonPrimitive("Unprocessable Content"))
                            put("detail", JsonPrimitive("缺少必填字段: $msg"))
                        }
                    )
                }
                else -> {
                    call.respond(
                        HttpStatusCode.BadRequest,
                        buildJsonObject {
                            put("error", JsonPrimitive("Bad Request"))
                            put("detail", JsonPrimitive("数据完整性错误: $msg"))
                        }
                    )
                }
            }
        }

        exception<UsernameInvalidError> { call, cause ->
            call.respond(
                HttpStatusCode.UnprocessableEntity,
                buildJsonObject {
                    put("error", JsonPrimitive("Unprocessable Content"))
                    put("detail", JsonPrimitive(cause.message ?: ""))
                }
            )
        }

        exception<Throwable> { call, _ ->
            call.respond(
                HttpStatusCode.InternalServerError,
                buildJsonObject {
                    put("error", JsonPrimitive("Internal Server Error"))
                }
            )
        }
    }
}
