_restic = """
# HELP restic_last_run Epoch timestamp of the last run
# TYPE restic_last_run counter
restic_last_run{{config="{config_name}"}} {last_run}
# HELP restic_total_duration_seconds Total duration in seconds
# TYPE restic_total_duration_seconds gauge
restic_total_duration_seconds{{config="{config_name}"}} {total_duration_seconds}
"""

_restic_pre_hooks = """
# HELP restic_pre_hooks_duration_seconds Pre hooks duration in seconds
# TYPE restic_pre_hooks_duration_seconds gauge
restic_pre_hooks_duration_seconds{{config="{config_name}"}} {restic_pre_hooks[duration_seconds]}
# HELP restic_pre_hooks_rc Pre hooks return code
# TYPE restic_pre_hooks_rc gauge
restic_pre_hooks_rc{{config="{config_name}"}} {restic_pre_hooks[rc]}
"""

_restic_post_hooks = """
# HELP restic_post_hooks_duration_seconds Pre hooks duration in seconds
# TYPE restic_post_hooks_duration_seconds gauge
restic_post_hooks_duration_seconds{{config="{config_name}"}} {restic_post_hooks[duration_seconds]}
# HELP restic_post_hooks_rc Post hooks return code
# TYPE restic_post_hooks_rc gauge
restic_post_hooks_rc{{config="{config_name}"}} {restic_post_hooks[rc]}
"""

_restic_backup = """
# HELP restic_backup_files_new Number of new files
# TYPE restic_backup_files_new gauge
restic_backup_files_new{{config="{config_name}",repository="{repository}"}} {restic_backup[files][new]}
# HELP restic_backup_files_changed Number of changed files
# TYPE restic_backup_files_changed gauge
restic_backup_files_changed{{config="{config_name}",repository="{repository}"}} {restic_backup[files][changed]}
# HELP restic_backup_files_unmodified Number of unmodified files
# TYPE restic_backup_files_unmodified gauge
restic_backup_files_unmodified{{config="{config_name}",repository="{repository}"}} {restic_backup[files][unmodified]}
# HELP restic_backup_dirs_new Number of new dirs
# TYPE restic_backup_dirs_new gauge
restic_backup_dirs_new{{config="{config_name}",repository="{repository}"}} {restic_backup[dirs][new]}
# HELP restic_backup_dirs_changed Number of changed dirs
# TYPE restic_backup_dirs_changed gauge
restic_backup_dirs_changed{{config="{config_name}",repository="{repository}"}} {restic_backup[dirs][changed]}
# HELP restic_backup_dirs_unmodified Number of unmodified dirs
# TYPE restic_backup_dirs_unmodified gauge
restic_backup_dirs_unmodified{{config="{config_name}",repository="{repository}"}} {restic_backup[dirs][unmodified]}
# HELP restic_backup_processed_files Number of processed files
# TYPE restic_backup_processed_files gauge
restic_backup_processed_files{{config="{config_name}",repository="{repository}"}} {restic_backup[processed][files]}
# HELP restic_backup_processed_size_bytes Processed size bytes
# TYPE restic_backup_processed_size_bytes gauge
restic_backup_processed_size_bytes{{config="{config_name}",repository="{repository}"}} {restic_backup[processed][size_bytes]}
# HELP restic_backup_processed_duration_seconds Backup processed duration in seconds
# TYPE restic_backup_processed_duration_seconds gauge
restic_backup_processed_duration_seconds{{config="{config_name}",repository="{repository}"}} {restic_backup[processed][duration_seconds]}
# HELP restic_backup_added_to_repo Number of added to repo
# TYPE restic_backup_added_to_repo gauge
restic_backup_added_to_repo{{config="{config_name}",repository="{repository}"}} {restic_backup[added_to_repo]}
# HELP restic_backup_duration_seconds Backup duration in seconds
# TYPE restic_backup_duration_seconds gauge
restic_backup_duration_seconds{{config="{config_name}",repository="{repository}"}} {restic_backup[duration_seconds]}
# HELP restic_backup_rc Return code of the restic backup command.
# TYPE restic_backup_rc gauge
restic_backup_rc{{config="{config_name}",repository="{repository}"}} {restic_backup[rc]}
"""

