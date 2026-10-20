package com.xfunnote.xfunnote

import android.webkit.JavascriptInterface
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import xfun.AppConfig
import xfun.service.ApiRouter
import java.io.File
import java.nio.file.Paths

/**
 * Android 本地模式的 JS↔Kotlin 桥。
 * 前端 apiClient 检测到 window.XFunBridge 就走这里，进程内直调共享 :core 的 ApiRouter，
 * 不经过任何 HTTP/端口。返回 {status, body} 且 body 为 JSON 字符串，与 HTTP 传输逐字节一致。
 */
class XFunBridge {

    private val json = Json { ignoreUnknownKeys = true }

    @JavascriptInterface
    fun request(reqJson: String): String {
        val req = json.parseToJsonElement(reqJson).jsonObject

        fun str(key: String): String? = (req[key] as? JsonPrimitive)?.contentOrNull

        val query: Map<String, String> = (req["query"] as? JsonObject)
            ?.mapValues { (_, v) -> v.jsonPrimitive.content }
            ?: emptyMap()

        val body = req["body"]?.takeIf { it != JsonNull }

        val r = ApiRouter.dispatch(
            method = str("method") ?: "GET",
            path = str("path") ?: "/",
            query = query,
            body = body,
            token = str("token"),
            user = str("user"),
        )

        return buildJsonObject {
            put("status", r.status)
            put("body", r.body.toString())   // RawResponse.body 是字符串
        }.toString()
    }

    /** 本地模式：暴露本机 bootstrap root token，供前端自动完成本地登录（远端模式用不到）。 */
    @JavascriptInterface
    fun getBootstrapToken(): String = AppConfig.rootToken

    companion object {
        /** 桥/WebView 建立前调用：把数据目录与本机 root token 注入共享 :core。 */
        fun configure(dataDir: File, rootToken: String) {
            AppConfig.dataDir = Paths.get(dataDir.absolutePath)
            AppConfig.rootToken = rootToken
        }
    }
}
