package xfun.service

import kotlinx.serialization.json.*
import xfun.*
import xfun.core.*
import xfun.utils.nowStr
import java.nio.file.Path
import kotlin.io.path.exists

/** 鉴权结果：token + 已初始化的 DB + 读写权限对。 */
data class ApiPermission(
    val token: String,
    val db: DB,
    val permission: DBPermission,
)

/**
 * 传输无关鉴权。仅需 token / user 两个字符串——
 * HTTP 传输从请求头取，Android JS 桥从参数取。
 *
 * @param allowInactive 为 true 时，停用/过期 Token 返回空权限而非报错（供 /tokens/info 查询自身状态）
 */
fun resolveApiPermission(token: String?, user: String?, allowInactive: Boolean = false): ApiPermission {
    if (token.isNullOrEmpty())
        throw ApiError(Http.UNPROCESSABLE, "Invalid authorization header. Must use Bearer scheme.")
    if (user.isNullOrEmpty())
        throw ApiError(Http.UNPROCESSABLE, "Missing User header")

    val dbPath = getDbPath(user)
    val existing = Path.of(dbPath).exists()
    val db = DB(dbPath)

    // ROOT_TOKEN 直通：可创建/初始化数据库
    if (ROOT_TOKEN.isNotEmpty() && token == ROOT_TOKEN) {
        initDb(db)
        if (!existing) db.init()
        return ApiPermission(token, db, rootPermission(db))
    }

    if (!existing) throw ApiError(Http.NOT_FOUND, "用户不存在")

    initDb(db)

    val rPerm = rootPermission(db)

    // 查 _token 表
    val tokenResults = db.withReadTransaction { conn ->
        val view: View = mutableMapOf()
        view["_token"] = mutableListOf(
            TableSpec(listOf("permission", "is_active", "expires_at"), Filter.Leaf(Condition("token", token, "=")))
        )
        query(conn, rPerm, "_token", view, limit = 1)
    }
    if (tokenResults.isEmpty()) throw ApiError(Http.UNAUTHORIZED, "无效或未知的 Token")

    val tokenRow = tokenResults[0]
    val isActive = (tokenRow["is_active"] as? Number)?.toInt() ?: 0
    val expiresAt = tokenRow["expires_at"] as? String
    val permUuid = tokenRow["permission"] as? String

    if (isActive == 0) {
        if (allowInactive) return ApiPermission(token, db, noPermission(db))
        throw ApiError(Http.UNAUTHORIZED, "Token 已被停用")
    }
    if (expiresAt != null && expiresAt < nowStr()) {
        if (allowInactive) return ApiPermission(token, db, noPermission(db))
        throw ApiError(Http.UNAUTHORIZED, "Token 已过期")
    }

    // 查 _permission 表
    val permResults = db.withReadTransaction { conn ->
        val view: View = mutableMapOf()
        view["_permission"] = mutableListOf(TableSpec(db.cols("_permission"), Filter.Leaf(Condition("uuid", permUuid, "="))))
        query(conn, rPerm, "_permission", view, limit = 1)
    }
    if (permResults.isEmpty()) throw ApiError(Http.UNAUTHORIZED, "未知的权限标识")

    val permRow = permResults[0]
    val readView = parseViewJson(Json.parseToJsonElement(permRow["read_view"] as String).jsonObject)
    val writeView = parseViewJson(Json.parseToJsonElement(permRow["write_view"] as String).jsonObject)

    return ApiPermission(token, db, readView to writeView)
}

/** 需要 ROOT_TOKEN 的操作（数据库管理 /db 系列路由）。 */
fun requireRootPermission(token: String?, user: String?): ApiPermission {
    val p = resolveApiPermission(token, user)
    if (p.token != ROOT_TOKEN) throw ApiError(Http.FORBIDDEN, "需要 ROOT_TOKEN 才能管理数据库")
    return p
}
