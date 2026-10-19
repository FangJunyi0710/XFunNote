package xfun.core

import xfun.utils.nowStr
import xfun.utils.timestampStr
import xfun.utils.uuid7
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.Paths
import java.sql.*

// ---------------------------------------------------------------------------
// Column definition
// ---------------------------------------------------------------------------

data class Column(
    val name: String,
    val colType: String,
    val nullable: Boolean = false,
    val primary_key: Boolean = false,
    val unique: Boolean = false,
    val index: Boolean = false,
    val default: Any? = null,
    val auto: Boolean = false,
) {
    companion object {
        private val COLUMN_PATTERN = Regex("""^[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*$""")

        fun check(name: String) {
            if (!COLUMN_PATTERN.matches(name)) throw SQLInvalidError(name)
        }

        fun checkOrderBy(orderBy: String) {
            for (part in orderBy.split(",")) {
                val tokens = part.trim().split(Regex("\\s+"), 2)
                check(tokens[0])
                if (tokens.size > 1 && tokens[1] !in listOf("ASC", "DESC")) {
                    throw SQLInvalidError(tokens[1])
                }
            }
        }
    }

    val sql: String
        get() {
            check(name)
            val parts = mutableListOf(name, colType)
            if (primary_key) parts.add("PRIMARY KEY")
            if (unique) parts.add("UNIQUE")
            if (!nullable) parts.add("NOT NULL")
            return parts.joinToString(" ")
        }
}

// ---------------------------------------------------------------------------
// Connection wrapper
// ---------------------------------------------------------------------------

class ConnWrapper(val raw: Connection, val db: DB) {
    fun execute(sql: String, params: List<Any?> = emptyList()): ResultSet {
        val stmt = raw.prepareStatement(sql)
        for ((i, p) in params.withIndex()) {
            stmt.setObject(i + 1, p)
        }
        return stmt.executeQuery()
    }

    fun executeUpdate(sql: String, params: List<Any?> = emptyList()): Int {
        val stmt = raw.prepareStatement(sql)
        try {
            for ((i, p) in params.withIndex()) {
                stmt.setObject(i + 1, p)
            }
            return stmt.executeUpdate()
        } finally {
            stmt.close()
        }
    }

    fun executeMany(sql: String, paramsList: List<Map<String, Any?>>) {
        val stmt = raw.prepareStatement(sql)
        try {
            for (params in paramsList) {
                val namedPattern = Regex(":([a-zA-Z_][a-zA-Z0-9_]*)")
                val paramNames = namedPattern.findAll(sql).map { it.groupValues[1] }.toList()
                for ((i, name) in paramNames.withIndex()) {
                    stmt.setObject(i + 1, params[name])
                }
                stmt.addBatch()
            }
            stmt.executeBatch()
        } finally {
            stmt.close()
        }
    }

    fun fetchAll(rs: ResultSet): List<Map<String, Any?>> {
        val result = mutableListOf<Map<String, Any?>>()
        val meta = rs.metaData
        val colCount = meta.columnCount
        while (rs.next()) {
            val row = linkedMapOf<String, Any?>()
            for (i in 1..colCount) {
                row[meta.getColumnLabel(i)] = rs.getObject(i)
            }
            result.add(row)
        }
        val stmt = rs.statement
        rs.close()
        stmt?.close()
        return result
    }
}

// ---------------------------------------------------------------------------
// Transaction contexts
// ---------------------------------------------------------------------------

class TransactionContext(private val db: DB) {
    fun connect(): ConnWrapper {
        val conn = db.createConnection()
        conn.createStatement().use { it.execute("BEGIN IMMEDIATE") }
        return ConnWrapper(conn, db)
    }

    fun commit(conn: Connection) {
        conn.createStatement().use { it.execute("COMMIT") }
        conn.close()
    }

    fun rollback(conn: Connection) {
        try {
            conn.createStatement().use { it.execute("ROLLBACK") }
        } finally {
            conn.close()
        }
    }
}

class ReadTransactionContext(private val db: DB) {
    fun connect(): ConnWrapper {
        val conn = db.createConnection()
        conn.createStatement().use { it.execute("PRAGMA query_only = ON") }
        conn.createStatement().use { it.execute("BEGIN") }
        return ConnWrapper(conn, db)
    }

    fun commit(conn: Connection) {
        conn.createStatement().use { it.execute("COMMIT") }
        conn.close()
    }

