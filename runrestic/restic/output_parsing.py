import json
import logging
import re
from typing import Any, Dict

from runrestic.runrestic.tools import parse_size, parse_time

logger = logging.getLogger(__name__)


def parse_backup(process_infos: Dict[str, Any]) -> Dict[str, Any]:
    rc, output = process_infos["output"][-1]
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
        "duration_seconds": process_infos["time"],
        "rc": rc,
    }


def parse_forget(process_infos: Dict[str, Any]) -> Dict[str, Any]:
    rc, output = process_infos["output"][-1]
    re_removed_snapshots = re.findall(r"remove ([0-9]+) snapshots", output)
    return {
        "removed_snapshots": re_removed_snapshots[0] if re_removed_snapshots else 0,
        "duration_seconds": process_infos["time"],
        "rc": rc,
    }


def parse_prune(process_infos: Dict[str, Any]) -> Dict[str, Any]:
    rc, output = process_infos["output"][-1]
    containing_packs, containing_blobs, containing_size = re.findall(
        r"repository contains ([0-9]+) packs \(([0-9]+) blobs\) with (-?[0-9.]+ ?[a-zA-Z]*B)",
        output,
    )[0]
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
        "containing_packs_before": containing_packs,
        "containing_blobs": containing_blobs,
        "containing_size_bytes": parse_size(containing_size),
        "duplicate_blobs": duplicate_blobs,
        "duplicate_size_bytes": parse_size(duplicate_size),
        "in_use_blobs": in_use_blobs,
        "removed_blobs": removed_blobs,
        "invalid_files": invalid_files,
        "deleted_packs": deleted_packs,
        "rewritten_packs": rewritten_packs,
        "size_freed_bytes": parse_size(size_freed),
        "removed_index_files": removed_index_files,
        "duration_seconds": process_infos["time"],
        "rc": rc,
    }


def parse_stats(process_infos: Dict[str, Any]) -> Dict[str, Any]:
    rc, output = process_infos["output"][-1]
    stats_json = json.loads(output)
    return {
        "total_file_count": stats_json["total_file_count"],
        "total_size_bytes": stats_json["total_size"],
        "duration_seconds": process_infos["time"],
        "rc": rc,
    }
