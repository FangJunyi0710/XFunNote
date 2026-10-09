package xfun.api

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.*
import xfun.*
import xfun.core.DB
import java.nio.file.Files
import java.nio.file.Path
import kotlin.io.path.*
import kotlin.streams.toList

fun Route.manageDbRoutes() {

    // POST /db/init
    post("/db/init") {
        val apiPerm = call.requireRootToken()
        initDb(apiPerm.db)
        apiPerm.db.init()
        call.respond(buildJsonObject {
            put("message", JsonPrimitive("数据库初始化完成"))
        })
    }

    // POST /db/backup
    post("/db/backup") {
        val apiPerm = call.requireRootToken()
        val path = apiPerm.db.backup()
        call.respond(buildJsonObject {
            put("message", JsonPrimitive("备份完成: $path"))
        })
    }

    // POST /db/reset
    post("/db/reset") {
        val apiPerm = call.requireRootToken()
        val body = try { call.receive<JsonObject>() } catch (_: Exception) { buildJsonObject {} }
        val backupFirst = body["backup_first"]?.jsonPrimitive?.boolean ?: true
        if (backupFirst) apiPerm.db.backup()
        apiPerm.db.reset()
        call.respond(buildJsonObject {
            put("message", JsonPrimitive("数据库已重置"))
        })
    }

    // POST /db/restore
    post("/db/restore") {
        val apiPerm = call.requireRootToken()
        val body = call.receive<JsonObject>()
        val backupPath = body["backup_path"]?.jsonPrimitive?.content
            ?: throw AuthException(HttpStatusCode.UnprocessableEntity, "缺少 backup_path 字段")
        try {
            val path = apiPerm.db.restore(backupPath)
            call.respond(buildJsonObject {
                put("message", JsonPrimitive("已从备份恢复: $path"))
            })
        } catch (e: java.io.FileNotFoundException) {
            throw AuthException(HttpStatusCode.NotFound, e.message ?: "")
        }
    }

    // GET /db/backups
    get("/db/backups") {
        call.requireRootToken()
        val backupDir = DATA_DIR.resolve("backups")
        if (!backupDir.exists()) {
            call.respond(buildJsonObject {
                put("backups", buildJsonArray {})
            })
            return@get
        }
        val files = Files.list(backupDir).use { stream ->
            stream.filter { it.isRegularFile() }
                .map { it.toString() }
                .sorted()
                .toList()
        }
        call.respond(buildJsonObject {
            put("backups", buildJsonArray {
                for (f in files) add(JsonPrimitive(f))
            })
        })
    }
}
