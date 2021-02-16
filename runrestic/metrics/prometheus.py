from typing import Any, Dict, Iterator

_restic_help_general = """
# HELP restic_last_run Epoch timestamp of the last run
# TYPE restic_last_run gauge
# HELP restic_total_duration_seconds Total duration in seconds
# TYPE restic_total_duration_seconds gauge
# HELP restic_total_errors Total amount of errors within the last run
# TYPE restic_total_errors gauge
"""
_restic_general = """
restic_last_run{{config="{name}"}} {last_run}
restic_total_duration_seconds{{config="{name}"}} {total_duration_seconds}
restic_total_errors{{config="{name}"}} {errors}
"""

_restic_help_pre_hooks = """
# HELP restic_pre_hooks_duration_seconds Pre hooks duration in seconds
# TYPE restic_pre_hooks_duration_seconds gauge
# HELP restic_pre_hooks_rc Pre hooks return code
# TYPE restic_pre_hooks_rc gauge
"""
_restic_pre_hooks = """
restic_pre_hooks_duration_seconds{{config="{name}"}} {duration_seconds}
restic_pre_hooks_rc{{config="{name}"}} {rc}
"""

_restic_help_post_hooks = """
# HELP restic_post_hooks_duration_seconds Post hooks duration in seconds
# TYPE restic_post_hooks_duration_seconds gauge
# HELP restic_post_hooks_rc Post hooks return code
# TYPE restic_post_hooks_rc gauge
"""
_restic_post_hooks = """
restic_post_hooks_duration_seconds{{config="{name}"}} {duration_seconds}
restic_post_hooks_rc{{config="{name}"}} {rc}
"""

