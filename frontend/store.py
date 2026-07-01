"""Flat-key single-source store for session_state.

每个数据只有 1 个扁平 session_state key，无嵌套、无副本、无手动同步。
"""
from __future__ import annotations

import streamlit as st


class StoreProxy:
    """Prefix-based flat key proxy for st.session_state.

    store["limit"] → st.session_state["nb_plan_limit"]
    store["results"] = None → st.session_state["nb_plan_results"] = None

    所有 widget key 直接等于 session_state key，无需 on_change 同步。
    """

    def __init__(self, prefix: str):
        self._prefix = prefix

    def _key(self, name: str) -> str:
        return f"{self._prefix}_{name}"

    def __getitem__(self, name: str):
        return st.session_state[self._key(name)]

    def __setitem__(self, name: str, value):
        st.session_state[self._key(name)] = value

    def __delitem__(self, name: str):
        del st.session_state[self._key(name)]

    def __contains__(self, name: str) -> bool:
        return self._key(name) in st.session_state

    def get(self, name: str, default=None):
        return st.session_state.get(self._key(name), default)
