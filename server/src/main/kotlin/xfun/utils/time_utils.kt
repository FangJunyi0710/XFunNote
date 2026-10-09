package xfun.utils

import java.time.Instant
import java.time.LocalDate
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException

private val ISO_FORMATTER = DateTimeFormatter
    .ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'")
    .withZone(ZoneOffset.UTC)

private val DATE_FORMATTER = DateTimeFormatter.ISO_LOCAL_DATE

fun formatDateTime(millis: Long = System.currentTimeMillis()): String {
    return ISO_FORMATTER.format(Instant.ofEpochMilli(millis))
}

fun nowStr(): String = formatDateTime()

fun timestampStr(): String {
    val now = Instant.now().atOffset(ZoneOffset.UTC)
    return String.format(
        "%04d%02d%02d_%02d%02d%02d",
        now.year, now.monthValue, now.dayOfMonth,
        now.hour, now.minute, now.second
    )
}

private val DATETIME_REGEX = Regex("""^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$""")

fun validateDatetime(s: String): Boolean {
    if (!DATETIME_REGEX.matches(s)) return false
    return try {
        Instant.parse(s)
        true
    } catch (_: DateTimeParseException) {
        false
    }
}

private val DATE_REGEX = Regex("""^\d{4}-\d{2}-\d{2}$""")

fun validateDate(s: String): Boolean {
    if (!DATE_REGEX.matches(s)) return false
    return try {
        LocalDate.parse(s, DATE_FORMATTER)
        true
    } catch (_: DateTimeParseException) {
        false
    }
}

private val YYMM_REGEX = Regex("""^\d{2}(0[1-9]|1[0-2])$""")

fun validateYymm(s: String): Boolean = YYMM_REGEX.matches(s)