_restic_help_backup = """
# HELP restic_backup_files_new Number of new files
# TYPE restic_backup_files_new gauge
# HELP restic_backup_files_changed Number of changed files
# TYPE restic_backup_files_changed gauge
# HELP restic_backup_files_unmodified Number of unmodified files
# TYPE restic_backup_files_unmodified gauge
# HELP restic_backup_dirs_new Number of new dirs
# TYPE restic_backup_dirs_new gauge
# HELP restic_backup_dirs_changed Number of changed dirs
# TYPE restic_backup_dirs_changed gauge
# HELP restic_backup_dirs_unmodified Number of unmodified dirs
# TYPE restic_backup_dirs_unmodified gauge
# HELP restic_backup_processed_files Number of processed files
# TYPE restic_backup_processed_files gauge
# HELP restic_backup_processed_size_bytes Processed size bytes
# TYPE restic_backup_processed_size_bytes gauge
# HELP restic_backup_processed_duration_seconds Backup processed duration in seconds
# TYPE restic_backup_processed_duration_seconds gauge
# HELP restic_backup_added_to_repo Number of added to repo
# TYPE restic_backup_added_to_repo gauge
# HELP restic_backup_duration_seconds Backup duration in seconds
# TYPE restic_backup_duration_seconds gauge
# HELP restic_backup_rc Return code of the restic backup command
# TYPE restic_backup_rc gauge
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

_restic_help_forget = """
# HELP restic_forget_removed_snapshots Number of forgotten snapshots
# TYPE restic_forget_removed_snapshots gauge
# HELP restic_forget_duration_seconds Forget duration in seconds
# TYPE restic_forget_duration_seconds gauge
# HELP restic_forget_rc Return code of the restic forget command
# TYPE restic_forget_rc gauge
"""
_restic_forget = """
restic_forget_removed_snapshots{{config="{name}",repository="{repository}"}} {removed_snapshots}
restic_forget_duration_seconds{{config="{name}",repository="{repository}"}} {duration_seconds}
restic_forget_rc{{config="{name}",repository="{repository}"}} {rc}
"""

_restic_help_prune = """
# HELP restic_prune_containing_packs_before Number of packs contained in repository before pruning
# TYPE restic_prune_containing_packs_before gauge
# HELP restic_prune_containing_blobs Number of blobs contained in repository before pruning
# TYPE restic_prune_containing_blobs gauge
# HELP restic_prune_containing_size_bytes Size in bytes contained in repository before pruning
# TYPE restic_prune_containing_size_bytes gauge
# HELP restic_prune_duplicate_blobs Number of duplicates found in the processed blobs
# TYPE restic_prune_duplicate_blobs gauge
# HELP restic_prune_duplicate_size_bytes Size in bytes of the duplicates found in the processed blobs
# TYPE restic_prune_duplicate_size_bytes gauge
# HELP restic_prune_in_use_blobs Number of blobs that are still in use (won't be removed)
# TYPE restic_prune_in_use_blobs gauge
# HELP restic_prune_removed_blobs Number of blobs to remove
# TYPE restic_prune_removed_blobs gauge
# HELP restic_prune_invalid_files Number of invalid files to remove
# TYPE restic_prune_invalid_files gauge
# HELP restic_prune_deleted_packs Number of pack to delete
# TYPE restic_prune_deleted_packs gauge
# HELP restic_prune_rewritten_packs Number of pack to delete
# TYPE restic_prune_rewritten_packs gauge
# HELP restic_prune_size_freed_bytes Size in byte freed after pack deletion
# TYPE restic_prune_size_freed_bytes gauge
# HELP restic_prune_removed_index_files Number of old index removed
# TYPE restic_prune_removed_index_files gauge
# HELP restic_prune_duration_seconds Duration in seconds
# TYPE restic_prune_duration_seconds gauge
# HELP restic_prune_rc Return code of the restic prune command
# TYPE restic_prune_rc gauge
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
_restic_new_prune = """
restic_prune_to_repack_blobs{{config="{name}",repository="{repository}"}} {to_repack_blobs}
restic_prune_to_repack_bytes{{config="{name}",repository="{repository}"}} {to_repack_bytes}
restic_prune_removed_blobs{{config="{name}",repository="{repository}"}} {removed_blobs}
restic_prune_removed_bytes{{config="{name}",repository="{repository}"}} {removed_bytes}
restic_prune_to_delete_blobs{{config="{name}",repository="{repository}"}} {to_delete_blobs}
restic_prune_to_delete_bytes{{config="{name}",repository="{repository}"}} {to_delete_bytes}
restic_prune_total_prune_blobs{{config="{name}",repository="{repository}"}} {total_prune_blobs}
restic_prune_total_prune_bytes{{config="{name}",repository="{repository}"}} {total_prune_bytes}
restic_prune_remaining_blobs{{config="{name}",repository="{repository}"}} {remaining_blobs}
restic_prune_remaining_bytes{{config="{name}",repository="{repository}"}} {remaining_bytes}
restic_prune_remaining_unused_size{{config="{name}",repository="{repository}"}} {remaining_unused_size}
restic_prune_duration_seconds{{config="{name}",repository="{repository}"}} {duration_seconds}
restic_prune_rc{{config="{name}",repository="{repository}"}} {rc}
"""

