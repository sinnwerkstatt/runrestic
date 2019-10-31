import json
import logging
import re

from runrestic.runrestic.tools import parse_size, parse_time, make_size

logger = logging.getLogger(__name__)


def repo_init_check(output: str):
    if "Is there a repository at the following location?" in output:
        logger.error(
            "\nIt seems like the repo is not initialized. Run `runrestic init`."
        )
        return
    raise Exception(f"Unknown problem: {output}")


def parse_backup(output: str) -> dict:
    files_new, files_changed, files_unmodified = re.findall(
        r"Files:\s+([0-9]+) new,\s+([0-9]+) changed,\s+([0-9]+) unmodified", output
    )[0]
    dirs_new, dirs_changed, dirs_unmodified = re.findall(
        r"Dirs:\s+([0-9]+) new,\s+([0-9]+) changed,\s+([0-9]+) unmodified", output
    )[0]
    added_to_the_repo = re.findall(
        r"Added to the repo:\s+(-?[0-9.]+ [a-zA-Z]*B)", output
    )[0]
    processed_files, processed_size, processed_time = re.findall(
        r"processed ([0-9]+) files,\s+(-?[0-9.]+ [a-zA-Z]*B) in ([0-9]+:+[0-9]+)",
        output,
    )[0]

    return {
        "files": {
            "new": files_new,
            "changed": files_changed,
            "unmodified": files_unmodified,
        },
        "dirs": {
            "new": dirs_new,
            "changed": dirs_changed,
            "unmodified": dirs_unmodified,
        },
        "processed": {
            "files": processed_files,
            "size_bytes": parse_size(processed_size),
            "duration_seconds": parse_time(processed_time),
        },
        "added_to_repo": parse_size(added_to_the_repo),
    }


def parse_forget(output: str) -> dict:
    re_removed_snapshots = re.findall(r"remove ([0-9]+) snapshots", output)
    return {"removed_snapshots": re_removed_snapshots[0] if re_removed_snapshots else 0}


def parse_prune(output: str) -> dict:
    containing_packs_before, containing_blobs_before, containing_size_before = re.findall(
        r"repository contains ([0-9]+) packs \(([0-9]+) blobs\) with (-?[0-9.]+ ?[a-zA-Z]*B)",
        output,
    )[
        0
    ]
    duplicate_blobs, duplicate_size = re.findall(
        r"([0-9]+) duplicate blobs, (-?[0-9.]+ ?[a-zA-Z]*B) duplicate", output
    )[0]
    in_use_blobs, _, removed_blobs = re.findall(
        r"found ([0-9]+) of ([0-9]+) data blobs still in use, removing ([0-9]+) blobs",
        output,
    )[0]
    invalid_files = re.findall(r"will remove ([0-9]+) invalid files", output)[0]
    deleted_packs, rewritten_packs, size_freed = re.findall(
        r"will delete ([0-9]+) packs and rewrite ([0-9]+) packs, this frees (-?[0-9.]+ ?[a-zA-Z]*B)",
        output,
    )[0]
    removed_index_files = re.findall(r"remove ([0-9]+) old index files", output)[0]

    return {
        "containing_packs_before": containing_packs_before,
        "containing_blobs": containing_blobs_before,
        "containing_size_bytes": parse_size(containing_size_before),
        "duplicate_blobs": duplicate_blobs,
        "duplicate_size_bytes": parse_size(duplicate_size),
        "in_use_blobs": in_use_blobs,
        "removed_blobs": removed_blobs,
        "invalid_files": invalid_files,
        "deleted_packs": deleted_packs,
        "rewritten_packs": rewritten_packs,
        "size_freed_bytes": parse_size(size_freed),
        "removed_index_files": removed_index_files,
    }


def parse_stats(output: str) -> dict:
    stats_json = json.loads(output)
    logger.debug(
        f"Total File Count: {stats_json['total_file_count']}\n"
        f"Total Size: {make_size(stats_json['total_size'])}"
    )
    return stats_json
