package xfun.service

import kotlinx.serialization.json.*
import xfun.*
import xfun.core.*
import xfun.utils.nowStr
import java.nio.file.Files
import java.nio.file.Path
import kotlin.io.path.exists
import kotlin.io.path.isRegularFile
import kotlin.streams.toList

/** GET /tables/{name}/entries 的查询参数（避免依赖 Ktor 的 queryParameters）。 */
data class QueryParams(
    val orderBy: String = "",
    val limit: Int = -1,
    val offset: Int = 0,
    val view: String = "",
    val filter: String = "",
)

/**
 * 传输无关的应用服务层：所有端点业务逻辑集中于此。
 * 每个方法用 (token, user, 已解析的入参) 作为输入，返回 [ApiResponse]，
 * 内部统一 try/catch 转错误响应。Ktor HTTP 与 Android JS 桥都只作薄适配调用它。
 */
object ApiService {

    // ------------------------------------------------------------------ tables

    fun listTables(token: String?, user: String?): ApiResponse = api {
        val p = resolveApiPermission(token, user)
        val arr = buildJsonArray {
            for ((name, cols) in p.db.tableInfos) {
                add(buildJsonObject {
                    put("table_name", JsonPrimitive(name))
                    put("columns", columnsToJson(cols))
                })
            }
        }
        ApiResponse(Http.OK, arr)
    }

    fun getSchema(token: String?, user: String?, name: String): ApiResponse = api {
        val p = resolveApiPermission(token, user)
        validateTable(p.db, name)
        ApiResponse(Http.OK, columnsToJson(p.db.tableInfos[name]!!))
    }

    fun queryEntries(token: String?, user: String?, name: String, q: QueryParams): ApiResponse = api {
        val p = resolveApiPermission(token, user)
        validateTable(p.db, name)

        var view: View = if (q.view.isNotEmpty()) {
            resolveView(p.db, p.permission, q.view)
        } else {
            mutableMapOf(name to mutableListOf(TableSpec(p.db.cols(name), Filter.TRUE)))
        }

        if (q.filter.isNotEmpty()) {
            val f = try {
                parseFilterJson(Json.parseToJsonElement(q.filter))
            } catch (e: Exception) {
                throw ApiError(Http.UNPROCESSABLE, "filter 不是合法 JSON: ${e.message}")
            }
            view = view.entries.associate { (t, specs) ->
                if (t == name) {
                    t to specs.map { (c, flt) -> TableSpec(c, Filter.OrGroups(listOf(listOf(flt, f)))) }.toMutableList()
                } else {
                    t to specs
                }
            }.toMutableMap()
        }

        val fv = view
        val (results, total) = p.db.withReadTransaction { conn ->
            val total = count(conn, p.permission, name, fv)
            val rs = query(conn, p.permission, name, fv, orderBy = q.orderBy, limit = q.limit, offset = q.offset)
            rs to total
        }
        ApiResponse(Http.OK, buildJsonObject {
            put("count", JsonPrimitive(total))
            put("results", resultsToJson(results))
        })
    }

    fun addEntries(token: String?, user: String?, name: String, body: JsonElement): ApiResponse = api {
        val p = resolveApiPermission(token, user)
        val entriesArr = body.jsonObject["entries"]?.jsonArray
            ?: throw ApiError(Http.UNPROCESSABLE, "缺少 entries 字段")
        val entries = entriesArr.map { jsonToMap(it.jsonObject) }
        validateTable(p.db, name)
        val results = p.db.withTransaction { conn -> add(conn, p.permission, name, entries) }
        ApiResponse(Http.CREATED, buildJsonObject {
            put("count", JsonPrimitive(results.size))
            put("results", resultsToJson(results))
        })
    }

    fun updateEntries(token: String?, user: String?, name: String, body: JsonElement): ApiResponse = api {
        val p = resolveApiPermission(token, user)
        val obj = body.jsonObject
        val filterElement = obj["filter"] ?: throw ApiError(Http.UNPROCESSABLE, "缺少 filter 字段")
        val valuesElement = obj["values"]?.jsonObject ?: throw ApiError(Http.UNPROCESSABLE, "缺少 values 字段")
        if (valuesElement.isEmpty()) throw ApiError(Http.UNPROCESSABLE, "values 不能为空")
        val filter = parseFilterJson(filterElement)
        val values = jsonToMap(valuesElement)
        validateTable(p.db, name)
        val results = p.db.withTransaction { conn -> update(conn, p.permission, name, filter, values) }
        ApiResponse(Http.OK, buildJsonObject {
            put("count", JsonPrimitive(results.size))
            put("results", resultsToJson(results))
        })
    }

