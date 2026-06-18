"""测试 Notebook 注册查找。"""

import pytest
from xfun.core.registry import Registry
from xfun.core.errors import NotebookNotFoundError
from xfun.notebooks.plan import PlanNotebook


def test_lookup_found():
    reg = Registry()
    nb = PlanNotebook()
    reg.register("plan", nb)
    assert reg.notebook("plan") is nb


def test_lookup_missing_raises():
    reg = Registry()
    with pytest.raises(NotebookNotFoundError, match="nonexistent"):
        reg.notebook("nonexistent")


def test_register_sets_name():
    reg = Registry()
    nb = PlanNotebook()
    reg.register("my_plan", nb)
    assert nb.name == "my_plan"


def test_unregister_after_register():
    reg = Registry()
    reg.register("plan", PlanNotebook())
    reg.unregister("plan")
    with pytest.raises(NotebookNotFoundError):
        reg.notebook("plan")


def test_list_names():
    reg = Registry()
    reg.register("plan", PlanNotebook())
    reg.register("diary", PlanNotebook())
    names = list(reg.list_names())
    assert "plan" in names
    assert "diary" in names


def test_iterable():
    reg = Registry()
    nb = PlanNotebook()
    reg.register("plan", nb)
    notebooks = list(reg)
    assert notebooks == [nb]


def test_len():
    reg = Registry()
    assert len(reg) == 0
    reg.register("plan", PlanNotebook())
    assert len(reg) == 1


def test_contains():
    reg = Registry()
    assert "plan" not in reg
    reg.register("plan", PlanNotebook())
    assert "plan" in reg


def test_repr():
    reg = Registry()
    assert "(空)" in repr(reg)
    reg.register("plan", PlanNotebook())
    assert "plan" in repr(reg)
