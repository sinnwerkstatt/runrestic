from typing import Any
from unittest import TestCase
from unittest.mock import mock_open, patch

from runrestic.metrics import prometheus, write_metrics


class TestResticMetrics(TestCase):
    @patch("builtins.open", new_callable=mock_open)
    @patch(
        "runrestic.metrics.prometheus.generate_lines",
        return_value=["line1\n", "line2\n"],
    )
    def test_write_metrics(self, mock_generate_lines, mock_open):
        cfg = {
            "name": "test",
            "metrics": {"prometheus": {"path": "/prometheus_path"}},
        }
        metrics = {
            "backup": {
                "repo1": {
                    "files": {"new": "1", "changed": "2", "unmodified": "3"},
                },
            }
        }
        write_metrics(metrics, cfg)
        mock_generate_lines.assert_called_once_with(metrics, "test")
        mock_open.assert_called_once_with("/prometheus_path", "w")
        fh = mock_open()
        fh.writelines.assert_called_once_with("line1\nline2\n")

    @patch(
        "runrestic.metrics.prometheus.generate_lines",
        return_value=["line1\n", "line2\n"],
    )
    def test_write_metrics_skipped(self, mock_generate_lines):
        cfg = {
            "name": "test",
            "metrics": {"unknown": {"path": "/other_path"}},
        }
        metrics = {"dummy": "metrics"}
        write_metrics(metrics, cfg)
        mock_generate_lines.assert_not_called()


def mock_metrics_func(metrics, name):
    return f"{name}: {metrics}"