    fun deleteEntries(token: String?, user: String?, name: String, body: JsonElement): ApiResponse = api {
        val p = resolveApiPermission(token, user)
        val filterElement = body.jsonObject["filter"] ?: throw ApiError(Http.UNPROCESSABLE, "缺少 filter 字段")
        val filter = parseFilterJson(filterElement)
        validateTable(p.db, name)
        val results = p.db.withTransaction { conn -> delete(conn, p.permission, name, filter) }
        ApiResponse(Http.OK, buildJsonObject {
            put("count", JsonPrimitive(results.size))
            put("results", resultsToJson(results))
        })
    }

    // ----------------------------------------------------------------------- db

    fun dbInit(token: String?, user: String?): ApiResponse = api {
        val p = requireRootPermission(token, user)
        initDb(p.db)
        p.db.init()
        ApiResponse(Http.OK, buildJsonObject { put("message", JsonPrimitive("数据库初始化完成")) })
    }

    fun dbBackup(token: String?, user: String?): ApiResponse = api {
        val p = requireRootPermission(token, user)
        val path = p.db.backup()
        ApiResponse(Http.OK, buildJsonObject { put("message", JsonPrimitive("备份完成: $path")) })
    }

    fun dbReset(token: String?, user: String?, body: JsonElement?): ApiResponse = api {
        val p = requireRootPermission(token, user)
        val backupFirst = body?.jsonObject?.get("backup_first")?.jsonPrimitive?.boolean ?: true
        if (backupFirst) p.db.backup()
        p.db.reset()
        ApiResponse(Http.OK, buildJsonObject { put("message", JsonPrimitive("数据库已重置")) })
    }

    fun dbRestore(token: String?, user: String?, body: JsonElement): ApiResponse = api {
        val p = requireRootPermission(token, user)
        val backupPath = body.jsonObject["backup_path"]?.jsonPrimitive?.content
            ?: throw ApiError(Http.UNPROCESSABLE, "缺少 backup_path 字段")
        val path = try {
            p.db.restore(backupPath)
        } catch (e: java.io.FileNotFoundException) {
            throw ApiError(Http.NOT_FOUND, e.message ?: "")
        }
        ApiResponse(Http.OK, buildJsonObject { put("message", JsonPrimitive("已从备份恢复: $path")) })
    }

    fun listBackups(token: String?, user: String?): ApiResponse = api {
        requireRootPermission(token, user)
        val backupDir = DATA_DIR.resolve("backups")
        val files = if (!backupDir.exists()) emptyList()
        else Files.list(backupDir).use { s ->
            s.filter { it.isRegularFile() }.map { it.toString() }.sorted().toList()
        }
        ApiResponse(Http.OK, buildJsonObject {
            put("backups", buildJsonArray { for (f in files) add(JsonPrimitive(f)) })
        })
    }

    // ------------------------------------------------------------------- tokens

    fun tokenInfo(token: String?, user: String?): ApiResponse = api {
        val p = resolveApiPermission(token, user, allowInactive = true)
        val perm = rootPermission(p.db)

        val row: Map<String, Any?> = if (p.token != ROOT_TOKEN) {
            val results = p.db.withReadTransaction { conn ->
                val cols = listOf("name", "shortcut", "shortcut_expire_at", "expires_at",
                    "created_at", "updated_at", "is_active")
                val view: View = mutableMapOf()
                view["_token"] = mutableListOf(TableSpec(cols, Filter.Leaf(Condition("token", p.token, "="))))
                query(conn, perm, "_token", view, limit = 1)
            }
            if (results.isEmpty()) throw ApiError(Http.NOT_FOUND, "Token 在鉴权后被删除")
            results[0]
        } else emptyMap()

        ApiResponse(Http.OK, buildJsonObject {
            put("name", JsonPrimitive(row["name"] as? String ?: "ROOT_TOKEN"))
            put("shortcut", row["shortcut"]?.let { JsonPrimitive(it as? String) } ?: JsonNull)
            put("shortcut_expire_at", row["shortcut_expire_at"]?.let { JsonPrimitive(it as? String) } ?: JsonNull)
            put("expires_at", row["expires_at"]?.let { JsonPrimitive(it as? String) } ?: JsonNull)
            put("created_at", row["created_at"]?.let { JsonPrimitive(it as? String) } ?: JsonNull)
            put("updated_at", row["updated_at"]?.let { JsonPrimitive(it as? String) } ?: JsonNull)
            put("is_active", JsonPrimitive((row["is_active"] as? Number)?.toInt()?.let { it != 0 } ?: true))
            put("read_view", viewToJson(p.permission.first))
            put("write_view", viewToJson(p.permission.second))
        })
    }

