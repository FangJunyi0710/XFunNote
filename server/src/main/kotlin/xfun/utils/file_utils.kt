package xfun

import xfun.core.EntryInvalidError
import xfun.core.SQLInvalidError
import xfun.core.UsernameInvalidError
import xfun.core.XFunError
import java.nio.file.Path
import java.util.regex.Pattern
import kotlin.io.path.exists

// ---------------------------------------------------------------------------
// file_utils
// ---------------------------------------------------------------------------

private val USERNAME_PATTERN = Pattern.compile("^[a-zA-Z0-9\\-_]{1,64}$")

fun getDbPath(user: String): String {
    if (!USERNAME_PATTERN.matcher(user).matches()) {
        throw UsernameInvalidError(user)
    }
    return DATA_DIR.resolve("$user.db").toString()
}
