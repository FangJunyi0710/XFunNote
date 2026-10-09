package xfun.core

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.boolean
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.longOrNull

// ---------------------------------------------------------------------------
// Filter type — recursive structure: outer OR, inner AND, leaf = Condition
// ---------------------------------------------------------------------------

sealed class Filter {
    data class Leaf(val condition: Condition) : Filter()
    data class Negated(val inner: Filter, val negate: Boolean) : Filter()
    data class OrGroups(val groups: List<List<Filter>>) : Filter()

    companion object {
        val TRUE: Filter = OrGroups(listOf(emptyList()))
        val FALSE: Filter = OrGroups(emptyList())
    }
}

// ---------------------------------------------------------------------------
// Condition
// ---------------------------------------------------------------------------

data class Condition(val col: String, val value: Any?, val op: String = "=") {

    fun toSql(): Pair<String, List<Any?>> {
        Column.check(col)
        val handler = opRegistry[op] ?: throw FilterInvalidError(this)
        return handler(col, value, op)
    }

    companion object {
        internal val opRegistry = mutableMapOf<String, (String, Any?, String) -> Pair<String, List<Any?>>>()

        fun registerOps() {
            // Called eagerly to populate the registry
            register("=") { col, value, op -> builtinSql(col, value, op) }
            register("!=") { col, value, op -> builtinSql(col, value, op) }
            register(">") { col, value, op -> builtinSql(col, value, op) }
            register("<") { col, value, op -> builtinSql(col, value, op) }
            register(">=") { col, value, op -> builtinSql(col, value, op) }
            register("<=") { col, value, op -> builtinSql(col, value, op) }
            register("LIKE") { col, value, op -> builtinSql(col, value, op) }
            register("NOT LIKE") { col, value, op -> builtinSql(col, value, op) }
            register("IN") { col, value, op -> builtinSql(col, value, op) }
            register("NOT IN") { col, value, op -> builtinSql(col, value, op) }
            register("BETWEEN") { col, value, op -> builtinSql(col, value, op) }
            register("GLOB") { col, value, op -> builtinSql(col, value, op) }
            register("NOT GLOB") { col, value, op -> builtinSql(col, value, op) }
        }

        private fun register(op: String, handler: (String, Any?, String) -> Pair<String, List<Any?>>) {
            opRegistry[op] = handler
        }

        private fun builtinSql(column: String, value: Any?, op: String): Pair<String, List<Any?>> {
            // NULL handling: only = and != can handle NULL
            if (value == null) {
                if (op == "=") return "$column IS NULL" to emptyList()
                if (op == "!=") return "$column IS NOT NULL" to emptyList()
                throw FilterInvalidError(Condition(column, value, op))
            }

            // IN / NOT IN
            if (op in listOf("IN", "NOT IN")) {
                val list = value as? List<*> ?: throw FilterInvalidError(Condition(column, value, op))
                val deduped = list.distinct()
                if (deduped.isEmpty()) {
                    return if (op == "IN") "1=0" to emptyList() else "1=1" to emptyList()
                }
                val placeholders = deduped.joinToString(", ") { "?" }
                return "$column $op ($placeholders)" to deduped
            }

            // BETWEEN
            if (op == "BETWEEN") {
                val list = value as? List<*> ?: throw FilterInvalidError(Condition(column, value, op))
                if (list.size != 2) throw FilterInvalidError(Condition(column, value, op))
                if (list[0] == null || list[1] == null) return "1=0" to emptyList()
                return "$column BETWEEN ? AND ?" to listOf(list[0], list[1])
            }

            // General: =, >, <, >=, <=, !=, LIKE, NOT LIKE, GLOB, NOT GLOB
            return "$column $op ?" to listOf(value)
        }
    }
}

// Initialize operators
private object FilterInit {
    init { Condition.registerOps() }
}
private val _filterInit = FilterInit

// ---------------------------------------------------------------------------
// filter_to_sql
// ---------------------------------------------------------------------------

