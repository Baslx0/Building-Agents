"""Read-only Windows disk space analyzer. No deletion or file modification."""

import argparse
import os
import shutil
from pathlib import Path


REPARSE_POINT = getattr(__import__("stat"), "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def format_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if size < 1024 or unit == "PB":
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def is_link_or_reparse(entry: os.DirEntry) -> bool:
    try:
        if entry.is_symlink():
            return True
        return bool(entry.stat(follow_symlinks=False).st_file_attributes & REPARSE_POINT)
    except AttributeError:
        return False


def folder_size(root: Path, errors: list[str]) -> int:
    """Iterative traversal; skips links/reparse points and inaccessible paths."""
    total = 0
    pending = [root]
    while pending:
        folder = pending.pop()
        try:
            with os.scandir(folder) as entries:
                for entry in entries:
                    try:
                        if is_link_or_reparse(entry):
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            pending.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                    except (OSError, PermissionError) as exc:
                        errors.append(f"{entry.path}: {exc}")
        except (OSError, PermissionError) as exc:
            errors.append(f"{folder}: {exc}")
    return total


def analyze(path: Path, top: int) -> None:
    if not path.exists() or not path.is_dir():
        raise ValueError(f"Not an accessible directory: {path}")

    disk = shutil.disk_usage(path)
    print(f"\nPath: {path}")
    print(f"Disk total: {format_size(disk.total)}")
    print(f"Disk used:  {format_size(disk.used)}")
    print(f"Disk free:  {format_size(disk.free)}")
    print("\nScanning immediate child folders (read-only)...")

    errors: list[str] = []
    results: list[tuple[int, str]] = []
    with os.scandir(path) as entries:
        for entry in entries:
            try:
                if is_link_or_reparse(entry):
                    continue
                if entry.is_dir(follow_symlinks=False):
                    results.append((folder_size(Path(entry.path), errors), entry.name))
            except (OSError, PermissionError) as exc:
                errors.append(f"{entry.path}: {exc}")

    print(f"\nLargest folders under {path}:")
    for size, name in sorted(results, reverse=True)[:top]:
        print(f"  {format_size(size):>12}  {name}")

    print(f"\nScan warnings: {len(errors)}")
    if errors:
        print("Some sizes are incomplete due to inaccessible items.")
        for warning in errors[:5]:
            print(f"  - {warning}")
        if len(errors) > 5:
            print(f"  ...and {len(errors) - 5} more warnings.")
    print("\nNo files were deleted or changed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only disk usage analyzer")
    parser.add_argument("--path", type=Path, default=Path("C:/"), help="Drive or directory to scan")
    parser.add_argument("--top", type=int, default=10, help="Number of largest folders to show")
    args = parser.parse_args()
    if args.top < 1:
        parser.error("--top must be greater than zero")
    try:
        analyze(args.path.resolve(), args.top)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