    fun rollback(conn: Connection) {
        try {
            conn.createStatement().use { it.execute("ROLLBACK") }
        } finally {
            conn.close()
        }
    }
}

// ---------------------------------------------------------------------------
// DB class
// ---------------------------------------------------------------------------

class DB(val dbPath: String) {
    val tableInfos = linkedMapOf<String, List<Column>>()
    private val hooks = mutableMapOf<String, HookSet>()

    data class HookSet(
        val preAdd: ((ConnWrapper, MutableList<Map<String, Any?>>) -> Unit)? = null,
        val validate: ((Map<String, Any?>) -> Unit)? = null,
        val autofill: ((MutableMap<String, Any?>) -> Unit)? = null
    )

    fun registerHooks(
        tableName: String,
        preAdd: ((ConnWrapper, MutableList<Map<String, Any?>>) -> Unit)? = null,
        validate: ((Map<String, Any?>) -> Unit)? = null,
        autofill: ((MutableMap<String, Any?>) -> Unit)? = null
    ) {
        hooks[tableName] = HookSet(preAdd, validate, autofill)
    }

    fun cols(table: String): List<String> = tableInfos[table]!!.map { it.name }

    fun createConnection(): Connection {
        Path.of(dbPath).parent?.let { Files.createDirectories(it) }
        val conn = DriverManager.getConnection("jdbc:sqlite:$dbPath")
        conn.createStatement().use { it.execute("PRAGMA journal_mode=WAL") }
        conn.createStatement().use { it.execute("PRAGMA busy_timeout=5000") }
        // Don't set autoCommit=false; we use explicit BEGIN/COMMIT
        return conn
    }

    fun transaction(): TransactionContext = TransactionContext(this)
    fun readTransaction(): ReadTransactionContext = ReadTransactionContext(this)

    // ---- inline transaction helpers ----

    inline fun <T> withTransaction(block: (ConnWrapper) -> T): T {
        val ctx = transaction()
        val conn = ctx.connect()
        return try {
            val result = block(conn)
            ctx.commit(conn.raw)
            result
        } catch (e: Exception) {
            ctx.rollback(conn.raw)
            throw e
        }
    }

    inline fun <T> withReadTransaction(block: (ConnWrapper) -> T): T {
        val ctx = readTransaction()
        val conn = ctx.connect()
        return try {
            val result = block(conn)
            ctx.commit(conn.raw)
            result
        } catch (e: Exception) {
            ctx.rollback(conn.raw)
            throw e
        }
    }

    // ---- init ----

