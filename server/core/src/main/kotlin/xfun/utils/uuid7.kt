package xfun.utils

import java.util.concurrent.atomic.AtomicLong

private val UUID7_EPOCH_MILLIS = 1704067200000L // 2024-01-01T00:00:00Z

private val counter = AtomicLong(0)

fun uuid7(): String {
    val timestamp = System.currentTimeMillis() - UUID7_EPOCH_MILLIS
    val seq = counter.incrementAndGet() and 0x3FFF

    val msb = (timestamp and 0xFFFFFFFFFFFFL) shl 16 or (0x7L shl 12) or (seq and 0x0FFF)
    val lsb = (0x80L shl 56) or ((System.nanoTime() and 0x3FFFFFFFFFFFFFFFL) or 1L)

    return formatUuid(msb, lsb)
}

private fun formatUuid(msb: Long, lsb: Long): String {
    val hex = "0123456789abcdef"
    val chars = CharArray(36)
    var idx = 0
    for (i in 63 downTo 32 step 4) {
        chars[idx++] = hex[((msb shr i) and 0xF).toInt()]
    }
    chars[idx++] = '-'
    for (i in 31 downTo 16 step 4) {
        chars[idx++] = hex[((msb shr i) and 0xF).toInt()]
    }
    chars[idx++] = '-'
    for (i in 15 downTo 0 step 4) {
        chars[idx++] = hex[((msb shr i) and 0xF).toInt()]
    }
    chars[idx++] = '-'
    for (i in 63 downTo 48 step 4) {
        chars[idx++] = hex[((lsb shr i) and 0xF).toInt()]
    }
    chars[idx++] = '-'
    for (i in 47 downTo 0 step 4) {
        chars[idx++] = hex[((lsb shr i) and 0xF).toInt()]
    }
    return String(chars)
}
