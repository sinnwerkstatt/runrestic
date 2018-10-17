_restic_backup = """
restic_backup_files_new{{config="{config_name}",repository="{repository}"}} {restic_backup[files][new]}
restic_backup_files_changed{{config="{config_name}",repository="{repository}"}} {restic_backup[files][changed]}
restic_backup_files_unmodified{{config="{config_name}",repository="{repository}"}} {restic_backup[files][unmodified]}
restic_backup_dirs_new{{config="{config_name}",repository="{repository}"}} {restic_backup[dirs][new]}
restic_backup_dirs_changed{{config="{config_name}",repository="{repository}"}} {restic_backup[dirs][changed]}
restic_backup_dirs_unmodified{{config="{config_name}",repository="{repository}"}} {restic_backup[dirs][unmodified]}
restic_backup_processed_files{{config="{config_name}",repository="{repository}"}} {restic_backup[processed][files]}
restic_backup_processed_size_bytes{{config="{config_name}",repository="{repository}"}} {restic_backup[processed][size_bytes]}
restic_backup_processed_duration_seconds{{config="{config_name}",repository="{repository}"}} {restic_backup[processed][duration_seconds]}
restic_backup_added_to_repo{{config="{config_name}",repository="{repository}"}} {restic_backup[added_to_repo]}
restic_backup_rc{{config="{config_name}",repository="{repository}"}} {restic_backup[rc]}
"""

_restic_forget = """
restic_forget_removed_snapshots{{config="{config_name}",repository="{repository}"}} {restic_forget[removed_snapshots]}
restic_forget_rc{{config="{config_name}",repository="{repository}"}} {restic_forget[rc]}
"""

_restic_prune = """
restic_prune_containing_packs_before{{config="{config_name}",repository="{repository}"}} {restic_prune[containing_packs_before]}
restic_prune_containing_blobs{{config="{config_name}",repository="{repository}"}} {restic_prune[containing_blobs]}
restic_prune_containing_size_bytes{{config="{config_name}",repository="{repository}"}} {restic_prune[containing_size_bytes]}
restic_prune_duplicate_blobs{{config="{config_name}",repository="{repository}"}} {restic_prune[duplicate_blobs]}
restic_prune_duplicate_size_bytes{{config="{config_name}",repository="{repository}"}} {restic_prune[duplicate_size_bytes]}
restic_prune_in_use_blobs{{config="{config_name}",repository="{repository}"}} {restic_prune[in_use_blobs]}
restic_prune_removed_blobs{{config="{config_name}",repository="{repository}"}} {restic_prune[removed_blobs]}
restic_prune_invalid_files{{config="{config_name}",repository="{repository}"}} {restic_prune[invalid_files]}
restic_prune_deleted_packs{{config="{config_name}",repository="{repository}"}} {restic_prune[deleted_packs]}
restic_prune_rewritten_packs{{config="{config_name}",repository="{repository}"}} {restic_prune[rewritten_packs]}
restic_prune_size_freed_bytes{{config="{config_name}",repository="{repository}"}} {restic_prune[size_freed_bytes]}
restic_prune_removed_index_files{{config="{config_name}",repository="{repository}"}} {restic_prune[removed_index_files]}
restic_prune_rc{{config="{config_name}",repository="{repository}"}} {restic_prune[rc]}
"""

_restic_check = """
restic_check_errors{{config="{config_name}",repository="{repository}"}} {restic_check[errors]}
restic_check_errors_data{{config="{config_name}",repository="{repository}"}} {restic_check[errors_data]}
restic_check_errors_snapshots{{config="{config_name}",repository="{repository}"}} {restic_check[errors_snapshots]}
restic_check_read_data{{config="{config_name}",repository="{repository}"}} {restic_check[read_data]}
restic_check_check_unused{{config="{config_name}",repository="{repository}"}} {restic_check[check_unused]}
restic_check_rc{{config="{config_name}",repository="{repository}"}} {restic_check[rc]}
"""


def prometheus_generate_lines(metrics, repository, config_name):
    output = 'restic_last_run{{config="{config_name}",repository="{repository}"}} {last_run}\n'
    if metrics.get('restic_backup'):
        output += _restic_backup
    if metrics.get('restic_forget'):
        output += _restic_forget
    if metrics.get('restic_prune'):
        output += _restic_prune
    if metrics.get('restic_check'):
        output += _restic_check
    output += "\n\n"
    return output.format(**metrics, repository=repository, config_name=config_name)


def prometheus_write_file(lines, path):
    with open(path, 'w') as file:
        file.writelines(lines)
