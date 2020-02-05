from runrestic.metrics import write_metrics


def test_write_metrics(tmpdir):
    metrics = {
        "backup": {
            "_restic_pre_hooks": {"duration_seconds": 2, "rc": 0},
            "_restic_post_hooks": {"duration_seconds": 2, "rc": 0},
            "repo1": {
                "files": {"new": "1", "changed": "2", "unmodified": "3"},
                "dirs": {"new": "1", "changed": "2", "unmodified": "3"},
                "processed": {"files": "1", "size_bytes": 2, "duration_seconds": 3},
                "added_to_repo": 2,
                "duration_seconds": 4,
                "rc": 0,
            },
            "repo2": {
                "files": {"new": "1", "changed": "2", "unmodified": "3"},
                "dirs": {"new": "1", "changed": "2", "unmodified": "3"},
                "processed": {"files": "1", "size_bytes": 2, "duration_seconds": 3},
                "added_to_repo": 2,
                "duration_seconds": 4,
                "rc": 0,
            },
        },
        "forget": {
            "repo1": {"removed_snapshots": "1", "duration_seconds": 3.2, "rc": 0,},
            "repo2": {"removed_snapshots": "1", "duration_seconds": 3.3, "rc": 0,},
        },
        "prune": {
            "/tmp/restic-repo1": {
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
                "duration_seconds": 4.2081992626190186,
                "rc": 0,
            },
            "/tmp/restic-repo2": {
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
                "rc": 0,
            },
        },
        "check": {
            "/tmp/restic-repo1": {
                "errors": 0,
                "errors_data": 0,
                "errors_snapshots": 0,
                "read_data": 1,
                "check_unused": 1,
                "duration_seconds": 28.380418062210083,
                "rc": 0,
            },
            "/tmp/restic-repo2": {
                "errors": 0,
                "errors_data": 0,
                "errors_snapshots": 0,
                "read_data": 1,
                "check_unused": 1,
                "duration_seconds": 28.380418062210083,
                "rc": 0,
            },
        },
        "stats": {
            "/tmp/restic-repo1": {
                "total_file_count": 885276,
                "total_size_bytes": 18148185424,
                "duration_seconds": 20.471401691436768,
                "rc": 0,
            },
            "/tmp/restic-repo2": {
                "total_file_count": 885276,
                "total_size_bytes": 18148185424,
                "duration_seconds": 20.466784715652466,
                "rc": 0,
            },
        },
        "last_run": 1575577432.185576,
        "total_duration_seconds": 62.44408392906189,
    }

    cfg = {
        "name": "test",
        "metrics": {"prometheus": {"path": tmpdir.join("example.prom")}},
    }
    write_metrics(metrics, cfg)
