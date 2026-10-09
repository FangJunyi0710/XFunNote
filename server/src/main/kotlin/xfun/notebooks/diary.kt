package xfun.notebooks

import xfun.core.Column
import xfun.core.EntryInvalidError
import xfun.core.Notebook
import xfun.utils.validateDate

object DiaryNotebook : Notebook() {
    override val name = "diary"
    override val extraColumns = listOf(
        Column("date", "TEXT", index = true),
        Column("mood", "TEXT", nullable = true),
        Column("weather", "TEXT", nullable = true),
    )

    override fun validate(entry: Map<String, Any?>) {
        super.validate(entry)
        val date = entry["date"]
        if (date != null) {
            if (!validateDate(date.toString())) {
                throw EntryInvalidError("diary", "date 格式错误，应为 YYYY-MM-DD，实际: $date")
            }
        }
    }
}
