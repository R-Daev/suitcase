import os
import shutil
from pathlib import Path

# Category mapping based on file extensions
EXT_MAPPING = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "PDFs": [".pdf"],
    "Documents": [".docx", ".doc", ".txt", ".md", ".pptx", ".ppt", ".xlsx", ".xls", ".csv"],
    "Code": [".py", ".c", ".cpp", ".h", ".json", ".xml", ".html", ".css", ".js"],
    "Archives": [".zip", ".tar", ".gz", ".7z", ".rar"],
    "Audio_Video": [".mp3", ".wav", ".mp4", ".mkv", ".avi", ".mov"]
}

def get_destination_category(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    for category, extensions in EXT_MAPPING.items():
        if ext in extensions:
            return category
    return "Others"

def get_unique_destination_path(target_dir: Path, filename: str) -> Path:
    """Ensures no existing files are ever overwritten by appending a counter."""
    dest = target_dir / filename
    if not dest.exists():
        return dest

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        candidate = target_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1

def plan_moves(target_dir: Path) -> list[tuple[Path, Path]]:
    moves = []
    # Only iterate through direct files in the target folder (ignoring directories)
    for entry in target_dir.iterdir():
        if entry.is_file() and entry.name != "organizer.py":
            category = get_destination_category(entry)
            dest_folder = target_dir / category
            dest_path = get_unique_destination_path(dest_folder, entry.name)
            moves.append((entry, dest_path))
    return moves

def main():
    target_input = input("Enter the absolute path to your test folder: ").strip().strip('"')
    target_dir = Path(target_input)

    if not target_dir.exists() or not target_dir.is_dir():
        print(f"Error: '{target_dir}' is not a valid directory.")
        return

    moves = plan_moves(target_dir)

    if not moves:
        print("No files found to organize.")
        return

    print("\n--- Move Preview (Dry Run) ---")
    for src, dst in moves:
        print(f"{src.name:<30} -> {dst.parent.name}/{dst.name}")
    print(f"Total files to organize: {len(moves)}\n")

    confirm = input("Execute these moves? (yes/no): ").strip().lower()
    if confirm not in ("y", "yes"):
        print("Operation cancelled. No files were moved.")
        return

    # Execute moves safely
    success_count = 0
    for src, dst in moves:
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(src), str(dst))
            success_count += 1
        except Exception as e:
            print(f"Failed to move {src.name}: {e}")

    print(f"\nDone. Successfully organized {success_count}/{len(moves)} files.")

if __name__ == "__main__":
    main()