fun filterToSql(filter: Filter): Pair<String, List<Any?>> {
    return when (filter) {
        is Filter.Leaf -> {
            val (sql, vals) = filter.condition.toSql()
            if (sql.isNotEmpty()) sql to vals else "1=0" to emptyList()
        }
        is Filter.Negated -> {
            val (clause, vals) = filterToSql(filter.inner)
            if (filter.negate) "NOT ($clause)" to vals else clause to vals
        }
        is Filter.OrGroups -> {
            if (filter.groups.isEmpty()) return "1=0" to emptyList()

            val orClauses = mutableListOf<String>()
            val params = mutableListOf<Any?>()

            for (group in filter.groups) {
                val andClauses = mutableListOf<String>()
                for (item in group) {
                    val (clause, vals) = filterToSql(item)
                    andClauses.add("($clause)")
                    params.addAll(vals)
                }
                if (andClauses.isEmpty()) {
                    andClauses.add("1=1")
                }
                orClauses.add("(" + andClauses.joinToString(" AND ") + ")")
            }

            if (orClauses.isEmpty()) return "1=0" to emptyList()
            orClauses.joinToString(" OR ") to params
        }
    }
}

// ---------------------------------------------------------------------------
// parse_filter_json — from kotlinx.serialization JsonElement
// ---------------------------------------------------------------------------

fun parseFilterJson(element: JsonElement): Filter {
    return when (element) {
        is JsonObject -> {
            val col = element["col"]!!.jsonPrimitive.content
            val op = element["op"]?.jsonPrimitive?.content ?: "="
            val valElement = element["val"]!!
            val value = jsonElementToValue(valElement)
            Filter.Leaf(Condition(col, value, op))
        }
        is JsonArray -> {
            if (element.size == 2 && element[1] is JsonPrimitive) {
                val prim = element[1] as JsonPrimitive
                val negate = prim.booleanOrNull ?: throw FilterInvalidError(element)
                val inner = parseFilterJson(element[0])
                Filter.Negated(inner, negate)
            } else {
                val groups = element.map { group ->
                    val groupArr = group as? JsonArray
                        ?: throw FilterInvalidError(element)
                    groupArr.map { parseFilterJson(it) }
                }
                Filter.OrGroups(groups)
            }
        }
        else -> throw FilterInvalidError(element)
    }
}

// ---------------------------------------------------------------------------
// filter_to_json — to kotlinx.serialization JsonElement
// ---------------------------------------------------------------------------

fun filterToJson(filter: Filter): JsonElement {
    return when (filter) {
        is Filter.Leaf -> {
            val c = filter.condition
            buildJsonObject {
                put("col", JsonPrimitive(c.col))
                put("val", valueToJsonElement(c.value))
                put("op", JsonPrimitive(c.op))
            }
        }
        is Filter.Negated -> {
            buildJsonArray {
                add(filterToJson(filter.inner))
                add(JsonPrimitive(filter.negate))
            }
        }
        is Filter.OrGroups -> {
            buildJsonArray {
                for (group in filter.groups) {
                    add(buildJsonArray {
                        for (item in group) {
                            add(filterToJson(item))
                        }
                    })
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// JSON value conversion helpers
// ---------------------------------------------------------------------------

fun jsonElementToValue(element: JsonElement): Any? {
    return when (element) {
        is JsonNull -> null
        is JsonPrimitive -> {
            if (element.isString) element.content
            else {
                val content = element.content
                element.intOrNull
                    ?: element.longOrNull
                    ?: element.doubleOrNull
                    ?: content
            }
        }
        is JsonArray -> element.map { jsonElementToValue(it) }
        is JsonObject -> element.mapValues { jsonElementToValue(it.value) }
    }
}

fun valueToJsonElement(value: Any?): JsonElement {
    return when (value) {
        null -> JsonNull
        is String -> JsonPrimitive(value)
        is Int -> JsonPrimitive(value)
        is Long -> JsonPrimitive(value)
        is Double -> JsonPrimitive(value)
        is Float -> JsonPrimitive(value.toDouble())
        is Boolean -> JsonPrimitive(value)
        is List<*> -> buildJsonArray {
            for (item in value) add(valueToJsonElement(item))
        }
        is Map<*, *> -> buildJsonObject {
            for ((k, v) in value) put(k.toString(), valueToJsonElement(v))
        }
        else -> JsonPrimitive(value.toString())
    }
}
