import re

re_bytes = re.compile('([0-9.]+) ?([a-zA-Z]*B)')
re_time = re.compile('(?:([0-9]+):)?([0-9]+):([0-9]+)')


def _parse_size(size: str):
    number, unit = re_bytes.findall(size)[0]
    units = {
        "B": 1, "kB": 10 ** 3, "MB": 10 ** 6, "GB": 10 ** 9, "TB": 10 ** 12,
        "KiB": 1024, "MiB": 2 ** 20, "GiB": 2 ** 30, "TiB": 2 ** 40,
    }
    return float(number) * units[unit]


def _parse_time(time: str):
    hours, minutes, seconds = (int(x) if x else 0 for x in re_time.findall(time)[0])
    if minutes:
        seconds += minutes * 60
    if hours:
        seconds += hours * 3600
    return seconds


def parse_backup(output: str) -> dict:
    files_new, files_changed, files_unmodified = re.findall('Files:\s+([0-9]+) new,\s+([0-9]+) changed,\s+([0-9]+) unmodified', output)[0]
    dirs_new, dirs_changed, dirs_unmodified = re.findall('Dirs:\s+([0-9]+) new,\s+([0-9]+) changed,\s+([0-9]+) unmodified', output)[0]
    added_to_the_repo = re.findall('Added to the repo:\s+(-?[0-9.]+ [a-zA-Z]*B)', output)[0]
    processed_files, processed_size, processed_time = re.findall('processed ([0-9]+) files,\s+(-?[0-9.]+ [a-zA-Z]*B) in ([0-9]+:+[0-9]+)', output)[0]

    return {
        'files': {'new': files_new, 'changed': files_changed, 'unmodified': files_unmodified},
        'dirs': {'new': dirs_new, 'changed': dirs_changed, 'unmodified': dirs_unmodified},
        'processed': {'files': processed_files, 'size_bytes': _parse_size(processed_size), 'duration_seconds': _parse_time(processed_time)},
        'added_to_repo': _parse_size(added_to_the_repo)
    }


def parse_forget(output: str) -> dict:
    re_removed_snapshots = re.findall("remove ([0-9]+) snapshots", output)
    return {
        'removed_snapshots': re_removed_snapshots[0] if re_removed_snapshots else 0
    }


def parse_prune(output: str) -> dict:
    containing_packs_before, containing_blobs_before, containing_size_before = \
        re.findall('repository contains ([0-9]+) packs \(([0-9]+) blobs\) with (-?[0-9.]+ ?[a-zA-Z]*B)', output)[0]
    duplicate_blobs, duplicate_size = re.findall('([0-9]+) duplicate blobs, (-?[0-9.]+ ?[a-zA-Z]*B) duplicate', output)[0]
    in_use_blobs, _, removed_blobs = re.findall('found ([0-9]+) of ([0-9]+) data blobs still in use, removing ([0-9]+) blobs', output)[0]
    invalid_files = re.findall('will remove ([0-9]+) invalid files', output)[0]
    deleted_packs, rewritten_packs, size_freed = \
        re.findall('will delete ([0-9]+) packs and rewrite ([0-9]+) packs, this frees (-?[0-9.]+ ?[a-zA-Z]*B)', output)[0]
    removed_index_files = re.findall('remove ([0-9]+) old index files', output)[0]

    return {
        'containing_packs_before': containing_packs_before,
        'containing_blobs': containing_blobs_before,
        'containing_size_bytes': _parse_size(containing_size_before),
        'duplicate_blobs': duplicate_blobs,
        'duplicate_size_bytes': _parse_size(duplicate_size),
        'in_use_blobs': in_use_blobs,
        'removed_blobs': removed_blobs,
        'invalid_files': invalid_files,
        'deleted_packs': deleted_packs,
        'rewritten_packs': rewritten_packs,
        'size_freed_bytes': _parse_size(size_freed),
        'removed_index_files': removed_index_files,
    }
