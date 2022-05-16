"""Test the restic output parsing"""

from runrestic.restic import output_parsing


def test_parse_backup():
    """Validate that all backup details are correctly captured"""
    output = """repository c2e84608 opened successfully, password is correct
created new cache in /home/user/.cache/restic
found 2 old cache directories in /home/user/.cache/restic, run `restic cache --cleanup` to remove them
no parent snapshot found, will read all files

Files:       22391 new,    42 changed,     5 unmodified
Dirs:         2927 new,     1 changed,     3 unmodified
Added to the repo: 259.569 MiB

processed 22438 files, 302.750 MiB in 1:12
snapshot 215cf0fa saved"""
    data = {
        "files": {
            "new": "22391",
            "changed": "42",
            "unmodified": "5",
        },
        "dirs": {
            "new": "2927",
            "changed": "1",
            "unmodified": "3",
        },
        "processed": {
            "files": "22438",
            "size_bytes": 302.750 * 2**20,
            "duration_seconds": 72,
        },
        "added_to_repo": 259.569 * 2**20,
        "duration_seconds": 35.8,
        "rc": 0,
    }
    process_infos = {"output": [(0, output)], "time": data["duration_seconds"]}
    result = output_parsing.parse_backup(process_infos)
    assert result == data


def test_parse_forget():
    """Validate that all forget details are correctly captured"""
    output = """repository c2e84608 opened successfully, password is correct
found 2 old cache directories in /home/user/.cache/restic, run `restic cache --cleanup` to remove them
Applying Policy: keep 2 latest snapshots
keep 2 snapshots:
ID        Time                 Host        Tags        Reasons        Paths
--------------------------------------------------------------------------------------------------
04ffe2e5  2022-05-27 15:01:41  cubitus                 last snapshot  /home/user/git/runrestic
611527ee  2022-05-27 15:01:53  cubitus                 last snapshot  /home/user/git/runrestic
--------------------------------------------------------------------------------------------------
2 snapshots

remove 1 snapshots:
ID        Time                 Host        Tags        Paths
-----------------------------------------------------------------------------------
215cf0fa  2022-05-27 14:42:40  cubitus                 /home/user/git/runrestic
-----------------------------------------------------------------------------------
1 snapshots

[0:00] 100.00%  1 / 1 files deleted"""
    data = {
        "removed_snapshots": "1",
        "duration_seconds": 12.7,
        "rc": 0,
    }
    process_infos = {"output": [(0, output)], "time": data["duration_seconds"]}
    result = output_parsing.parse_forget(process_infos)
    assert result == data


def test_parse_prune():
    """Validate that all prune details are correctly captured (version < 12.0)"""
    output = """password is correct
storage ID 9babef79
counting files in repo
building new index for repo
[2:16] 100.00% 11981 / 11981 packs
repository contains 11981 packs (345057 blobs) with 56.676 GiB
processed 345057 blobs: 0 duplicate blobs, 0B duplicate
load all snapshots
find data that is still in use for 1 snapshots
[0:00] 100.00% 1 / 1 snapshots
found 2 of 345057 data blobs still in use, removing 345055 blobs
will remove 0 invalid files
will delete 11979 packs and rewrite 0 packs, this frees 56.664 GiB
counting files in repo
[0:00] 100.00% 2 / 2 packs
finding old index files
saved new indexes as [70561784]
remove 11 old index files
[1:12] 100.00% 11979 / 11979 packs deleted
done"""
    data = {
        "containing_packs_before": "11981",
        "containing_blobs": "345057",
        "containing_size_bytes": 56.676 * 2**30,
        "duplicate_blobs": "0",
        "duplicate_size_bytes": 0.0,
        "in_use_blobs": "2",
        "removed_blobs": "345055",
        "invalid_files": "0",
        "deleted_packs": "11979",
        "rewritten_packs": "0",
        "size_freed_bytes": 56.664 * 2**30,
        "removed_index_files": "11",
        "duration_seconds": 3.27,
        "rc": 0,
    }
    process_infos = {"output": [(0, output)], "time": data["duration_seconds"]}
    result = output_parsing.parse_prune(process_infos)
    assert result == data


def test_parse_new_prune():
    """Validate that all prune details are correctly captured (version >= 12.0)"""
    output = """repository c2e84608 opened successfully, password is correct
found 2 old cache directories in /home/user/.cache/restic, run `restic cache --cleanup` to remove them
loading indexes...
loading all snapshots...
finding data that is still in use for 1 snapshots
[0:00] 100.00%  1 / 1 snapshots
searching used packs...
collecting packs for deletion and repacking
[0:00] 100.00%  65 / 65 packs processed

to repack:             1 blobs / 1234 B
this removes:          2 blobs / 5678 B
to delete:            32 blobs / 158.830 KiB
total prune:          35 blobs / 158.830 KiB
remaining:         19154 blobs / 260.161 MiB
unused size after prune: 0 B (0.00% of remaining size)

rebuilding index
[0:00] 100.00%  62 / 62 packs processed
deleting obsolete index files
[0:00] 100.00%  2 / 2 files deleted
removing 3 old packs
[0:00] 100.00%  3 / 3 files deleted
done"""
    data = {
        "to_repack_blobs": "1",
        "to_repack_bytes": 1234.0,
        "removed_blobs": "2",
        "removed_bytes": 5678.0,
        "to_delete_blobs": "32",
        "to_delete_bytes": 158.830 * 2**10,
        "total_prune_blobs": "35",
        "total_prune_bytes": 158.830 * 2**10,
        "remaining_blobs": "19154",
        "remaining_bytes": 260.161 * 2**20,
        "remaining_unused_size": 0.0,
        "duration_seconds": 8.47,
        "rc": 0,
    }
    process_infos = {"output": [(0, output)], "time": data["duration_seconds"]}
    result = output_parsing.parse_new_prune(process_infos)
    assert result == data


def test_parse_stats_quiet():
    """Validate that all stats are correctly captured"""
    output = '{"total_size":317458353,"total_file_count":50653}'
    data = {
        "total_file_count": 50653,
        "total_size_bytes": 317458353,
        "duration_seconds": 1.57,
        "rc": 0,
    }
    process_infos = {"output": [(0, output)], "time": data["duration_seconds"]}
    result = output_parsing.parse_stats(process_infos)
    assert result == data


def test_parse_stats_verbose():
    """Validate that all stats are correctly captured"""
    output = """found 2 old cache directories in /home/user/.cache/restic, run `restic cache --cleanup` to remove them
{"total_size":317458353,"total_file_count":50653}"""
    data = {
        "total_file_count": 50653,
        "total_size_bytes": 317458353,
        "duration_seconds": 1.57,
        "rc": 0,
    }
    process_infos = {"output": [(0, output)], "time": data["duration_seconds"]}
    result = output_parsing.parse_stats(process_infos)
    assert result == data
