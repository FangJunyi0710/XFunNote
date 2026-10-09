package xfun.api

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.*
import xfun.*
import xfun.core.*

fun Route.tablesRoutes() {

    // GET /tables
    get("/tables") {
        val apiPerm = call.getApiPermission()
        val result = buildJsonArray {
            for ((name, cols) in apiPerm.db.tableInfos) {
                add(buildJsonObject {
                    put("table_name", JsonPrimitive(name))
                    put("columns", buildJsonArray {
                        for (col in cols) {
                            add(buildJsonObject {
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
                    })
                })
            }
        }
        call.respond(result)
    }

    // GET /tables/{name}/schema
    get("/tables/{name}/schema") {
        val apiPerm = call.getApiPermission()
        val name = call.parameters["name"]!!
        validateTable(apiPerm.db, name)

        val result = buildJsonArray {
            for (col in apiPerm.db.tableInfos[name]!!) {
                add(buildJsonObject {
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
        }
        call.respond(result)
    }

    // GET /tables/{name}/entries
    get("/tables/{name}/entries") {
        val apiPerm = call.getApiPermission()
        val name = call.parameters["name"]!!
        val orderBy = call.request.queryParameters["order_by"] ?: ""
        val limit = call.request.queryParameters["limit"]?.toInt() ?: -1
        val offset = call.request.queryParameters["offset"]?.toInt() ?: 0
        val viewName = call.request.queryParameters["view"] ?: ""
        val filterParam = call.request.queryParameters["filter"] ?: ""

        validateTable(apiPerm.db, name)

        var view: View? = if (viewName.isNotEmpty()) {
            resolveView(apiPerm.db, apiPerm.permission, viewName)
        } else null

        if (view == null) {
            view = mutableMapOf(name to mutableListOf(TableSpec(apiPerm.db.cols(name), Filter.TRUE)))
        }

        var filter: Filter? = null
        if (filterParam.isNotEmpty()) {
            try {
                val jsonElement = Json.parseToJsonElement(filterParam)
                filter = parseFilterJson(jsonElement)
            } catch (e: Exception) {
                throw AuthException(HttpStatusCode.UnprocessableEntity, "filter 不是合法 JSON: ${e.message}")
            }
        }

        if (filter != null) {
            val f = filter
            view = view.entries.associate { (t, specs) ->
                if (t == name) {
                    t to specs.map { (cols, flt) ->
                        TableSpec(cols, Filter.OrGroups(listOf(listOf(flt, f))))
                    }.toMutableList()
                } else {
                    t to specs
                }
            }.toMutableMap()
        }

        val (results, total) = apiPerm.db.withReadTransaction { conn ->
            val total = count(conn, apiPerm.permission, name, view)
            val results = query(conn, apiPerm.permission, name, view,
                orderBy = orderBy, limit = limit, offset = offset)
            results to total
        }

        call.respond(buildJsonObject {
            put("count", JsonPrimitive(total))
            put("results", buildJsonArray {
                for (row in results) {
                    add(mapToJson(row))
                }
            })
        })
    }

    // POST /tables/{name}/entries
    post("/tables/{name}/entries") {
        val apiPerm = call.getApiPermission()
        val name = call.parameters["name"]!!
        val body = call.receive<JsonObject>()
        val entriesArr = body["entries"]?.jsonArray
            ?: throw AuthException(HttpStatusCode.UnprocessableEntity, "缺少 entries 字段")
        val entries = entriesArr.map { jsonToMap(it.jsonObject) }

        validateTable(apiPerm.db, name)

        val results = apiPerm.db.withTransaction { conn ->
            add(conn, apiPerm.permission, name, entries)
        }

        call.respond(
            HttpStatusCode.Created,
            buildJsonObject {
                put("count", JsonPrimitive(results.size))
                put("results", buildJsonArray {
                    for (row in results) add(mapToJson(row))
                })
            }
        )
    }

    // PUT /tables/{name}/entries
    put("/tables/{name}/entries") {
        val apiPerm = call.getApiPermission()
        val name = call.parameters["name"]!!
        val body = call.receive<JsonObject>()
        val filterElement = body["filter"]
            ?: throw AuthException(HttpStatusCode.UnprocessableEntity, "缺少 filter 字段")
        val valuesElement = body["values"]?.jsonObject
            ?: throw AuthException(HttpStatusCode.UnprocessableEntity, "缺少 values 字段")

        if (valuesElement.isEmpty()) {
            throw AuthException(HttpStatusCode.UnprocessableEntity, "values 不能为空")
        }

        val filter = parseFilterJson(filterElement)
        val values = jsonToMap(valuesElement)

        validateTable(apiPerm.db, name)

        val results = apiPerm.db.withTransaction { conn ->
            update(conn, apiPerm.permission, name, filter, values)
        }

        call.respond(buildJsonObject {
            put("count", JsonPrimitive(results.size))
            put("results", buildJsonArray {
                for (row in results) add(mapToJson(row))
            })
        })
    }

    // DELETE /tables/{name}/entries
    delete("/tables/{name}/entries") {
        val apiPerm = call.getApiPermission()
        val name = call.parameters["name"]!!
        val body = call.receive<JsonObject>()
        val filterElement = body["filter"]
            ?: throw AuthException(HttpStatusCode.UnprocessableEntity, "缺少 filter 字段")
        val filter = parseFilterJson(filterElement)

        validateTable(apiPerm.db, name)

        val results = apiPerm.db.withTransaction { conn ->
            delete(conn, apiPerm.permission, name, filter)
        }

        call.respond(buildJsonObject {
            put("count", JsonPrimitive(results.size))
            put("results", buildJsonArray {
                for (row in results) add(mapToJson(row))
            })
        })
    }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

private fun validateTable(db: DB, table: String) {
    if (table !in db.tableInfos) {
        throw AuthException(HttpStatusCode.NotFound, "未知表: '$table'，可用: ${db.tableInfos.keys}")
    }
}

private fun resolveView(db: DB, permission: DBPermission, name: String): View {
    val results = db.withReadTransaction { conn ->
        val view: View = mutableMapOf()
        view["_view"] = mutableListOf(TableSpec(db.cols("_view"), Filter.Leaf(Condition("name", name, "="))))
        query(conn, permission, "_view", view, limit = 1)
    }
    if (results.isEmpty()) {
        throw AuthException(HttpStatusCode.NotFound, "视图不存在: '$name'")
    }
    try {
        val data = results[0]["data"] as String
        return parseViewJson(Json.parseToJsonElement(data).jsonObject)
    } catch (e: Exception) {
        throw AuthException(HttpStatusCode.UnprocessableEntity, "视图数据无效: '$name'")
    }
}

fun mapToJson(map: Map<String, Any?>): JsonObject {
    return buildJsonObject {
        for ((k, v) in map) {
            put(k, valueToJsonElement(v))
        }
    }
}

fun jsonToMap(obj: JsonObject): Map<String, Any?> {
    return obj.mapValues { (_, v) -> jsonElementToValue(v) }
}
