"""测试 PlanNotebook 的核心业务逻辑：seq 分配、编号生成。"""

import pytest
from xfun.notebooks.plan import PlanNotebook, _seq_to_letter


class TestSeqAllocation:
    """计划本最核心的逻辑：seq 按月独立递增。"""

    def test_increments_within_month(self, db, plan_nb):
        db.init({plan_nb.name: plan_nb.columns})
        with db.transaction() as conn:
            ids = plan_nb.add(conn, [
                {"month": "2606", "content": "one"},
                {"month": "2606", "content": "two"},
                {"month": "2606", "content": "three"},
            ])
        with db.read_transaction() as conn:
            results = plan_nb.get_by_ids(conn, ids)
        assert [r["seq"] for r in results] == [1, 2, 3]

    def test_resets_per_month(self, db, plan_nb):
        db.init({plan_nb.name: plan_nb.columns})
        with db.transaction() as conn:
            ids = plan_nb.add(conn, [
                {"month": "2606", "content": "june"},
                {"month": "2607", "content": "july"},
            ])
        with db.read_transaction() as conn:
            results = plan_nb.get_by_ids(conn, ids)
        assert results[0]["seq"] == 1
        assert results[1]["seq"] == 1  # 不同月份独立计数

    def test_continues_across_batches(self, db, plan_nb):
        db.init({plan_nb.name: plan_nb.columns})
        with db.transaction() as conn:
            ids1 = plan_nb.add(conn, [{"month": "2607", "content": "first"}])
        with db.transaction() as conn:
            ids2 = plan_nb.add(conn, [{"month": "2607", "content": "second"}])
        with db.read_transaction() as conn:
            results = plan_nb.get_by_ids(conn, ids1 + ids2)
        assert [r["seq"] for r in results] == [1, 2]

    def test_id_format(self, db, plan_nb):
        db.init({plan_nb.name: plan_nb.columns})
        with db.transaction() as conn:
            ids = plan_nb.add(conn, [{"month": "2607", "content": "test"}])
        assert ids[0].startswith("plan-")

    def test_no_format(self, db, plan_nb):
        db.init({plan_nb.name: plan_nb.columns})
        with db.transaction() as conn:
            ids = plan_nb.add(conn, [{"month": "2607", "content": "test"}])
        with db.read_transaction() as conn:
            result = plan_nb.get_by_ids(conn, ids)
        assert result[0]["no"] == "2607A"


class TestSeqToLetter:
    """_seq_to_letter 边界情况。"""

    def test_overflow_uses_bracket(self):
        """seq 超出字母映射范围时使用 [seq] 格式。"""
        result = _seq_to_letter(101)
        assert result == "[101]"

    def test_first_maps_to_A(self):
        assert _seq_to_letter(1) == "A"

    def test_last_maps_to_omega(self):
        """第 100 个对应大写 Omega Ω。"""
        result = _seq_to_letter(100)
        assert result == "Ω"
