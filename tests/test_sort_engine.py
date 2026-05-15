"""Tests for SortEngine and SortResult."""

from __future__ import annotations

import pytest

from envoy_local.env_file import EnvFile
from envoy_local.sort_engine import SortEngine, SortOrder, SortResult


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("ZEBRA=1\nAPPLE=2\nMango=3\nBETA=4\n")
    ef = EnvFile(str(p))
    ef.load()
    return ef


@pytest.fixture
def engine(env_file):
    return SortEngine(env_file)


class TestSortResult:
    def test_success_true_when_no_error(self):
        r = SortResult(original_order=["B", "A"], sorted_order=["A", "B"])
        assert r.success is True

    def test_success_false_when_error_set(self):
        r = SortResult(original_order=[], sorted_order=[], error="boom")
        assert r.success is False

    def test_changed_when_orders_differ(self):
        r = SortResult(original_order=["B", "A"], sorted_order=["A", "B"])
        assert r.changed is True

    def test_not_changed_when_orders_same(self):
        r = SortResult(original_order=["A", "B"], sorted_order=["A", "B"])
        assert r.changed is False

    def test_summary_on_error(self):
        r = SortResult(original_order=[], sorted_order=[], error="oops")
        assert "failed" in r.summary()

    def test_summary_no_change(self):
        r = SortResult(original_order=["A"], sorted_order=["A"])
        assert "already" in r.summary()

    def test_summary_dry_run(self):
        r = SortResult(original_order=["B", "A"], sorted_order=["A", "B"])
        assert "dry-run" in r.summary()

    def test_summary_saved(self):
        r = SortResult(original_order=["B", "A"], sorted_order=["A", "B"], saved=True)
        assert "saved" in r.summary()

    def test_repr_contains_key_info(self):
        r = SortResult(original_order=["B", "A"], sorted_order=["A", "B"])
        assert "SortResult" in repr(r)
        assert "changed=True" in repr(r)


class TestSortEngine:
    def test_alpha_asc_sorts_keys(self, engine):
        result = engine.sort(order=SortOrder.ALPHA_ASC)
        assert result.sorted_order == sorted(result.original_order)

    def test_alpha_desc_sorts_keys(self, engine):
        result = engine.sort(order=SortOrder.ALPHA_DESC)
        assert result.sorted_order == sorted(result.original_order, reverse=True)

    def test_length_asc_sorts_by_length(self, engine):
        result = engine.sort(order=SortOrder.LENGTH_ASC)
        lengths = [len(k) for k in result.sorted_order]
        assert lengths == sorted(lengths)

    def test_length_desc_sorts_by_length_descending(self, engine):
        result = engine.sort(order=SortOrder.LENGTH_DESC)
        lengths = [len(k) for k in result.sorted_order]
        assert lengths == sorted(lengths, reverse=True)

    def test_dry_run_does_not_write(self, engine, env_file, tmp_path):
        original_text = open(env_file.path).read()
        engine.sort(order=SortOrder.ALPHA_ASC, dry_run=True)
        assert open(env_file.path).read() == original_text

    def test_write_persists_sorted_order(self, engine, env_file):
        result = engine.sort(order=SortOrder.ALPHA_ASC, dry_run=False)
        assert result.saved is True
        reloaded = EnvFile(env_file.path)
        reloaded.load()
        assert list(reloaded.keys()) == result.sorted_order

    def test_already_sorted_not_changed(self, tmp_path):
        p = tmp_path / ".env"
        p.write_text("ALPHA=1\nBETA=2\nZETA=3\n")
        ef = EnvFile(str(p))
        ef.load()
        eng = SortEngine(ef)
        result = eng.sort(order=SortOrder.ALPHA_ASC)
        assert result.changed is False
        assert result.saved is False