    private fun tableExists(conn: ConnWrapper, tableName: String): Boolean {
        val rs = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            listOf(tableName)
        )
        return conn.fetchAll(rs).isNotEmpty()
    }

    private fun createTable(conn: ConnWrapper, tableName: String, cols: List<Column>) {
        val colsSql = cols.joinToString(", ") { it.sql }
        conn.executeUpdate("CREATE TABLE $tableName ($colsSql)")
    }

    private fun syncExistingTable(conn: ConnWrapper, tableName: String, desiredCols: List<Column>) {
        val rs = conn.execute("PRAGMA table_info($tableName)")
        val existingCols = conn.fetchAll(rs).associateBy { it["name"] as String }
        val desiredNames = desiredCols.map { it.name }.toSet()

        for ((existingName, _) in existingCols) {
            if (existingName !in desiredNames) {
                throw SQLInvalidError(
                    "表 $tableName 存在代码未定义的列 '$existingName'：" +
                    "请手动删除该列或重置数据库：ALTER TABLE $tableName DROP COLUMN $existingName"
                )
            }
        }

        for (col in desiredCols) {
            val existing = existingCols[col.name]
            if (existing == null) {
                checkAdditionColumn(col)
                conn.executeUpdate("ALTER TABLE $tableName ADD COLUMN ${col.sql}")
            } else {
                checkExistingColumn(col, existing, tableName)
            }
        }
    }

    private fun checkAdditionColumn(col: Column) {
        Column.check(col.name)
        if (!col.nullable) {
            throw SQLInvalidError("新增列 ${col.name} 不可为 NULL：ALTER TABLE ADD COLUMN 要求列必须可空")
        }
        if (col.primary_key) {
            throw SQLInvalidError("新增列 ${col.name} 为主键：ALTER TABLE ADD COLUMN 不支持添加主键列")
        }
        if (col.unique) {
            throw SQLInvalidError("新增列 ${col.name} 为 UNIQUE：ALTER TABLE ADD COLUMN 不支持添加 UNIQUE 约束列")
        }
    }

    private fun checkExistingColumn(col: Column, existing: Map<String, Any?>, tableName: String) {
        val existingType = (existing["type"] as String).uppercase()
        if (col.colType.uppercase() != existingType) {
            throw SQLInvalidError(
                "表 $tableName 列 ${col.name} 类型冲突：代码定义 ${col.colType}，数据库中为 $existingType"
            )
        }
        val existingNotNull = (existing["notnull"] as Number).toInt() != 0
        if (!col.nullable != existingNotNull) {
            throw SQLInvalidError(
                "表 $tableName 列 ${col.name} 约束冲突：代码定义 nullable=${col.nullable}，" +
                "数据库中为 ${if (existingNotNull) "NOT NULL" else "NULLABLE"}"
            )
        }
        val colPk = if (col.primary_key) 1 else 0
        val existingPk = (existing["pk"] as Number).toInt()
        if (colPk != existingPk) {
            throw SQLInvalidError(
                "表 $tableName 列 ${col.name} 主键属性冲突：代码定义 primary_key=${col.primary_key}，" +
                "数据库中为 ${if (existingPk != 0) "是主键" else "非主键"}"
            )
        }
    }

    private fun createIndexes(conn: ConnWrapper, tableName: String, cols: List<Column>) {
        for (col in cols) {
            if (!col.index) continue
            if (col.unique) continue
            conn.executeUpdate("CREATE INDEX IF NOT EXISTS idx_${tableName}_${col.name} ON $tableName(${col.name})")
        }
    }

    fun init() {
        withTransaction { conn ->
            for ((tableName, desiredCols) in tableInfos) {
                if (desiredCols.isEmpty()) continue
                Column.check(tableName)
                for (col in desiredCols) Column.check(col.name)

                if (tableExists(conn, tableName)) {
                    syncExistingTable(conn, tableName, desiredCols)
                } else {
                    createTable(conn, tableName, desiredCols)
                }
                createIndexes(conn, tableName, desiredCols)
            }
        }
    }

    // ---- backup & reset ----

    fun backup(): String {
        val parent = Path.of(dbPath).parent
        val stem = Path.of(dbPath).fileName.toString().substringBeforeLast(".")
        val dst = parent.resolve("backups").resolve("$stem.backup.${timestampStr()}")
        Files.createDirectories(dst.parent)
        Files.deleteIfExists(dst)

        val conn = createConnection()
        try {
            conn.createStatement().use { it.execute("VACUUM INTO '${dst.toAbsolutePath()}'") }
        } finally {
            conn.close()
        }
        return dst.toString()
    }

    fun restore(backupPath: String): String {
        val src = Path.of(backupPath)
        if (!Files.exists(src)) throw java.io.FileNotFoundException("备份文件不存在: $backupPath")

        val name = Path.of(dbPath).fileName.toString()
        val parent = Path.of(dbPath).parent
        for (ext in listOf("-wal", "-shm")) {
            Files.deleteIfExists(parent.resolve("$name$ext"))
        }

        Files.copy(src, Path.of(dbPath), java.nio.file.StandardCopyOption.REPLACE_EXISTING)
        return src.toString()
    }

    fun reset() {
        withTransaction { conn ->
            val rs = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            val rows = conn.fetchAll(rs)
            for (row in rows) {
                conn.executeUpdate("DROP TABLE IF EXISTS ${row["name"]}")
            }
        }
        init()
    }

    // ---- SQL generation ----

    fun insertSql(tableName: String): String {
        val colNames = cols(tableName)
        val cols = colNames.joinToString(", ")
        val vals = colNames.joinToString(", ") { ":$it" }
        return "INSERT INTO $tableName ($cols) VALUES ($vals)"
    }

    fun selectSql(tableName: String, cols: List<String>): String {
        val allCols = cols(tableName)
        val pieces = allCols.map { col ->
            if (col in cols) "$tableName.$col" else "NULL AS $col"
        }
        return "SELECT ${pieces.joinToString(", ")} FROM $tableName"
    }

    // ---- CRUD ----

    private fun validateEntryNull(tableName: String, entry: Map<String, Any?>) {
        for (col in tableInfos[tableName]!!) {
            if (!col.nullable && col.default == null && !col.auto) {
                if (col.name !in entry) {
                    throw EntryInvalidError(tableName, "缺少必填字段 '${col.name}'")
                }
            }
        }
    }

    private fun validateEntryType(tableName: String, entry: Map<String, Any?>) {
        for (col in tableInfos[tableName]!!) {
            val value = entry[col.name] ?: continue
            when (col.colType) {
                "TEXT" -> if (value !is String) {
                    throw EntryInvalidError(tableName, "列 '${col.name}' 应为 TEXT 类型，实际为 ${value::class.simpleName}")
                }
                "INTEGER" -> if (value !is Int && value !is Long) {
                    throw EntryInvalidError(tableName, "列 '${col.name}' 应为 INTEGER 类型，实际为 ${value::class.simpleName}")
                }
                "REAL" -> if (value !is Double && value !is Float && value !is Int && value !is Long) {
                    throw EntryInvalidError(tableName, "列 '${col.name}' 应为 REAL 类型，实际为 ${value::class.simpleName}")
                }
            }
        }
    }

    private fun autofillEntry(tableName: String, entry: MutableMap<String, Any?>) {
        val allCols = cols(tableName)
        if ("id" in allCols) entry["id"] = "$tableName-${uuid7()}"
        if ("created_at" in allCols) entry["created_at"] = nowStr()
        if ("updated_at" in allCols) entry["updated_at"] = nowStr()

        for (col in tableInfos[tableName]!!) {
            if (col.default != null) {
                val defaultVal = when (col.default) {
                    is Function0<*> -> (col.default as Function0<*>).invoke()
                    else -> col.default
                }
                entry.putIfAbsent(col.name, defaultVal)
            }
            if (col.nullable && col.name !in entry) {
                entry[col.name] = null
            }
        }
    }

    fun addEntries(conn: ConnWrapper, tableName: String, entries: MutableList<Map<String, Any?>>): List<String> {
        val hookSet = hooks[tableName] ?: HookSet()

        for (entry in entries) {
            validateEntryNull(tableName, entry)
            validateEntryType(tableName, entry)
            hookSet.validate?.invoke(entry)
        }

        hookSet.preAdd?.invoke(conn, entries)

        for (entry in entries) {
            @Suppress("UNCHECKED_CAST")
            val mutable = if (entry is MutableMap<String, Any?>) entry else entry.toMutableMap()
            autofillEntry(tableName, mutable)
            hookSet.autofill?.invoke(mutable)
        }

        conn.executeMany(insertSql(tableName), entries)
        return entries.map { it["id"] as String }
    }

    fun listIds(
        conn: ConnWrapper,
        tableName: String,
        filter: Filter,
        orderBy: String = "",
        limit: Int = -1,
        offset: Int = 0,
    ): List<String> {
        val (whereSql, params) = filterToSql(filter)
        val parts = mutableListOf("SELECT id FROM $tableName")
        if (whereSql.isNotEmpty()) parts.add("WHERE $whereSql")
        if (orderBy.isNotEmpty()) {
            Column.checkOrderBy(orderBy)
            parts.add("ORDER BY $orderBy")
        }
        parts.add("LIMIT $limit OFFSET $offset")
        val rs = conn.execute(parts.joinToString(" "), params)
        return conn.fetchAll(rs).map { it["id"] as String }
    }

    fun updateEntries(conn: ConnWrapper, tableName: String, entryIds: List<String>, entry: Map<String, Any?>) {
        if (entryIds.isEmpty()) return
        for (k in entry.keys) Column.check(k)

        validateEntryType(tableName, entry)
        val hookSet = hooks[tableName] ?: HookSet()
        hookSet.validate?.invoke(entry)

        val mutable = entry.toMutableMap()
        mutable.remove("id")
        mutable.remove("created_at")
        if ("updated_at" in cols(tableName)) {
            mutable["updated_at"] = nowStr()
        }

        val setClause = mutable.keys.joinToString(", ") { "$it = :$it" }
        val paramsList = entryIds.map { eid -> mutable + ("id" to eid) }
        conn.executeMany("UPDATE $tableName SET $setClause WHERE id = :id", paramsList)
    }

    fun deleteEntries(conn: ConnWrapper, tableName: String, entryIds: List<String>) {
        if (entryIds.isEmpty()) return
        val paramsList = entryIds.map { mapOf("id" to it) }
        conn.executeMany("DELETE FROM $tableName WHERE id = :id", paramsList)
    }
}
