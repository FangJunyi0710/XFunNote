package xfun.core

open class XFunError(message: String) : Exception(message)

class UsernameInvalidError(val username: String) :
    XFunError("非法用户名：$username")

class EntryInvalidError(val notebook: String, val reason: String) :
    XFunError("[$notebook] 条目无效: $reason")

class SQLInvalidError(val name: String) :
    XFunError("非法SQL片段: '$name'")

class FilterInvalidError(val obj: Any?) :
    XFunError("非法 Filter 对象: $obj")