_restic_forget = """
# HELP restic_forget_removed_snapshots Number of forgotten snapshots
# TYPE restic_forget_removed_snapshots gauge
restic_forget_removed_snapshots{{config="{config_name}",repository="{repository}"}} {restic_forget[removed_snapshots]}
# HELP restic_forget_rc Return code of the restic forget command.
# TYPE restic_forget_rc gauge
restic_forget_rc{{config="{config_name}",repository="{repository}"}} {restic_forget[rc]}
"""

_restic_prune = """
# HELP restic_prune_containing_packs_before Number of packs contained in repository before pruning
# TYPE restic_prune_containing_packs_before gauge
restic_prune_containing_packs_before{{config="{config_name}",repository="{repository}"}} {restic_prune[containing_packs_before]}
# HELP restic_prune_containing_blobs Number of blobs contained in repository before pruning
# TYPE restic_prune_containing_blobs gauge
restic_prune_containing_blobs{{config="{config_name}",repository="{repository}"}} {restic_prune[containing_blobs]}
# HELP restic_prune_containing_size_bytes Size in bytes contained in repository before pruning
# TYPE restic_prune_containing_size_bytes gauge
restic_prune_containing_size_bytes{{config="{config_name}",repository="{repository}"}} {restic_prune[containing_size_bytes]}
# HELP restic_prune_duplicate_blobs Number of duplicates found in the processed blobs
# TYPE restic_prune_duplicate_blobs gauge
restic_prune_duplicate_blobs{{config="{config_name}",repository="{repository}"}} {restic_prune[duplicate_blobs]}
# HELP restic_prune_duplicate_size_bytes Size in bytes of the duplicates found in the processed blobs
# TYPE restic_prune_duplicate_size_bytes gauge
restic_prune_duplicate_size_bytes{{config="{config_name}",repository="{repository}"}} {restic_prune[duplicate_size_bytes]}
# HELP restic_prune_in_use_blobs Number of blobs that are still in use (won't be removed)
# TYPE restic_prune_in_use_blobs gauge
restic_prune_in_use_blobs{{config="{config_name}",repository="{repository}"}} {restic_prune[in_use_blobs]}
# HELP restic_prune_removed_blobs Number of blobs to remove
# TYPE restic_prune_removed_blobs gauge
restic_prune_removed_blobs{{config="{config_name}",repository="{repository}"}} {restic_prune[removed_blobs]}
# HELP restic_prune_invalid_files Number of invalid files to remove
# TYPE restic_prune_invalid_files gauge
restic_prune_invalid_files{{config="{config_name}",repository="{repository}"}} {restic_prune[invalid_files]}
# HELP restic_prune_deleted_packs Number of pack to delete
# TYPE restic_prune_deleted_packs gauge
restic_prune_deleted_packs{{config="{config_name}",repository="{repository}"}} {restic_prune[deleted_packs]}
# HELP restic_prune_rewritten_packs Number of pack to delete
# TYPE restic_prune_rewritten_packs gauge
restic_prune_rewritten_packs{{config="{config_name}",repository="{repository}"}} {restic_prune[rewritten_packs]}
# HELP restic_prune_size_freed_bytes Size in byte freed after pack deletion
# TYPE restic_prune_size_freed_bytes gauge
restic_prune_size_freed_bytes{{config="{config_name}",repository="{repository}"}} {restic_prune[size_freed_bytes]}
# HELP restic_prune_removed_index_files Number of old index removed
# TYPE restic_prune_removed_index_files gauge
restic_prune_removed_index_files{{config="{config_name}",repository="{repository}"}} {restic_prune[removed_index_files]}
# HELP restic_prune_duration_seconds Duration in seconds
# TYPE restic_prune_duration_seconds gauge
restic_prune_duration_seconds{{config="{config_name}",repository="{repository}"}} {restic_prune[duration_seconds]}
# HELP restic_prune_rc Return code of the restic prune command.
# TYPE restic_prune_rc gauge
restic_prune_rc{{config="{config_name}",repository="{repository}"}} {restic_prune[rc]}
"""

