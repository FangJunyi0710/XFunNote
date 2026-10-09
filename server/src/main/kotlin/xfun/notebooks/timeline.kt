package xfun.notebooks

import xfun.core.Column
import xfun.core.EntryInvalidError
import xfun.core.Notebook
import xfun.utils.validateDatetime

object TimelineNotebook : Notebook() {
    override val name = "timeline"
    override val extraColumns = listOf(
        Column("start_time", "TEXT", index = true),
        Column("end_time", "TEXT", nullable = true),
        Column("location", "TEXT", nullable = true),
    )

    override fun validate(entry: Map<String, Any?>) {
        super.validate(entry)
        val startTime = entry["start_time"]
        if (startTime != null) {
            if (!validateDatetime(startTime.toString())) {
                throw EntryInvalidError("timeline", "start_time 格式错误，应为 ISO 8601，实际: $startTime")
            }
        }
        val endTime = entry["end_time"]
        if (endTime != null) {
            if (!validateDatetime(endTime.toString())) {
                throw EntryInvalidError("timeline", "end_time 格式错误，应为 ISO 8601，实际: $endTime")
            }
        }
    }
}
