package xfun.api

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.*
import xfun.core.*
import xfun.getDbPath
import xfun.initDb
import xfun.utils.nowStr
import java.nio.file.Path
import kotlin.io.path.exists

fun Route.tokensRoutes() {

    // GET /tokens/info
    get("/tokens/info") {
        val apiPerm = call.getApiPermission(allowInactive = true)
        val perm = rootPermission(apiPerm.db)

        val row: Map<String, Any?> = if (apiPerm.token != xfun.ROOT_TOKEN) {
            val results = apiPerm.db.withReadTransaction { conn ->
                val cols = listOf("name", "shortcut", "shortcut_expire_at", "expires_at",
                    "created_at", "updated_at", "is_active")
                val view: View = mutableMapOf()
                view["_token"] = mutableListOf(TableSpec(cols, Filter.Leaf(Condition("token", apiPerm.token, "="))))
                query(conn, perm, "_token", view, limit = 1)
            }
            if (results.isEmpty()) {
                throw AuthException(HttpStatusCode.NotFound, "Token 在鉴权后被删除")
            }
            results[0]
        } else {
            emptyMap()
        }

        val readViewJson = viewToJson(apiPerm.permission.first)
        val writeViewJson = viewToJson(apiPerm.permission.second)

        call.respond(buildJsonObject {
            put("name", JsonPrimitive(row["name"] as? String ?: "ROOT_TOKEN"))
            put("shortcut", row["shortcut"]?.let { JsonPrimitive(it as? String) } ?: JsonNull)
            put("shortcut_expire_at", row["shortcut_expire_at"]?.let { JsonPrimitive(it as? String) } ?: JsonNull)
            put("expires_at", row["expires_at"]?.let { JsonPrimitive(it as? String) } ?: JsonNull)
            put("created_at", row["created_at"]?.let { JsonPrimitive(it as? String) } ?: JsonNull)
            put("updated_at", row["updated_at"]?.let { JsonPrimitive(it as? String) } ?: JsonNull)
            put("is_active", JsonPrimitive((row["is_active"] as? Number)?.toInt()?.let { it != 0 } ?: true))
            put("read_view", readViewJson)
            put("write_view", writeViewJson)
        })
    }

    // POST /tokens/exchange (no auth required)
    post("/tokens/exchange") {
        val body = call.receive<JsonObject>()
        val shortcut = body["shortcut"]?.jsonPrimitive?.content
            ?: throw AuthException(HttpStatusCode.UnprocessableEntity, "缺少 shortcut 字段")
        val user = call.request.headers["User"]
            ?: throw AuthException(HttpStatusCode.UnprocessableEntity, "Missing User header")

        val dbPath = getDbPath(user)
        if (!Path.of(dbPath).exists()) {
            throw AuthException(HttpStatusCode.NotFound, "用户不存在")
        }

        val db = DB(dbPath)
        xfun.initDb(db)
        val perm = rootPermission(db)

        val result = db.withTransaction { conn ->
            val cols = db.cols("_token")
            val view: View = mutableMapOf()
            view["_token"] = mutableListOf(TableSpec(cols, Filter.Leaf(Condition("shortcut", shortcut, "="))))
            val results = query(conn, perm, "_token", view, limit = 1)

            if (results.isEmpty()) {
                throw AuthException(HttpStatusCode.NotFound, "Shortcut 不存在或已被兑换")
            }

            val row = results[0]
            val expireAt = row["shortcut_expire_at"] as? String
            if (expireAt != null && expireAt < nowStr()) {
                throw AuthException(HttpStatusCode.Gone, "Shortcut 已过期")
            }

            val tokenValue = row["token"] as String
            val rowId = row["id"] as String

            // Clear shortcut (one-time use)
            update(conn, perm, "_token",
                Filter.Leaf(Condition("id", rowId, "=")),
                mapOf("shortcut" to null, "shortcut_expire_at" to null))

            tokenValue
        }

        call.respond(buildJsonObject {
            put("token", JsonPrimitive(result))
        })
    }
}
