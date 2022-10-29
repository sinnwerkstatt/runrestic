import json
import logging
import re
from typing import Any, Dict

from runrestic.runrestic.tools import parse_line, parse_size, parse_time

logger = logging.getLogger(__name__)


def parse_backup(process_infos: Dict[str, Any]) -> Dict[str, Any]:
    return_code, output = process_infos["output"][-1]
    logger.debug("Parsing backup output: %s", output)

    files_new, files_changed, files_unmodified = parse_line(
        r"Files:\s+([0-9]+) new,\s+([0-9]+) changed,\s+([0-9]+) unmodified",
        output,
        ("0", "0", "0"),
    )
    dirs_new, dirs_changed, dirs_unmodified = parse_line(
        r"Dirs:\s+([0-9]+) new,\s+([0-9]+) changed,\s+([0-9]+) unmodified",
        output,
        ("0", "0", "0"),
    )
    added_to_the_repo = parse_line(
        r"Added to the repo\w*:\s+(-?[0-9.]+ [a-zA-Z]*B)",
        output,
        "0 B",
    )
    processed_files, processed_size, processed_time = parse_line(
        r"processed ([0-9]+) files,\s+(-?[0-9.]+ [a-zA-Z]*B) in ([0-9]+:+[0-9]+)",
        output,
        ("0", "0 B", "00:00"),
    )

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
        "rc": return_code,
    }


def parse_forget(process_infos: Dict[str, Any]) -> Dict[str, Any]:
    return_code, output = process_infos["output"][-1]
    re_removed_snapshots = parse_line(r"remove ([0-9]+) snapshots", output, "0")
    return {
        "removed_snapshots": re_removed_snapshots,
        "duration_seconds": process_infos["time"],
        "rc": return_code,
    }


def parse_prune(process_infos: Dict[str, Any]) -> Dict[str, Any]:
    return_code, output = process_infos["output"][-1]
    containing_packs, containing_blobs, containing_size = parse_line(
        r"repository contains ([0-9]+) packs \(([0-9]+) blobs\) with (-?[0-9.]+ ?[a-zA-Z]*B)",
        output,
        ("0", "0", "0 B"),
    )
    duplicate_blobs, duplicate_size = parse_line(
        r"([0-9]+) duplicate blobs, (-?[0-9.]+ ?[a-zA-Z]*B) duplicate",
        output,
        ("0", "0 B"),
    )
    in_use_blobs, _, removed_blobs = parse_line(
        r"found ([0-9]+) of ([0-9]+) data blobs still in use, removing ([0-9]+) blobs",
        output,
        ("0", "0", "0"),
    )
    invalid_files = parse_line(r"will remove ([0-9]+) invalid files", output, ("0"))
    deleted_packs, rewritten_packs, size_freed = parse_line(
        r"will delete ([0-9]+) packs and rewrite ([0-9]+) packs, this frees (-?[0-9.]+ ?[a-zA-Z]*B)",
        output,
        ("0", "0", "0 B"),
    )
    removed_index_files = parse_line(r"remove ([0-9]+) old index files", output, "0")

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
        "rc": return_code,
    }


def parse_new_prune(process_infos: Dict[str, Any]) -> Dict[str, Any]:
    return_code, output = process_infos["output"][-1]

    to_repack_blobs, to_repack_bytes = parse_line(
        r"to repack:[\s]+([0-9]+) blobs / (-?[0-9.]+ ?[a-zA-Z]*B)",
        output,
        ("0", "0 B"),
    )
    removed_blobs, removed_bytes = parse_line(
        r"this removes[:]*[\s]+([0-9]+) blobs / (-?[0-9.]+ ?[a-zA-Z]*B)",
        output,
        ("0", "0 B"),
    )
    to_delete_blobs, to_delete_bytes = parse_line(
        r"to delete:[\s]+([0-9]+) blobs / (-?[0-9.]+ ?[a-zA-Z]*B)",
        output,
        ("0", "0 B"),
    )
    total_prune_blobs, total_prune_bytes = parse_line(
        r"total prune:[\s]+([0-9]+) blobs / (-?[0-9.]+ ?[a-zA-Z]*B)",
        output,
        ("0", "0 B"),
    )
    remaining_blobs, remaining_bytes = parse_line(
        r"remaining:[\s]+([0-9]+) blobs / (-?[0-9.]+ ?[a-zA-Z]*B)",
        output,
        ("0", "0 B"),
    )
    remaining_unused_size = parse_line(
        r"unused size after prune:[\s]+(-?[0-9.]+ ?[a-zA-Z]*B)",
        output,
        "0 B",
    )
    return {
        "to_repack_blobs": to_repack_blobs,
        "to_repack_bytes": parse_size(to_repack_bytes),
        "removed_blobs": removed_blobs,
        "removed_bytes": parse_size(removed_bytes),
        "to_delete_blobs": to_delete_blobs,
        "to_delete_bytes": parse_size(to_delete_bytes),
        "total_prune_blobs": total_prune_blobs,
        "total_prune_bytes": parse_size(total_prune_bytes),
        "remaining_blobs": remaining_blobs,
        "remaining_bytes": parse_size(remaining_bytes),
        "remaining_unused_size": parse_size(remaining_unused_size),
        "duration_seconds": process_infos["time"],
        "rc": return_code,
    }


def parse_stats(process_infos: Dict[str, Any]) -> Dict[str, Any]:
    return_code, output = process_infos["output"][-1]
    try:
        stats_json = json.loads(re.findall(r"(\{.*\})", output, re.MULTILINE)[0])
        return {
            "total_file_count": stats_json["total_file_count"],
            "total_size_bytes": stats_json["total_size"],
            "duration_seconds": process_infos["time"],
            "rc": return_code,
        }
    except KeyError as err:
        logger.error("Key %s not found in output: %s", err, output)
        return {
            "total_file_count": 0,
            "total_size_bytes": 0,
            "duration_seconds": 0,
            "rc": return_code,
        }
