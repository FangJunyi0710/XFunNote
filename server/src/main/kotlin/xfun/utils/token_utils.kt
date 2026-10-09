package xfun.utils

import java.security.SecureRandom
import java.util.Base64

fun generateToken(): String {
    val random = SecureRandom()
    val bytes = ByteArray(24)
    random.nextBytes(bytes)
    return "sk-" + Base64.getUrlEncoder().withoutPadding().encodeToString(bytes)
}

private val TOKEN_REGEX = Regex("^sk-[-A-Za-z0-9_]{32}$")

fun validateToken(token: String): Boolean = TOKEN_REGEX.matches(token)
