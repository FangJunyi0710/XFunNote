package xfun.notebooks

import xfun.core.Column
import xfun.core.EntryInvalidError
import xfun.core.Notebook
import xfun.utils.uuid7
import xfun.utils.validateDate

object LedgerNotebook : Notebook() {
    override val name = "ledger"
    override val extraColumns = listOf(
        Column("date", "TEXT", index = true),
        Column("amount_cents", "INTEGER"),
        Column("account", "TEXT"),
        Column("transaction_id", "TEXT", index = true, default = { uuid7() }),
    )

    override fun validate(entry: Map<String, Any?>) {
        super.validate(entry)
        val date = entry["date"]
        if (date != null) {
            if (!validateDate(date.toString())) {
                throw EntryInvalidError("ledger", "date 格式错误，应为 YYYY-MM-DD，实际: $date")
            }
        }
        val amountCents = entry["amount_cents"]
        if (amountCents != null) {
            val v = (amountCents as? Number)?.toInt() ?: throw EntryInvalidError("ledger", "amount_cents 必须为数字，实际: $amountCents")
            if (v == 0) throw EntryInvalidError("ledger", "amount_cents 不能为 0")
        }
    }
}
