"""测试 PlanNotebook — 字母编号、seq 自动递增。"""

import pytest

from xfun.core.filter import Condition


class TestPlanNotebook:
    def test_add_single(self, registry, db):
        nb = registry["plan"]
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "plan", [{"content": "task 1", "month": "2606"}])
        assert len(ids) == 1
        assert ids[0].startswith("plan-")

    def test_seq_increments_within_month(self, registry, db):
        nb = registry["plan"]
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "plan", [
                {"content": "task 1", "month": "2606"},
                {"content": "task 2", "month": "2606"},
                {"content": "task 3", "month": "2606"},
            ])
        with db.transaction() as conn:
            rows = [dict(r) for r in conn.execute(
                f"SELECT * FROM plan WHERE id IN ({', '.join('?' for _ in ids)})",
                ids,
            ).fetchall()]
        seqs = [r["seq"] for r in rows]
        assert seqs == [1, 2, 3]

    def test_seq_independent_across_months(self, registry, db):
        nb = registry["plan"]
        with db.transaction() as conn:
            ids2606 = conn.db.add_entries(conn, "plan", [
                {"content": "t1", "month": "2606"},
                {"content": "t2", "month": "2606"},
            ])
            ids2607 = conn.db.add_entries(conn, "plan", [
                {"content": "t3", "month": "2607"},
            ])
        with db.transaction() as conn:
            rows2606 = [dict(r) for r in conn.execute(
                f"SELECT * FROM plan WHERE id IN ({', '.join('?' for _ in ids2606)})",
                ids2606,
            ).fetchall()]
            rows2607 = [dict(r) for r in conn.execute(
                f"SELECT * FROM plan WHERE id IN ({', '.join('?' for _ in ids2607)})",
                ids2607,
            ).fetchall()]
        assert [r["seq"] for r in rows2606] == [1, 2]
        assert [r["seq"] for r in rows2607] == [1]

    def test_no_generated(self, registry, db):
        """plan 的 no 应基于 seq 自动生成字母编号。"""
        nb = registry["plan"]
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "plan", [
                {"content": "task A", "month": "2606"},
                {"content": "task B", "month": "2606"},
            ])
        with db.transaction() as conn:
            rows = [dict(r) for r in conn.execute(
                f"SELECT * FROM plan WHERE id IN ({', '.join('?' for _ in ids)})",
                ids,
            ).fetchall()]
        assert rows[0]["no"] == "2606A"
        assert rows[1]["no"] == "2606B"

    def test_no_generated_for_multiple_months(self, registry, db):
        nb = registry["plan"]
        with db.transaction() as conn:
            ids2606 = conn.db.add_entries(conn, "plan", [{"content": "t1", "month": "2606"}])
            ids2607 = conn.db.add_entries(conn, "plan", [{"content": "t2", "month": "2607"}])
        with db.transaction() as conn:
            r1 = [dict(r) for r in conn.execute(
                f"SELECT * FROM plan WHERE id IN ({', '.join('?' for _ in ids2606)})",
                ids2606,
            ).fetchall()]
            r2 = [dict(r) for r in conn.execute(
                f"SELECT * FROM plan WHERE id IN ({', '.join('?' for _ in ids2607)})",
                ids2607,
            ).fetchall()]
        assert r1[0]["no"] == "2606A"
        assert r2[0]["no"] == "2607A"

    def test_done_defaults_to_zero(self, registry, db):
        nb = registry["plan"]
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "plan", [{"content": "task", "month": "2606"}])
        with db.transaction() as conn:
            row = dict(conn.execute(
                "SELECT * FROM plan WHERE id = ?",
                ids,
            ).fetchone())
        assert row["done"] == 0

    def test_missing_month_raises(self, registry, db):
        nb = registry["plan"]
        with db.transaction() as conn:
            with pytest.raises(Exception):
                conn.db.add_entries(conn, "plan", [{"content": "no month"}])

    def test_seq_continues_after_add_batch(self, registry, db):
        """同一月份批量添加后，再添加应继续递增。"""
        nb = registry["plan"]
        with db.transaction() as conn:
            ids_first = conn.db.add_entries(conn, "plan", [
                {"content": "a", "month": "2606"},
                {"content": "b", "month": "2606"},
            ])
        with db.transaction() as conn:
            ids_second = conn.db.add_entries(conn, "plan", [
                {"content": "c", "month": "2606"},
            ])
        with db.transaction() as conn:
            r2 = [dict(r) for r in conn.execute(
                f"SELECT * FROM plan WHERE id IN ({', '.join('?' for _ in ids_second)})",
                ids_second,
            ).fetchall()]
        assert r2[0]["seq"] == 3
        assert r2[0]["no"] == "2606C"

    def test_list_by_month(self, registry, db):
        nb = registry["plan"]
        with db.transaction() as conn:
            conn.db.add_entries(conn, "plan", [
                {"content": "june1", "month": "2606"},
                {"content": "june2", "month": "2606"},
                {"content": "july1", "month": "2607"},
            ])
        with db.transaction() as conn:
            june_ids = conn.db.list_ids(conn, "plan", [[Condition("month", "2606", "=")]])
        assert len(june_ids) == 2

    def test_seq_starts_from_existing_max(self, registry, db):
        """seq 应从已有数据的 MAX(seq) + 1 开始。"""
        nb = registry["plan"]
        with db.transaction() as conn:
            conn.execute(
                "INSERT INTO plan (id, content, month, seq, no, done, created_at, updated_at, tags, ai_tags, is_ai_gen) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("plan-pre", "pre", "2606", 5, "2606E", 0,
                 "2026-01-01", "2026-01-01", "[]", "[]", 0),
            )
        with db.transaction() as conn:
            ids = conn.db.add_entries(conn, "plan", [{"content": "after", "month": "2606"}])
        with db.transaction() as conn:
            row = dict(conn.execute(
                "SELECT * FROM plan WHERE id = ?",
                ids,
            ).fetchone())
        assert row["no"] == "2606F"

    def test_missing_content_raises(self, registry, db):
        nb = registry["plan"]
        with db.transaction() as conn:
            with pytest.raises(Exception):
                conn.db.add_entries(conn, "plan", [{"month": "2606"}])


class TestPlanEdgeCases:
    """覆盖 _seq_to_letter 越界分支 (l.22)。"""

    def test_seq_to_letter_zero(self):
        from xfun.notebooks.plan import _seq_to_letter
        assert _seq_to_letter(0) == "[0]"

    def test_seq_to_letter_negative(self):
        from xfun.notebooks.plan import _seq_to_letter
        assert _seq_to_letter(-1) == "[-1]"

    def test_seq_to_letter_beyond_100(self):
        from xfun.notebooks.plan import _seq_to_letter
        assert _seq_to_letter(101) == "[101]"

    def test_seq_to_letter_normal(self):
        from xfun.notebooks.plan import _seq_to_letter
        assert _seq_to_letter(1) == "A"
        assert _seq_to_letter(26) == "Z"
