package xfun

import xfun.core.Column
import xfun.core.DB
import xfun.core.EntryInvalidError
import xfun.core.validateView
import xfun.utils.generateToken
import xfun.utils.uuid7
import xfun.utils.validateDatetime
import xfun.utils.validateToken

// ---------------------------------------------------------------------------
// System table definitions
// ---------------------------------------------------------------------------

val SYSTEM_TABLES: Map<String, List<Column>> = mapOf(
    "_token" to listOf(
        Column("id", "TEXT", primary_key = true, auto = true),
        Column("token", "TEXT", default = ::generateToken, auto = true, unique = true),
        Column("name", "TEXT", unique = true),
        Column("permission", "TEXT"),
        Column("is_active", "INTEGER", default = 0),
        Column("shortcut", "TEXT", nullable = true, unique = true),
        Column("shortcut_expire_at", "TEXT", nullable = true),
        Column("expires_at", "TEXT", nullable = true),
        Column("created_at", "TEXT", auto = true),
        Column("updated_at", "TEXT", auto = true),
    ),
    "_view" to listOf(
        Column("id", "TEXT", primary_key = true, auto = true),
        Column("name", "TEXT", unique = true),
        Column("data", "TEXT"),
        Column("created_at", "TEXT", auto = true),
        Column("updated_at", "TEXT", auto = true),
    ),
    "_permission" to listOf(
        Column("id", "TEXT", primary_key = true, auto = true),
        Column("uuid", "TEXT", default = { uuid7() }, auto = true, unique = true),
        Column("name", "TEXT", unique = true),
        Column("description", "TEXT", nullable = true),
        Column("read_view", "TEXT"),
        Column("write_view", "TEXT"),
        Column("created_at", "TEXT", auto = true),
        Column("updated_at", "TEXT", auto = true),
    ),
)

// ---------------------------------------------------------------------------
// System table hooks
// ---------------------------------------------------------------------------

private fun validateTokenEntry(entry: Map<String, Any?>) {
    val token = entry["token"]
    if (token != null) {
        if (!validateToken(token.toString())) {
            throw EntryInvalidError("_token", "token 格式无效: $token")
        }
    }
    val shortcut = entry["shortcut"]
    if (shortcut != null) {
        if (validateToken(shortcut.toString())) {
            throw EntryInvalidError("_token", "shortcut 不能符合 token 格式: $shortcut")
        }
    }
    val isActive = entry["is_active"]
    if (isActive != null) {
        val v = (isActive as? Number)?.toInt() ?: isActive
        if (v !in listOf(0, 1)) {
            throw EntryInvalidError("_token", "is_active 必须为 0 或 1: $isActive")
        }
    }
    val expiresAt = entry["expires_at"]
    if (expiresAt != null) {
        if (!validateDatetime(expiresAt.toString())) {
            throw EntryInvalidError("_token", "expires_at 不是有效的 ISO UTC 时间: $expiresAt")
        }
    }
    val shortcutExpireAt = entry["shortcut_expire_at"]
    if (shortcutExpireAt != null) {
        if (!validateDatetime(shortcutExpireAt.toString())) {
            throw EntryInvalidError("_token", "shortcut_expire_at 不是有效的 ISO UTC 时间: $shortcutExpireAt")
        }
    }
}

private fun validatePermissionEntry(entry: Map<String, Any?>) {
    for (key in listOf("read_view", "write_view")) {
        val value = entry[key]
        if (value != null) {
            validateView(value.toString())
        }
    }
}

private fun validateViewEntry(entry: Map<String, Any?>) {
    val data = entry["data"]
    if (data != null) {
        validateView(data.toString())
    }
}

fun registerSystemHooks(db: DB) {
    db.registerHooks("_token", validate = ::validateTokenEntry)
    db.registerHooks("_permission", validate = ::validatePermissionEntry)
    db.registerHooks("_view", validate = ::validateViewEntry)
}