class TestResticMetricsPrometheus(TestCase):
    def setUp(self) -> None:
        prometheus._restic_help_pre_hooks = "restic_help_pre_hooks|"
        prometheus._restic_pre_hooks = "pre:{name}:{rc}:{duration_seconds}|"
        prometheus._restic_help_post_hooks = "restic_help_post_hooks|"
        prometheus._restic_post_hooks = "post:{name}:{rc}:{duration_seconds}|"

    # def setUp(self) -> None:
    #     self.temp_dir: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory()
    #     self.prometheus_path = Path(self.temp_dir.name) / "example.prom"
    #     self.prometheus_path.mkdir()

    # def tearDown(self) -> None:
    #     self.temp_dir.cleanup()

    @patch("runrestic.metrics.prometheus.backup_metrics", wraps=mock_metrics_func)
    @patch("runrestic.metrics.prometheus.forget_metrics", wraps=mock_metrics_func)
    @patch("runrestic.metrics.prometheus.prune_metrics", wraps=mock_metrics_func)
    @patch("runrestic.metrics.prometheus.check_metrics", wraps=mock_metrics_func)
    @patch("runrestic.metrics.prometheus.stats_metrics", wraps=mock_metrics_func)
    def test_generate_lines(
        self,
        mock_stats_metrics,
        mock_check_metrics,
        mock_prune_metrics,
        mock_forget_metrics,
        mock_backup_metrics,
    ):
        scenarios: list[dict[str, Any]] = [
            {
                "name": "all_metrics",
                "metrics": {
                    "backup": {"backup_metrics": 1},
                    "forget": {"forget_metrics": 2},
                    "prune": {"prune_metrics": 3},
                    "check": {"check_metrics": 4},
                    "stats": {"stats_metrics": 5},
                },
            },
            {
                "name": "backup_metrics",
                "metrics": {
                    "backup": {"backup_metrics": 1},
                },
            },
            {
                "name": "no_metrics",
                "metrics": {},
            },
        ]
        genral_metrics = {
            "errors": 10,
            "last_run": 11,
            "total_duration_seconds": 12,
        }
        prometheus._restic_help_general = "restic_help_general"
        prometheus._restic_general = "restic_general:{name}:{last_run}:{errors}:{total_duration_seconds}"
        for sc in scenarios:
            with self.subTest(sc["name"]):
                expected_lines = [
                    "restic_help_general",
                    f"restic_general:{sc['name']}:11:10:12",
                ] + [f"{sc['name']}: {value}" for value in sc["metrics"].values()]
                metrics = sc["metrics"] | genral_metrics
                lines = prometheus.generate_lines(metrics, sc["name"])
                self.assertEqual(list(lines), expected_lines)

    def test_backup_metrics(self):
        scenarios: list[dict[str, Any]] = [
            {
                "name": "pre_and_post_hooks",
                "metrics": {
                    "_restic_pre_hooks": {"duration_seconds": 2, "rc": 0},
                    "_restic_post_hooks": {"duration_seconds": 4, "rc": 0},
                    "repo1": {
                        "files": {"new": "1", "changed": "2", "unmodified": "3"},
                        "dirs": {"new": "1", "changed": "2", "unmodified": "3"},
                        "processed": {
                            "files": "1",
                            "size_bytes": 2,
                            "duration_seconds": 3,
                        },
                        "added_to_repo": 7,
                        "duration_seconds": 9,
                        "rc": 0,
                    },
                    "repo2": {
                        "files": {"new": "1", "changed": "2", "unmodified": "3"},
                        "dirs": {"new": "1", "changed": "2", "unmodified": "3"},
                        "processed": {
                            "files": "1",
                            "size_bytes": 2,
                            "duration_seconds": 3,
                        },
                        "added_to_repo": 5,
                        "duration_seconds": 8,
                        "rc": 1,
                    },
                },
                "expected_lines": [
                    "restic_help_backup",
                    "restic_help_pre_hooks",
                    "restic_help_post_hooks",
                    "pre:my_backup:0:2",
                    "post:my_backup:0:4",
                    "restic_backup_data:my_backup:7:9",
                    'restic_backup_rc{config="my_backup",repository="repo2"} 1\n',
                ],
            },
            {
                "name": "without_hooks",
                "metrics": {
                    "repo1": {
                        "files": {"new": "1", "changed": "2", "unmodified": "3"},
                        "dirs": {"new": "1", "changed": "2", "unmodified": "3"},
                        "processed": {
                            "files": "1",
                            "size_bytes": 2,
                            "duration_seconds": 3,
                        },
                        "added_to_repo": 7,
                        "duration_seconds": 9,
                        "rc": 0,
                    },
                    "repo2": {
                        "files": {"new": "1", "changed": "2", "unmodified": "3"},
                        "dirs": {"new": "1", "changed": "2", "unmodified": "3"},
                        "processed": {
                            "files": "1",
                            "size_bytes": 2,
                            "duration_seconds": 3,
                        },
                        "added_to_repo": 5,
                        "duration_seconds": 8,
                        "rc": 1,
                    },
                },
                "expected_lines": [
                    "restic_help_backup",
                    "restic_backup_data:my_backup:7:9",
                    'restic_backup_rc{config="my_backup",repository="repo2"} 1\n',
                ],
            },
        ]
        # check that backup_metrics can be called with sample metrics
        # this validates that the `_restic_backup` template matches the data
        _lines = prometheus.backup_metrics(scenarios[0]["metrics"], "my_backup")
        # check call with simplified output
        prometheus._restic_help_backup = "restic_help_backup|"
        prometheus._restic_backup = "restic_backup_data:{name}:{added_to_repo}:{duration_seconds}|"
        for sc in scenarios:
            with self.subTest(sc["name"]):
                lines = prometheus.backup_metrics(sc["metrics"], "my_backup")
                self.assertEqual(
                    lines,
                    "|".join(sc["expected_lines"]),
                )

    def test_forget_metrics(self):
        metrics = {
            "repo1": {
                "removed_snapshots": "7",
                "duration_seconds": 9,
                "rc": 0,
            },
            "repo2": {
                "removed_snapshots": "2",
                "duration_seconds": 4.4,
                "rc": 1,
            },
        }
        # check that forget_metrics can be called with sample metrics
        _lines = prometheus.forget_metrics(metrics, "my_forget")
        # check call with simplified output
        prometheus._restic_help_forget = "restic_help_forget|"
        prometheus._restic_forget = "restic_forget_data:{name}:{removed_snapshots}:{duration_seconds}|"
        lines = prometheus.forget_metrics(metrics, "my_forget")
        self.assertEqual(
            lines,
            "|".join([
                "restic_help_forget",
                "restic_forget_data:my_forget:7:9",
                'restic_forget_rc{config="my_forget",repository="repo2"} 1\n',
            ]),
        )

    def test_new_prune_metrics(self):
        metrics = {
            "/tmp/restic-repo1": {  # noqa: S108
                "containing_packs_before": "576",
                "containing_blobs": "95060",
                "containing_size_bytes": 2764885196.8,
                "duplicate_blobs": "0",
                "duplicate_size_bytes": 0.0,
                "in_use_blobs": "95055",
                "removed_blobs": "5",
                "invalid_files": "0",
                "deleted_packs": "2",
                "rewritten_packs": "0",
                "size_freed_bytes": 16679.936,
                "removed_index_files": "2",
                "duration_seconds": 4.2,
                "rc": 0,
            },
            # data block with old prune metrics
            "/tmp/restic-repo2": {  # noqa: S108
                "to_repack_blobs": "864",
                # "containing_blobs": "95060",
                "to_repack_bytes": 2764885196.8,
                "removed_blobs": "11",
                "removed_bytes": 42.0,
                "to_delete_blobs": "96358",
                "to_delete_bytes": 5249.936,
                "total_prune_blobs": "5",
                "total_prune_bytes": 85176.225,
                "remaining_blobs": "2",
                "remaining_bytes": 52.244,
                "remaining_unused_size": 16679.936,
                "duration_seconds": 7.3,
                "rc": 0,
            },
            # data block with new prune metrics and rc > 0
            "/tmp/restic-repo3": {  # noqa: S108
                "containing_packs_before": "575",
                "containing_blobs": "95052",
                "containing_size_bytes": 2765958938.624,
                "duplicate_blobs": "0",
                "duplicate_size_bytes": 0.0,
                "in_use_blobs": "95047",
                "removed_blobs": "5",
                "invalid_files": "0",
                "deleted_packs": "2",
                "rewritten_packs": "0",
                "size_freed_bytes": 16613.376,
                "removed_index_files": "2",
                "duration_seconds": 4.281890153884888,
                "rc": 1,
            },
        }
        # check that prune_metrics can be called with sample metrics
        _lines = prometheus.prune_metrics(metrics, "my_prune")
        # check call with simplified output
        prometheus._restic_help_prune = "restic_help_prune|"
        prometheus._restic_prune = "restic_prune_data:{name}:{containing_packs_before}:{duration_seconds}|"
        prometheus._restic_new_prune = "restic_prune_data:{name}:{to_repack_blobs}:{duration_seconds}|"
        lines = prometheus.prune_metrics(metrics, "my_prune")
        self.assertEqual(
            lines,
            "|".join([
                "restic_help_prune",
                "restic_prune_data:my_prune:576:4.2",
                "restic_prune_data:my_prune:864:7.3",
                'restic_prune_rc{config="my_prune",repository="/tmp/restic-repo3"} 1\n',
            ]),
        )

    def test_check_metrics(self):
        metrics = {
            "/tmp/restic-repo1": {  # noqa: S108
                "errors": 0,
                "errors_data": 0,
                "errors_snapshots": 7,
                "read_data": 1,
                "check_unused": 1,
                "duration_seconds": 9,
                "rc": 0,
            },
            "/tmp/restic-repo2": {  # noqa: S108
                "errors": 0,
                "errors_data": 0,
                "errors_snapshots": 0,
                "read_data": 1,
                "check_unused": 1,
                "duration_seconds": 28.380418062210083,
                "rc": 1,
            },
        }
        # check that check_metrics can be called with sample metrics
        _lines = prometheus.check_metrics(metrics, "my_check")
        # check call with simplified output
        prometheus._restic_help_check = "restic_help_check|"
        prometheus._restic_check = "restic_check_data:{name}:{errors_snapshots}:{duration_seconds}|"
        lines = prometheus.check_metrics(metrics, "my_check")
        self.assertEqual(
            lines,
            "|".join([
                "restic_help_check",
                "restic_check_data:my_check:7:9",
                'restic_check_rc{config="my_check",repository="/tmp/restic-repo2"} 1\n',
            ]),
        )

    def test_stats_metrics(self):
        metrics = {
            "/tmp/restic-repo1": {  # noqa: S108
                "total_file_count": 7,
                "total_size_bytes": 18148185424,
                "duration_seconds": 9,
                "rc": 0,
            },
            "/tmp/restic-repo2": {  # noqa: S108
                "total_file_count": 885276,
                "total_size_bytes": 18148185424,
                "duration_seconds": 20.466784715652466,
                "rc": 1,
            },
        }
        # stats that stats_metrics can be called with sample metrics
        _lines = prometheus.stats_metrics(metrics, "my_stats")
        # stats call with simplified output
        prometheus._restic_help_stats = "restic_help_stats|"
        prometheus._restic_stats = "restic_stats_data:{name}:{total_file_count}:{duration_seconds}|"
        lines = prometheus.stats_metrics(metrics, "my_stats")
        self.assertEqual(
            lines,
            "|".join([
                "restic_help_stats",
                "restic_stats_data:my_stats:7:9",
                'restic_stats_rc{config="my_stats",repository="/tmp/restic-repo2"} 1\n',
            ]),
        )