    /** POST /tokens/exchange：无需鉴权，凭一次性 shortcut 换正式 token。 */
    fun tokenExchange(user: String?, body: JsonElement): ApiResponse = api {
        val shortcut = body.jsonObject["shortcut"]?.jsonPrimitive?.content
            ?: throw ApiError(Http.UNPROCESSABLE, "缺少 shortcut 字段")
        if (user.isNullOrEmpty()) throw ApiError(Http.UNPROCESSABLE, "Missing User header")

        val dbPath = getDbPath(user)
        if (!Path.of(dbPath).exists()) throw ApiError(Http.NOT_FOUND, "用户不存在")

        val db = DB(dbPath)
        initDb(db)
        val perm = rootPermission(db)

        val token = db.withTransaction { conn ->
            val cols = db.cols("_token")
            val view: View = mutableMapOf()
            view["_token"] = mutableListOf(TableSpec(cols, Filter.Leaf(Condition("shortcut", shortcut, "="))))
            val results = query(conn, perm, "_token", view, limit = 1)
            if (results.isEmpty()) throw ApiError(Http.NOT_FOUND, "Shortcut 不存在或已被兑换")

            val row = results[0]
            val expireAt = row["shortcut_expire_at"] as? String
            if (expireAt != null && expireAt < nowStr()) throw ApiError(Http.GONE, "Shortcut 已过期")

            val tokenValue = row["token"] as String
            val rowId = row["id"] as String

            update(conn, perm, "_token",
                Filter.Leaf(Condition("id", rowId, "=")),
                mapOf("shortcut" to null, "shortcut_expire_at" to null))

            tokenValue
        }

        ApiResponse(Http.OK, buildJsonObject { put("token", JsonPrimitive(token)) })
    }

    // ------------------------------------------------------------------ helpers

    private fun validateTable(db: DB, table: String) {
        if (table !in db.tableInfos)
            throw ApiError(Http.NOT_FOUND, "未知表: '$table'，可用: ${db.tableInfos.keys}")
    }

    private fun resolveView(db: DB, permission: DBPermission, name: String): View {
        val results = db.withReadTransaction { conn ->
            val view: View = mutableMapOf()
            view["_view"] = mutableListOf(TableSpec(db.cols("_view"), Filter.Leaf(Condition("name", name, "="))))
            query(conn, permission, "_view", view, limit = 1)
        }
        if (results.isEmpty()) throw ApiError(Http.NOT_FOUND, "视图不存在: '$name'")
        return try {
            parseViewJson(Json.parseToJsonElement(results[0]["data"] as String).jsonObject)
        } catch (e: Exception) {
            throw ApiError(Http.UNPROCESSABLE, "视图数据无效: '$name'")
        }
    }
}

// ---------------------------------------------------------------------------
// 共享 JSON 序列化助手（HTTP 与 JS 桥都复用，保证响应体一致）
// ---------------------------------------------------------------------------

fun columnsToJson(cols: List<Column>): JsonArray = buildJsonArray {
    for (col in cols) add(buildJsonObject {
        put("name", JsonPrimitive(col.name))
        put("col_type", JsonPrimitive(col.colType))
        put("nullable", JsonPrimitive(col.nullable))
        put("primary_key", JsonPrimitive(col.primary_key))
        put("unique", JsonPrimitive(col.unique))
        put("index", JsonPrimitive(col.index))
        put("auto", JsonPrimitive(col.auto))
        put("default", if (col.default != null) JsonPrimitive(col.default.toString()) else JsonNull)
    })
}

fun resultsToJson(rows: List<Map<String, Any?>>): JsonArray = buildJsonArray {
    for (row in rows) add(mapToJson(row))
}

fun mapToJson(map: Map<String, Any?>): JsonObject = buildJsonObject {
    for ((k, v) in map) put(k, valueToJsonElement(v))
}

fun jsonToMap(obj: JsonObject): Map<String, Any?> = obj.mapValues { (_, v) -> jsonElementToValue(v) }