_restic_help_check = """
# HELP restic_check_errors Boolean to tell if any error occured
# TYPE restic_check_errors gauge
# HELP restic_check_errors_data Boolean to tell if the pack ID does not match
# TYPE restic_check_errors_data gauge
# HELP restic_check_errors_snapshots Boolean to tell if any of the snapshots can not be loaded
# TYPE restic_check_errors_snapshots gauge
# HELP restic_check_read_data Boolean that indicates whether or not `--read-data` was pass to restic 
# TYPE restic_check_read_data gauge
# HELP restic_check_check_unused Boolean that indicates whether or not `--check-unused` was pass to restic
# TYPE restic_check_check_unused gauge
# HELP restic_check_duration_seconds Duration in seconds
# TYPE restic_check_duration_seconds gauge
# HELP restic_check_rc Return code of the restic check command
# TYPE restic_check_rc gauge
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

_restic_help_stats = """
# HELP restic_stats_total_file_count Stats for all snapshots in restore size mode - Total file count
# TYPE restic_stats_total_file_count gauge
# HELP restic_stats_total_size_bytes Stats for all snapshots in restore size mode - Total file size in bytes
# TYPE restic_stats_total_size_bytes gauge
# HELP restic_stats_duration_seconds Stats for all snapshots in restore size mode - Duration in seconds
# TYPE restic_stats_duration_seconds gauge
# HELP restic_stats_rc Stats for all snapshots in restore size mode - Return code of the restic stats command
# TYPE restic_stats_rc gauge
"""
_restic_stats = """
restic_stats_total_file_count{{config="{name}",repository="{repository}"}} {total_file_count}
restic_stats_total_size_bytes{{config="{name}",repository="{repository}"}} {total_size_bytes}
restic_stats_duration_seconds{{config="{name}",repository="{repository}"}} {duration_seconds}
restic_stats_rc{{config="{name}",repository="{repository}"}} {rc}
"""


def generate_lines(metrics: Dict[str, Any], name: str) -> Iterator[str]:
    yield _restic_help_general
    yield _restic_general.format(name=name, **metrics)

    if metrics.get("backup"):
        yield backup_metrics(metrics["backup"], name)
    if metrics.get("forget"):
        yield str(forget_metrics(metrics["forget"], name))
    if metrics.get("prune"):
        yield str(prune_metrics(metrics["prune"], name))
    if metrics.get("check"):
        yield str(check_metrics(metrics["check"], name))
    if metrics.get("stats"):
        yield str(stats_metrics(metrics["stats"], name))


def backup_metrics(metrics: Dict[str, Any], name: str) -> str:
    pre_hooks = post_hooks = False
    retval = ""
    for repo, mtrx in metrics.items():
        if repo == "_restic_pre_hooks":
            pre_hooks = True
            retval += _restic_pre_hooks.format(name=name, **mtrx)
        elif repo == "_restic_post_hooks":
            post_hooks = True
            retval += _restic_post_hooks.format(name=name, **mtrx)
        else:
            if mtrx["rc"] != 0:
                retval += f'restic_backup_rc{{config="{name}",repository="{repo}"}} {mtrx["rc"]}\n'
            else:
                retval += _restic_backup.format(name=name, repository=repo, **mtrx)

    help_text = _restic_help_backup
    if pre_hooks:
        help_text += _restic_help_pre_hooks
    if post_hooks:
        help_text += _restic_help_post_hooks
    return help_text + retval


def forget_metrics(metrics: Dict[str, Any], name: str) -> str:
    retval = _restic_help_forget
    for repo, mtrx in metrics.items():
        if mtrx["rc"] != 0:
            retval += f'restic_forget_rc{{config="{name}",repository="{repo}"}} {mtrx["rc"]}\n'
        else:
            retval += _restic_forget.format(name=name, repository=repo, **mtrx)
    return retval


def prune_metrics(metrics: Dict[str, Any], name: str) -> str:
    retval = _restic_help_prune
    for repo, mtrx in metrics.items():
        if mtrx["rc"] != 0:
            retval += (
                f'restic_prune_rc{{config="{name}",repository="{repo}"}} {mtrx["rc"]}\n'
            )
        else:
            try:
                retval += _restic_prune.format(name=name, repository=repo, **mtrx)
            except KeyError:
                retval += _restic_new_prune.format(name=name, repository=repo, **mtrx)
    return retval


def check_metrics(metrics: Dict[str, Any], name: str) -> str:
    retval = _restic_help_check
    for repo, mtrx in metrics.items():
        if mtrx["rc"] != 0:
            retval += (
                f'restic_check_rc{{config="{name}",repository="{repo}"}} {mtrx["rc"]}\n'
            )
        else:
            retval += _restic_check.format(name=name, repository=repo, **mtrx)
    return retval


def stats_metrics(metrics: Dict[str, Any], name: str) -> str:
    retval = _restic_help_stats
    for repo, mtrx in metrics.items():
        if mtrx["rc"] != 0:
            retval += (
                f'restic_stats_rc{{config="{name}",repository="{repo}"}} {mtrx["rc"]}\n'
            )
        else:
            retval += _restic_stats.format(name=name, repository=repo, **mtrx)
    return retval
