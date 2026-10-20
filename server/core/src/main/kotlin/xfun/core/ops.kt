package xfun.core

// ---------------------------------------------------------------------------
// CRUD operations with permission enforcement
// ---------------------------------------------------------------------------

fun query(
    conn: ConnWrapper,
    permission: DBPermission,
    table: String,
    queryView: View,
    orderBy: String = "",
    limit: Int = -1,
    offset: Int = 0,
): List<Map<String, Any?>> {
    val (rView, _) = permission
    val (sql, params) = viewToSql(viewAnd(queryView, rView), conn.db, table)
    if (sql.isEmpty()) return emptyList()

    val parts = mutableListOf(sql)
    if (orderBy.isNotEmpty()) {
        Column.checkOrderBy(orderBy)
        parts.add("ORDER BY $orderBy")
    }
    parts.add("LIMIT $limit OFFSET $offset")
    val fullSql = parts.joinToString(" ")
    val rs = conn.execute(fullSql, params)
    return conn.fetchAll(rs)
}

fun count(conn: ConnWrapper, permission: DBPermission, table: String, queryView: View): Int {
    val (rView, _) = permission
    val (sql, params) = viewToSql(viewAnd(queryView, rView), conn.db, table)
    if (sql.isEmpty()) return 0
    val countSql = "SELECT COUNT(*) FROM ($sql) AS cnt"
    val rs = conn.execute(countSql, params)
    val rows = conn.fetchAll(rs)
    return (rows[0].values.first() as Number).toInt()
}

private fun queryByIds(
    conn: ConnWrapper,
    permission: DBPermission,
    table: String,
    ids: List<String>,
): List<Map<String, Any?>> {
    val view: View = mutableMapOf()
    view[table] = mutableListOf(TableSpec(conn.db.cols(table), Filter.Leaf(Condition("id", ids, "IN"))))
    return query(conn, permission, table, view)
}

fun add(
    conn: ConnWrapper,
    permission: DBPermission,
    table: String,
    entries: List<Map<String, Any?>>,
): List<Map<String, Any?>> {
    val (_, wView) = permission
    val cleaned = viewCleanAdd(wView, table, entries)
    @Suppress("UNCHECKED_CAST")
    val mutableEntries = cleaned.map { it.toMutableMap() }.toMutableList() as MutableList<Map<String, Any?>>
    val ids = conn.db.addEntries(conn, table, mutableEntries)
    return queryByIds(conn, permission, table, ids)
}

fun update(
    conn: ConnWrapper,
    permission: DBPermission,
    table: String,
    filter: Filter,
    values: Map<String, Any?>,
): List<Map<String, Any?>> {
    val (_, wView) = permission
    val updatePairs = viewCleanUpdate(wView, table, filter, values)
    val allIds = mutableListOf<String>()

    for ((combinedFilter, cleanedValues) in updatePairs) {
        if (cleanedValues.isEmpty()) continue
        val ids = conn.db.listIds(conn, table, combinedFilter)
        if (ids.isEmpty()) continue
        allIds.addAll(ids)
        conn.db.updateEntries(conn, table, ids, cleanedValues)
    }

    return queryByIds(conn, permission, table, allIds)
}

fun delete(
    conn: ConnWrapper,
    permission: DBPermission,
    table: String,
    filter: Filter,
): List<Map<String, Any?>> {
    val (_, wView) = permission
    val combinedFilter = viewCleanDelete(wView, table, filter)
    val ids = conn.db.listIds(conn, table, combinedFilter)
    val entries = queryByIds(conn, permission, table, ids)
    conn.db.deleteEntries(conn, table, ids)
    return entries
}
