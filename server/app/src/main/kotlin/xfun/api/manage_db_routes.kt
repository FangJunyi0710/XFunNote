package xfun.api

import io.ktor.server.request.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.JsonObject
import xfun.service.ApiService

// 数据库管理路由（均需 ROOT_TOKEN）：薄壳委托 ApiService。
fun Route.manageDbRoutes() {

    post("/db/init") {
        call.respondApi(ApiService.dbInit(call.bearerToken(), call.userHeader()))
    }

    post("/db/backup") {
        call.respondApi(ApiService.dbBackup(call.bearerToken(), call.userHeader()))
    }

    post("/db/reset") {
        val body = try { call.receive<JsonObject>() } catch (_: Exception) { null }
        call.respondApi(ApiService.dbReset(call.bearerToken(), call.userHeader(), body))
    }

    post("/db/restore") {
        val body = call.receive<JsonObject>()
        call.respondApi(ApiService.dbRestore(call.bearerToken(), call.userHeader(), body))
    }

    get("/db/backups") {
        call.respondApi(ApiService.listBackups(call.bearerToken(), call.userHeader()))
    }
}
