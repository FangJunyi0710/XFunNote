package xfun.api

import io.ktor.server.request.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.JsonObject
import xfun.service.ApiService
import xfun.service.QueryParams

// 表相关路由：全部为薄壳——解析 HTTP 入参 → 调 ApiService → respondApi。
fun Route.tablesRoutes() {

    get("/tables") {
        call.respondApi(ApiService.listTables(call.bearerToken(), call.userHeader()))
    }

    get("/tables/{name}/schema") {
        val name = call.parameters["name"]!!
        call.respondApi(ApiService.getSchema(call.bearerToken(), call.userHeader(), name))
    }

    get("/tables/{name}/entries") {
        val name = call.parameters["name"]!!
        val qp = call.request.queryParameters
        val q = QueryParams(
            orderBy = qp["order_by"] ?: "",
            limit = qp["limit"]?.toIntOrNull() ?: -1,
            offset = qp["offset"]?.toIntOrNull() ?: 0,
            view = qp["view"] ?: "",
            filter = qp["filter"] ?: "",
        )
        call.respondApi(ApiService.queryEntries(call.bearerToken(), call.userHeader(), name, q))
    }

    post("/tables/{name}/entries") {
        val name = call.parameters["name"]!!
        val body = call.receive<JsonObject>()
        call.respondApi(ApiService.addEntries(call.bearerToken(), call.userHeader(), name, body))
    }

    put("/tables/{name}/entries") {
        val name = call.parameters["name"]!!
        val body = call.receive<JsonObject>()
        call.respondApi(ApiService.updateEntries(call.bearerToken(), call.userHeader(), name, body))
    }

    delete("/tables/{name}/entries") {
        val name = call.parameters["name"]!!
        val body = call.receive<JsonObject>()
        call.respondApi(ApiService.deleteEntries(call.bearerToken(), call.userHeader(), name, body))
    }
}
