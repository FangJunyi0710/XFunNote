package xfun.notebooks

import xfun.core.Column
import xfun.core.Notebook

object PlanNotebook : Notebook() {
    override val name = "plan"
    override val extraColumns = listOf(
        Column("no", "TEXT", auto = true, unique = true),
        Column("seq", "INTEGER", auto = true),
        Column("month", "TEXT", index = true),
        Column("done", "INTEGER", default = 0),
    )

    private val SEQ_TO_LETTER = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzαβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"

    private fun seqToLetter(seq: Int): String {
        return if (seq in 1..SEQ_TO_LETTER.length) {
            SEQ_TO_LETTER[seq - 1].toString()
        } else {
            "[$seq]"
        }
    }

    override fun preAdd(conn: xfun.core.ConnWrapper, entries: MutableList<Map<String, Any?>>) {
        val monthCounter = mutableMapOf<String, Int>()
        for (entry in entries) {
            val month = entry["month"] as String
            if (month !in monthCounter) {
                val rs = conn.execute(
                    "SELECT MAX(seq) FROM $name WHERE month = ?", listOf(month)
                )
                val rows = conn.fetchAll(rs)
                val maxSeq = rows[0].values.first()
                monthCounter[month] = if (maxSeq != null) (maxSeq as Number).toInt() else 0
            }
            monthCounter[month] = monthCounter[month]!! + 1
            (entry as MutableMap)["seq"] = monthCounter[month]
        }
    }

    override fun autofill(entry: MutableMap<String, Any?>) {
        super.autofill(entry)
        val month = entry["month"] as String
        val seq = (entry["seq"] as Number).toInt()
        entry["no"] = "$month${seqToLetter(seq)}"
    }

    override fun validate(entry: Map<String, Any?>) {
        super.validate(entry)
        val month = entry["month"]
        if (month != null) {
            if (!xfun.utils.validateYymm(month.toString())) {
                throw xfun.core.EntryInvalidError("plan", "month 格式错误，应为 YYMM，实际: $month")
            }
        }
        val done = entry["done"]
        if (done != null) {
            val v = (done as? Number)?.toInt() ?: done
            if (v !in listOf(0, 1)) {
                throw xfun.core.EntryInvalidError("plan", "done 必须为 0 或 1，实际: $done")
            }
        }
    }
}
