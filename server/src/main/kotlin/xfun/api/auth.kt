package xfun.api

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.util.*
import kotlinx.serialization.json.*
import xfun.*
import xfun.core.*
import xfun.getDbPath
import xfun.utils.nowStr
import java.nio.file.Path
import kotlin.io.path.exists

// ---------------------------------------------------------------------------
// ApiPermission data class
// ---------------------------------------------------------------------------

data class ApiPermission(
    val token: String,
    val db: DB,
    val permission: DBPermission,
)

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------

suspend fun ApplicationCall.extractToken(): String {
    val authHeader = request.headers["Authorization"]
        ?: throw AuthException(HttpStatusCode.UnprocessableEntity, "Invalid authorization header. Must use Bearer scheme.")
    if (!authHeader.startsWith("Bearer ")) {
        throw AuthException(HttpStatusCode.UnprocessableEntity, "Invalid authorization header. Must use Bearer scheme.")
    }
    return authHeader.removePrefix("Bearer ")
}

suspend fun ApplicationCall.getApiPermission(allowInactive: Boolean = false): ApiPermission {
    val token = extractToken()
    val user = request.headers["User"]
        ?: throw AuthException(HttpStatusCode.UnprocessableEntity, "Missing User header")

    val dbPath = getDbPath(user)
    val existing = Path.of(dbPath).exists()
    val db = DB(dbPath)

    // ROOT_TOKEN bypass
    if (ROOT_TOKEN.isNotEmpty() && token == ROOT_TOKEN) {
        initDb(db)
        if (!existing) db.init()
        return ApiPermission(token, db, rootPermission(db))
    }

    if (!existing) {
        throw AuthException(HttpStatusCode.NotFound, "用户不存在")
    }

    initDb(db)

    // Look up token in _token table
    val rPerm = rootPermission(db)
    val tokenResults = db.withReadTransaction { conn ->
        val view: View = mutableMapOf()
        view["_token"] = mutableListOf(TableSpec(listOf("permission", "is_active", "expires_at"), Filter.Leaf(Condition("token", token, "="))))
        query(conn, rPerm, "_token", view, limit = 1)
    }

    if (tokenResults.isEmpty()) {
        throw AuthException(HttpStatusCode.Unauthorized, "无效或未知的 Token")
    }

    val tokenRow = tokenResults[0]
    val isActive = (tokenRow["is_active"] as? Number)?.toInt() ?: 0
    val expiresAt = tokenRow["expires_at"] as? String
    val permUuid = tokenRow["permission"] as? String

    if (isActive == 0) {
        if (allowInactive) return ApiPermission(token, db, noPermission(db))
        throw AuthException(HttpStatusCode.Unauthorized, "Token 已被停用")
    }

    if (expiresAt != null && expiresAt < nowStr()) {
        if (allowInactive) return ApiPermission(token, db, noPermission(db))
        throw AuthException(HttpStatusCode.Unauthorized, "Token 已过期")
    }

    // Look up permission
    val permResults = db.withReadTransaction { conn ->
        val view: View = mutableMapOf()
        view["_permission"] = mutableListOf(TableSpec(db.cols("_permission"), Filter.Leaf(Condition("uuid", permUuid, "="))))
        query(conn, rPerm, "_permission", view, limit = 1)
    }

    if (permResults.isEmpty()) {
        throw AuthException(HttpStatusCode.Unauthorized, "未知的权限标识")
    }

    val permRow = permResults[0]
    val readViewJson = Json.parseToJsonElement(permRow["read_view"] as String).jsonObject
    val writeViewJson = Json.parseToJsonElement(permRow["write_view"] as String).jsonObject
    val readView = parseViewJson(readViewJson)
    val writeView = parseViewJson(writeViewJson)

    return ApiPermission(token, db, readView to writeView)
}

suspend fun ApplicationCall.requireRootToken(): ApiPermission {
    val apiPerm = getApiPermission()
    if (apiPerm.token != ROOT_TOKEN) {
        throw AuthException(HttpStatusCode.Forbidden, "需要 ROOT_TOKEN 才能管理数据库")
    }
    return apiPerm
}

class AuthException(val statusCode: HttpStatusCode, message: String) : Exception(message)
