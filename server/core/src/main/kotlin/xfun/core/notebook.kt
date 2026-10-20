package xfun.core

// ---------------------------------------------------------------------------
// Notebook base class
// ---------------------------------------------------------------------------

val BASE_COLUMNS = listOf(
    Column("id", "TEXT", primary_key = true, auto = true),
    Column("content", "TEXT"),
    Column("created_at", "TEXT", auto = true),
    Column("updated_at", "TEXT", auto = true),
    Column("tags", "TEXT", nullable = true),
    Column("note", "TEXT", nullable = true),
    Column("is_ai_gen", "INTEGER", default = 0, auto = true),
    Column("ai_tags", "TEXT", nullable = true, auto = true),
    Column("ai_note", "TEXT", nullable = true, auto = true),
)

abstract class Notebook {
    abstract val name: String
    open val extraColumns: List<Column> = emptyList()

    val columns: List<Column> get() = BASE_COLUMNS + extraColumns

    open fun preAdd(conn: ConnWrapper, entries: MutableList<Map<String, Any?>>) {}

    open fun validate(entry: Map<String, Any?>) {
        val isAiGen = entry["is_ai_gen"]
        if (isAiGen != null) {
            val v = (isAiGen as? Number)?.toInt()
            if (v != null && v !in listOf(0, 1)) {
                throw EntryInvalidError("notebook", "is_ai_gen 必须为 0 或 1，实际: $isAiGen")
            }
        }
    }

    open fun autofill(entry: MutableMap<String, Any?>) {}

    override fun toString(): String = name
}
