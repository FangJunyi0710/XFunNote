package xfun

import xfun.core.DB
import xfun.core.Notebook
import xfun.notebooks.*

val registry: Map<String, Notebook> = mapOf(
    "plan" to PlanNotebook,
    "diary" to DiaryNotebook,
    "word" to WordNotebook,
    "accumulation" to AccumulationNotebook,
    "aimemory" to AIMemoryNotebook,
    "timeline" to TimelineNotebook,
    "schedule" to ScheduleNotebook,
    "ledger" to LedgerNotebook,
)

fun initDb(db: DB) {
    for ((name, nb) in registry) {
        db.registerHooks(name, preAdd = nb::preAdd, validate = nb::validate, autofill = nb::autofill)
    }
    registerSystemHooks(db)
    for ((name, nb) in registry) {
        db.tableInfos[name] = nb.columns
    }
    db.tableInfos.putAll(SYSTEM_TABLES)
}
