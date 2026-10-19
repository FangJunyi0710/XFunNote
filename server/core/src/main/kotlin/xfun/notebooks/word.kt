package xfun.notebooks

import xfun.core.Column
import xfun.core.EntryInvalidError
import xfun.core.Notebook
import xfun.utils.validateDatetime

object WordNotebook : Notebook() {
    override val name = "word"
    override val extraColumns = listOf(
        Column("word", "TEXT", unique = true),
        Column("part_of_speech", "TEXT", nullable = true),
        Column("phonetic", "TEXT", nullable = true),
        Column("example", "TEXT", nullable = true),
        Column("related_words", "TEXT", nullable = true),
        Column("stability", "REAL", auto = true, default = 2.5),
        Column("difficulty", "REAL", auto = true, default = 5.0),
        Column("state", "INTEGER", auto = true, default = 0),
        Column("lapses", "INTEGER", auto = true, default = 0),
        Column("step", "INTEGER", auto = true, default = 0),
        Column("review_count", "INTEGER", auto = true, default = 0),
        Column("next_review", "TEXT", auto = true, default = { xfun.utils.nowStr() }),
        Column("last_review", "TEXT", nullable = true, auto = true),
    )

    override fun validate(entry: Map<String, Any?>) {
        super.validate(entry)
        val stability = entry["stability"]
        if (stability != null) {
            val v = (stability as? Number)?.toDouble() ?: throw EntryInvalidError("word", "stability 必须为数字，实际: $stability")
            if (v <= 0) throw EntryInvalidError("word", "stability 必须大于 0，实际: $v")
        }
        val difficulty = entry["difficulty"]
        if (difficulty != null) {
            val v = (difficulty as? Number)?.toDouble() ?: throw EntryInvalidError("word", "difficulty 必须为数字，实际: $difficulty")
            if (v < 1.0 || v > 10.0) throw EntryInvalidError("word", "difficulty 必须在 1.0 ~ 10.0 之间，实际: $v")
        }
        val state = entry["state"]
        if (state != null) {
            val v = (state as? Number)?.toInt() ?: throw EntryInvalidError("word", "state 必须为整数，实际: $state")
            if (v !in 0..3) throw EntryInvalidError("word", "state 必须为 0/1/2/3，实际: $v")
        }
        val lapses = entry["lapses"]
        if (lapses != null) {
            val v = (lapses as? Number)?.toInt() ?: throw EntryInvalidError("word", "lapses 必须为整数，实际: $lapses")
            if (v < 0) throw EntryInvalidError("word", "lapses 必须 >= 0，实际: $v")
        }
        val step = entry["step"]
        if (step != null) {
            val v = (step as? Number)?.toInt() ?: throw EntryInvalidError("word", "step 必须为整数，实际: $step")
            if (v < 0) throw EntryInvalidError("word", "step 必须 >= 0，实际: $v")
        }
        val reviewCount = entry["review_count"]
        if (reviewCount != null) {
            val v = (reviewCount as? Number)?.toInt() ?: throw EntryInvalidError("word", "review_count 必须为整数，实际: $reviewCount")
            if (v < 0) throw EntryInvalidError("word", "review_count 必须 >= 0，实际: $v")
        }
        val nextReview = entry["next_review"]
        if (nextReview != null) {
            if (!validateDatetime(nextReview.toString())) {
                throw EntryInvalidError("word", "next_review 格式错误，应为 ISO 8601，实际: $nextReview")
            }
        }
        val lastReview = entry["last_review"]
        if (lastReview != null) {
            if (!validateDatetime(lastReview.toString())) {
                throw EntryInvalidError("word", "last_review 格式错误，应为 ISO 8601，实际: $lastReview")
            }
        }
    }
}
