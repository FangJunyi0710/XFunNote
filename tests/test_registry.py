"""测试笔记本 dict 注册查找。"""

import pytest
from xfun.notebooks.plan import PlanNotebook


def test_lookup_found():
    reg = {"plan": PlanNotebook()}
    assert reg["plan"] is reg["plan"]


def test_lookup_missing_raises():
    reg: dict = {}
    with pytest.raises(KeyError, match="nonexistent"):
        _ = reg["nonexistent"]


def test_register_sets_name():
    nb = PlanNotebook()
    assert nb.name == "plan"


def test_unregister_after_register():
    reg = {"plan": PlanNotebook()}
    del reg["plan"]
    assert "plan" not in reg


def test_list_names():
    reg = {"plan": PlanNotebook(), "diary": PlanNotebook()}
    names = list(reg.keys())
    assert "plan" in names
    assert "diary" in names


def test_iterable():
    reg = {"plan": PlanNotebook()}
    notebooks = list(reg.values())
    assert len(notebooks) == 1


def test_len():
    reg: dict = {}
    assert len(reg) == 0
    reg["plan"] = PlanNotebook()
    assert len(reg) == 1


def test_contains():
    reg: dict = {}
    assert "plan" not in reg
    reg["plan"] = PlanNotebook()
    assert "plan" in reg