_restic_check = """
# HELP restic_check_errors Boolean to tell if any error occured
# TYPE restic_check_errors gauge
restic_check_errors{{config="{config_name}",repository="{repository}"}} {restic_check[errors]}
# HELP restic_check_errors_data Boolean to tell if the pack ID does not match
# TYPE restic_check_errors_data gauge
restic_check_errors_data{{config="{config_name}",repository="{repository}"}} {restic_check[errors_data]}
# HELP restic_check_errors_snapshots Boolean to tell if any of the snapshots can not be loaded
# TYPE restic_check_errors_snapshots gauge
restic_check_errors_snapshots{{config="{config_name}",repository="{repository}"}} {restic_check[errors_snapshots]}
# HELP restic_check_read_data Boolean that indicates whether or not `--read-data` was pass to restic 
# TYPE restic_check_read_data gauge
restic_check_read_data{{config="{config_name}",repository="{repository}"}} {restic_check[read_data]}
# HELP restic_check_check_unused Boolean that indicates whether or not `--check-unused` was pass to restic
# TYPE restic_check_check_unused gauge
restic_check_check_unused{{config="{config_name}",repository="{repository}"}} {restic_check[check_unused]}
# HELP restic_check_duration_seconds Duration in seconds
# TYPE restic_check_duration_seconds gauge
restic_check_duration_seconds{{config="{config_name}",repository="{repository}"}} {restic_check[duration_seconds]}
# HELP restic_check_rc Return code of the restic check command.
# TYPE restic_check_rc gauge
restic_check_rc{{config="{config_name}",repository="{repository}"}} {restic_check[rc]}
"""

_restic_stats = """
# HELP restic_stats_total_file_count Stats for all snapshots in restore size mode - Total file count
# TYPE restic_stats_total_file_count gauge
restic_stats_total_file_count{{config="{config_name}",repository="{repository}"}} {restic_stats[total_file_count]}
# HELP restic_stats_total_size_bytes Stats for all snapshots in restore size mode - Total file size in bytes
# TYPE restic_stats_total_size_bytes gauge
restic_stats_total_size_bytes{{config="{config_name}",repository="{repository}"}} {restic_stats[total_size]}
# HELP restic_stats_duration_seconds Stats for all snapshots in restore size mode - Duration in seconds
# TYPE restic_stats_duration_seconds gauge
restic_stats_duration_seconds{{config="{config_name}",repository="{repository}"}} {restic_stats[duration_seconds]}
# HELP restic_stats_rc Stats for all snapshots in restore size mode - Return code of the restic stats command
# TYPE restic_stats_rc gauge
restic_stats_rc{{config="{config_name}",repository="{repository}"}} {restic_stats[rc]}
"""


def prometheus_generate_lines(metrics, config_name):
    basic_info = _restic
    if metrics.get("restic_pre_hooks"):
        basic_info += _restic_pre_hooks
    if metrics.get("restic_post_hooks"):
        basic_info += _restic_post_hooks
    basic_info = basic_info.format(config_name=config_name, **metrics)

    routput = ""
    for repo_name, repo_metrics in metrics.get("repositories").items():
        output = ""
        if repo_metrics.get("restic_backup"):
            output += _restic_backup
        if repo_metrics.get("restic_forget"):
            output += _restic_forget
        if repo_metrics.get("restic_prune"):
            output += _restic_prune
        if repo_metrics.get("restic_check"):
            output += _restic_check
        if repo_metrics.get("restic_stats"):
            output += _restic_stats
        routput += output.format(
            repository=repo_name, config_name=config_name, **repo_metrics
        )
    return basic_info + routput + "\n"
    # return output.format(repository=repository, config_name=config_name, **metrics)


def prometheus_write_file(lines, path):
    with open(path, "w") as file:
        file.writelines(lines)