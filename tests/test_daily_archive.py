"""Synthetic, offline evidence preservation checks; never reads a live mailbox."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/dahua-daily-archive/scripts/export_day.py"
spec = importlib.util.spec_from_file_location("daily_archive", SCRIPT)
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


class DailyArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.paths = {}

    def source(self, stream, rows):
        p = self.root / (stream + ".json")
        key = "events" if stream == "operations" else "transcript"
        p.write_text(json.dumps({key: rows}, ensure_ascii=False))
        self.paths[stream] = p
        return p

    def group(self, **changes):
        row = dict(t="2026-10-15T12:30:00-07:00", speaker="青霞", text="第一行\n```\n原话  ", exchange_id="g1", kind="agent")
        return {**row, **changes}

    def run_export(self):
        result = archive.export("2026-10-15", "America/Los_Angeles", self.paths, self.root / "daily")
        p = Path(result["revision"])
        return result, p, json.loads((p / "records.json").read_text())

    def test_preserves_text_and_source_without_attesting_delivery(self):
        p = self.source("group", [self.group()])
        original = p.read_bytes()
        result, dest, payload = self.run_export()
        self.assertEqual(payload["records"][0]["text"], self.group()["text"])
        self.assertEqual(payload["records"][0]["delivery"], "unknown")
        self.assertEqual(payload["records"][0]["generation_origin"], "unknown")
        self.assertEqual(original, p.read_bytes())
        self.assertEqual(set(result["missing_sources"]), {"peer_private", "host_private", "operations"})
        archive.verify(dest)
        self.assertNotIn(str(self.root), (dest / "manifest.json").read_text())

    def test_idempotence_other_day_growth_and_late_revision(self):
        self.source("group", [self.group()])
        _, first, _ = self.run_export()
        frozen = {p.name: p.read_bytes() for p in first.iterdir()}
        self.source("group", [self.group(), self.group(t="2026-10-16T12:30:00-07:00")])
        result, _, _ = self.run_export()
        self.assertEqual(result["status"], "unchanged")
        self.source("group", [self.group(), self.group(text="迟到归档", t="2026-10-15T13:30:00-07:00")])
        result, second, payload = self.run_export()
        self.assertEqual(second.name, "r002")
        self.assertEqual(len(payload["records"]), 2)
        self.assertEqual(json.loads((second / "manifest.json").read_text())["supersedes"], "r001")
        self.assertEqual(frozen, {p.name: p.read_bytes() for p in first.iterdir()})

    def test_day_boundaries_and_dst(self):
        self.source("group", [self.group(t="2026-10-15T06:59:59Z"), self.group(t="2026-10-15T07:00:00Z"), self.group(t="2026-10-16T07:00:00Z")])
        _, _, payload = self.run_export()
        self.assertEqual(len(payload["records"]), 1)
        for day, hours in [("2026-03-08", 23), ("2026-11-01", 25)]:
            start, end = archive.window(day, "America/Los_Angeles")
            self.assertEqual((end-start).total_seconds(), hours*3600)

    def test_host_export_and_system_skip_remain_distinct(self):
        self.source("host_private", [dict(t="2026-10-15T17:07:00-07:00", **{"from":"青霞", "to":"紫霞"}, text="只有这句原话", session_id="h1")])
        self.source("operations", [dict(t="2026-10-15T02:00:00-07:00", type="skip", producer="system", text="fallback", session_id="s1")])
        _, _, payload = self.run_export()
        self.assertEqual(len(payload["records"]), 2)
        self.assertEqual(payload["records"][0]["reported_producer"], "system")
        self.assertEqual(payload["records"][1]["source_kind"], "host_export")
        self.assertEqual(payload["records"][1]["generation_origin"], "unknown")

    def test_duplicates_and_session_ids_are_preserved(self):
        row = dict(t=1792090800, **{"from":"qingxia", "to":"tangsanzang"}, text="同一句", session_id="p1")
        self.source("peer_private", [row, row, {**row,"session_id":"p2"}])
        _, _, payload = self.run_export()
        self.assertEqual([r["session_id"] for r in payload["records"]], ["p1","p1","p2"])
        self.assertEqual(len({r["source_pointer"] for r in payload["records"]}), 3)

    def test_corruption_stops_without_replacing_old_revision(self):
        p = self.source("group", [self.group()])
        _, first, _ = self.run_export()
        p.write_text("{bad json")
        with self.assertRaises(ValueError):self.run_export()
        self.assertFalse((first.parent / "r002").exists())
        archive.verify(first)

    def test_unknown_time_and_out_of_scope_actor_fail(self):
        for row in [self.group(t="2026-10-15T12:30:00"), self.group(speaker="unrelated-user")]:
            self.source("group", [row])
            with self.assertRaises(ValueError):self.run_export()

    def test_missing_and_available_empty_sources_differ(self):
        _, _, payload = self.run_export()
        self.assertEqual(set(payload["availability"].values()), {"missing"})
        self.source("group", [])
        _, dest, payload = self.run_export()
        self.assertEqual(dest.name, "r002")
        self.assertEqual(payload["availability"]["group"], "available")
        self.assertEqual(payload["coverage"], "not_attested")

    def test_tampering_detected(self):
        self.source("group", [self.group()])
        _, dest, _ = self.run_export()
        (dest / "conversations.zh-CN.md").write_text("modified")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):archive.verify(dest)
        with self.assertRaises(ValueError):self.run_export()


if __name__ == "__main__":
    unittest.main()
