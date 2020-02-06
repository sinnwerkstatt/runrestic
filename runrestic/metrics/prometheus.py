from typing import Any, Dict, Iterator

_restic = """
restic_last_run{{config="{name}"}} {last_run}
restic_total_duration_seconds{{config="{name}"}} {total_duration_seconds}
"""

_restic_pre_hooks = """
restic_pre_hooks_duration_seconds{{config="{name}"}} {duration_seconds}
restic_pre_hooks_rc{{config="{name}"}} {rc}
"""

_restic_post_hooks = """
restic_post_hooks_duration_seconds{{config="{name}"}} {duration_seconds}
restic_post_hooks_rc{{config="{name}"}} {rc}
"""

_restic_backup = """
restic_backup_files_new{{config="{name}",repository="{repository}"}} {files[new]}
restic_backup_files_changed{{config="{name}",repository="{repository}"}} {files[changed]}
restic_backup_files_unmodified{{config="{name}",repository="{repository}"}} {files[unmodified]}
restic_backup_dirs_new{{config="{name}",repository="{repository}"}} {dirs[new]}
restic_backup_dirs_changed{{config="{name}",repository="{repository}"}} {dirs[changed]}
restic_backup_dirs_unmodified{{config="{name}",repository="{repository}"}} {dirs[unmodified]}
restic_backup_processed_files{{config="{name}",repository="{repository}"}} {processed[files]}
restic_backup_processed_size_bytes{{config="{name}",repository="{repository}"}} {processed[size_bytes]}
restic_backup_processed_duration_seconds{{config="{name}",repository="{repository}"}} {processed[duration_seconds]}
restic_backup_added_to_repo{{config="{name}",repository="{repository}"}} {added_to_repo}
restic_backup_duration_seconds{{config="{name}",repository="{repository}"}} {duration_seconds}
restic_backup_rc{{config="{name}",repository="{repository}"}} {rc}
"""

_restic_forget = """
restic_forget_removed_snapshots{{config="{name}",repository="{repository}"}} {removed_snapshots}
restic_forget_duration_seconds{{config="{name}",repository="{repository}"}} {duration_seconds}
restic_forget_rc{{config="{name}",repository="{repository}"}} {rc}
"""

_restic_prune = """
restic_prune_containing_packs_before{{config="{name}",repository="{repository}"}} {containing_packs_before}
restic_prune_containing_blobs{{config="{name}",repository="{repository}"}} {containing_blobs}
restic_prune_containing_size_bytes{{config="{name}",repository="{repository}"}} {containing_size_bytes}
restic_prune_duplicate_blobs{{config="{name}",repository="{repository}"}} {duplicate_blobs}
restic_prune_duplicate_size_bytes{{config="{name}",repository="{repository}"}} {duplicate_size_bytes}
restic_prune_in_use_blobs{{config="{name}",repository="{repository}"}} {in_use_blobs}
restic_prune_removed_blobs{{config="{name}",repository="{repository}"}} {removed_blobs}
restic_prune_invalid_files{{config="{name}",repository="{repository}"}} {invalid_files}
restic_prune_deleted_packs{{config="{name}",repository="{repository}"}} {deleted_packs}
restic_prune_rewritten_packs{{config="{name}",repository="{repository}"}} {rewritten_packs}
restic_prune_size_freed_bytes{{config="{name}",repository="{repository}"}} {size_freed_bytes}
restic_prune_removed_index_files{{config="{name}",repository="{repository}"}} {removed_index_files}
restic_prune_duration_seconds{{config="{name}",repository="{repository}"}} {duration_seconds}
restic_prune_rc{{config="{name}",repository="{repository}"}} {rc}
"""

_restic_check = """
restic_check_errors{{config="{name}",repository="{repository}"}} {errors}
restic_check_errors_data{{config="{name}",repository="{repository}"}} {errors_data}
restic_check_errors_snapshots{{config="{name}",repository="{repository}"}} {errors_snapshots}
restic_check_read_data{{config="{name}",repository="{repository}"}} {read_data}
restic_check_check_unused{{config="{name}",repository="{repository}"}} {check_unused}
restic_check_duration_seconds{{config="{name}",repository="{repository}"}} {duration_seconds}
restic_check_rc{{config="{name}",repository="{repository}"}} {rc}
"""

_restic_stats = """
restic_stats_total_file_count{{config="{name}",repository="{repository}"}} {total_file_count}
restic_stats_total_size_bytes{{config="{name}",repository="{repository}"}} {total_size_bytes}
restic_stats_duration_seconds{{config="{name}",repository="{repository}"}} {duration_seconds}
restic_stats_rc{{config="{name}",repository="{repository}"}} {rc}
"""


def generate_lines(metrics: Dict[str, Any], name: str) -> Iterator[str]:
    yield _restic.format(name=name, **metrics)

    for repo, mtrx in metrics.get("backup", {}).items():
        if repo == "_restic_pre_hooks":
            yield _restic_pre_hooks.format(name=name, **mtrx)
        elif repo == "_restic_post_hooks":
            yield _restic_post_hooks.format(name=name, **mtrx)
        else:
            yield _restic_backup.format(name=name, repository=repo, **mtrx)

    for repo, mtrx in metrics.get("forget", {}).items():
        yield _restic_forget.format(name=name, repository=repo, **mtrx)
    for repo, mtrx in metrics.get("prune", {}).items():
        yield _restic_prune.format(name=name, repository=repo, **mtrx)

    for repo, mtrx in metrics.get("check", {}).items():
        yield _restic_check.format(name=name, repository=repo, **mtrx)

    for repo, mtrx in metrics.get("stats", {}).items():
        yield _restic_stats.format(name=name, repository=repo, **mtrx)


def write_file(lines: str, path: str) -> None:
    with open(path, "w") as file:
        file.writelines(lines)
