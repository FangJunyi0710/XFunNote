package xfun.core

import kotlinx.serialization.json.*

// ---------------------------------------------------------------------------
// View type definitions
// ---------------------------------------------------------------------------

data class TableSpec(val cols: List<String>, val filter: Filter)

typealias View = MutableMap<String, MutableList<TableSpec>>

fun newView(): View = mutableMapOf()

// ---------------------------------------------------------------------------
// view_to_sql
// ---------------------------------------------------------------------------

fun viewToSql(view: View, db: DB, table: String): Pair<String, List<Any?>> {
    if (table !in view || table !in db.tableInfos) return "" to emptyList()

    Column.check(table)
    val subSqls = mutableListOf<String>()
    val params = mutableListOf<Any?>()

    val baseSelect = db.selectSql(table, emptyList())
    subSqls.add("SELECT rowid, ${baseSelect.removePrefix("SELECT ")} WHERE 1=0")

    for ((cols, flt) in view[table]!!) {
        val (clause, vals) = filterToSql(flt)
        val select = db.selectSql(table, cols)
        subSqls.add("SELECT rowid, ${select.removePrefix("SELECT ")} WHERE $clause")
        params.addAll(vals)
    }

    val maxCols = db.cols(table).joinToString(", ") { "MAX($it) AS $it" }
    val unionAll = subSqls.joinToString(" UNION ALL ")
    val sql = "SELECT $maxCols FROM ($unionAll) AS combined GROUP BY rowid"
    return sql to params
}

// ---------------------------------------------------------------------------
// view_to_json / parse_view_json
// ---------------------------------------------------------------------------

fun viewToJson(view: View): JsonObject {
    return buildJsonObject {
        for ((tableName, specs) in view) {
            put(tableName, buildJsonArray {
                for ((cols, flt) in specs) {
                    add(buildJsonArray {
                        add(buildJsonArray {
                            for (col in cols) add(JsonPrimitive(col))
                        })
                        add(filterToJson(flt))
                    })
                }
            })
        }
    }
}

fun parseViewJson(obj: JsonObject): View {
    val result: View = mutableMapOf()
    for ((tableName, specsElement) in obj) {
        val specsArr = specsElement.jsonArray
        val specs = mutableListOf<TableSpec>()
        for (specElement in specsArr) {
            val specArr = specElement.jsonArray
            val cols = specArr[0].jsonArray.map { it.jsonPrimitive.content }
            val flt = parseFilterJson(specArr[1])
            specs.add(TableSpec(cols, flt))
        }
        result[tableName] = specs.toMutableList()
    }
    return result
}

// ---------------------------------------------------------------------------
// View algebra
// ---------------------------------------------------------------------------

fun viewOr(view1: View, view2: View): View {
    val tables = view1.keys + view2.keys
    val merged: View = mutableMapOf()
    for (table in tables) {
        val specs = mutableListOf<TableSpec>()
        view1[table]?.let { specs.addAll(it) }
        view2[table]?.let { specs.addAll(it) }
        merged[table] = specs
    }
    return merged
}

fun tableSpecAnd(spec1: TableSpec, spec2: TableSpec): TableSpec {
    val cols = (spec1.cols.toSet() intersect spec2.cols.toSet()).toList()
    val flt = Filter.OrGroups(listOf(listOf(spec1.filter, spec2.filter)))
    return TableSpec(cols, flt)
}

fun viewAnd(view1: View, view2: View): View {
    val tables = view1.keys intersect view2.keys
    val merged: View = mutableMapOf()
    for (table in tables) {
        val specs = mutableListOf<TableSpec>()
        for (spec1 in view1[table]!!) {
            for (spec2 in view2[table]!!) {
                specs.add(tableSpecAnd(spec1, spec2))
            }
        }
        merged[table] = specs
    }
    return merged
}

// ---------------------------------------------------------------------------
// Permission-based view cleaning
// ---------------------------------------------------------------------------

typealias DBPermission = Pair<View, View> // (readView, writeView)

private fun cleanEntry(entry: Map<String, Any?>, allowedColumns: Set<String>): Map<String, Any?> {
    val result = mutableMapOf<String, Any?>()
    for ((col, value) in entry) {
        if (col == "id") continue
        if (col in allowedColumns) result[col] = value
    }
    return result
}

fun viewCleanAdd(view: View, table: String, entries: List<Map<String, Any?>>): List<Map<String, Any?>> {
    if (table !in view) return emptyList()
    val allowedCols = view[table]!!.flatMap { (cols, _) -> cols }.toSet()
    return entries.map { cleanEntry(it, allowedCols) }
}

fun viewCleanDelete(view: View, table: String, filter: Filter): Filter {
    if (table !in view) return Filter.FALSE
    val idFilters = view[table]!!
        .filter { (cols, _) -> "id" in cols }
        .map { (_, flt) -> listOf(flt) }
    return Filter.OrGroups(listOf(listOf(filter, Filter.OrGroups(idFilters))))
}

fun viewCleanUpdate(view: View, table: String, filter: Filter, values: Map<String, Any?>): List<Pair<Filter, Map<String, Any?>>> {
    if (table !in view) return emptyList()
    val result = mutableListOf<Pair<Filter, Map<String, Any?>>>()
    for ((cols, flt) in view[table]!!) {
        val combinedFilter = Filter.OrGroups(listOf(listOf(flt, filter)))
        result.add(combinedFilter to cleanEntry(values, cols.toSet()))
    }
    return result
}

// ---------------------------------------------------------------------------
// Full / no view helpers
// ---------------------------------------------------------------------------

fun fullView(db: DB): View {
    val view: View = mutableMapOf()
    for ((tableName, cols) in db.tableInfos) {
        view[tableName] = mutableListOf(TableSpec(cols.map { it.name }, Filter.TRUE))
    }
    return view
}

fun noView(db: DB): View {
    val view: View = mutableMapOf()
    for (tableName in db.tableInfos.keys) {
        view[tableName] = mutableListOf(TableSpec(emptyList(), Filter.FALSE))
    }
    return view
}

fun rootPermission(db: DB): DBPermission = fullView(db) to fullView(db)
fun noPermission(db: DB): DBPermission = noView(db) to noView(db)

// ---------------------------------------------------------------------------
// validate_view
// ---------------------------------------------------------------------------

fun validateView(data: String) {
    try {
        val obj = Json.parseToJsonElement(data).jsonObject
        val view = parseViewJson(obj)
        for ((table, specs) in view) {
            Column.check(table)
            for ((cols, flt) in specs) {
                for (col in cols) Column.check(col)
                filterToSql(flt)
            }
        }
    } catch (e: Exception) {
        throw EntryInvalidError("_view", "data 不是有效的 View JSON: ${e.message}")
    }
}
