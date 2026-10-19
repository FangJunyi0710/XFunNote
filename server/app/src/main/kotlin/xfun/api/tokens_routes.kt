package xfun.api

import io.ktor.server.request.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.JsonObject
import xfun.service.ApiService

// Token 路由：薄壳委托 ApiService。
fun Route.tokensRoutes() {

    get("/tokens/info") {
        call.respondApi(ApiService.tokenInfo(call.bearerToken(), call.userHeader()))
    }

    // 无需鉴权：凭一次性 shortcut 换正式 token
    post("/tokens/exchange") {
        val body = call.receive<JsonObject>()
        call.respondApi(ApiService.tokenExchange(call.userHeader(), body))
    }
}
