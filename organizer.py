import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

# File category definitions
EXT_MAPPING = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "PDFs": [".pdf"],
    "Documents": [".docx", ".doc", ".txt", ".md", ".pptx", ".ppt", ".xlsx", ".xls", ".csv"],
    "Code": [".py", ".c", ".cpp", ".h", ".json", ".xml", ".html", ".css", ".js"],
    "Archives": [".zip", ".tar", ".gz", ".7z", ".rar"],
    "Audio_Video": [".mp3", ".wav", ".mp4", ".mkv", ".avi", ".mov"]
}

MANIFEST_NAME = ".suitcase_manifest.json"

def get_destination_category(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    for category, extensions in EXT_MAPPING.items():
        if ext in extensions:
            return category
    return "Others"

def get_unique_destination_path(target_dir: Path, filename: str) -> Path:
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
    for entry in target_dir.iterdir():
        # Only organize top-level files; skip the script and hidden manifest
        if entry.is_file() and entry.name not in ("organizer.py", MANIFEST_NAME):
            category = get_destination_category(entry)
            dest_folder = target_dir / category
            dest_path = get_unique_destination_path(dest_folder, entry.name)
            moves.append((entry, dest_path))
    return moves

def save_manifest(target_dir: Path, moves: list[tuple[Path, Path]]) -> None:
    manifest_path = target_dir / MANIFEST_NAME
    data = {
        "timestamp": datetime.now().isoformat(),
        "moves": [{"original": str(src), "current": str(dst)} for src, dst in moves]
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def organize(target_dir: Path) -> None:
    moves = plan_moves(target_dir)
    if not moves:
        print("No loose files found to organize.")
        return

    print("\n--- Move Preview (Dry Run) ---")
    for src, dst in moves:
        print(f"{src.name:<30} -> {dst.parent.name}/{dst.name}")
    print(f"Total files to organize: {len(moves)}\n")

    confirm = input("Execute these moves? (yes/no): ").strip().lower()
    if confirm not in ("y", "yes"):
        print("Operation cancelled. No files were moved.")
        return

    successful_moves = []
    for src, dst in moves:
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(src), str(dst))
            successful_moves.append((src, dst))
        except Exception as e:
            print(f"Error moving {src.name}: {e}")

    if successful_moves:
        save_manifest(target_dir, successful_moves)
        print(f"\nDone. Successfully organized {len(successful_moves)}/{len(moves)} files.")
        print(f"Manifest written to: {target_dir / MANIFEST_NAME}")

def undo(target_dir: Path) -> None:
    manifest_path = target_dir / MANIFEST_NAME
    if not manifest_path.exists():
        print(f"Error: No undo manifest ({MANIFEST_NAME}) found in {target_dir}.")
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    moves = data.get("moves", [])
    if not moves:
        print("Manifest is empty; nothing to undo.")
        return

    print(f"\n--- Undo Preview ---")
    print(f"Restoring {len(moves)} files back to base folder: {target_dir}")
    for item in moves:
        print(f"{Path(item['current']).name:<30} -> Root folder")

    confirm = input("\nProceed with undo? (yes/no): ").strip().lower()
    if confirm not in ("y", "yes"):
        print("Undo cancelled.")
        return

    reverted_count = 0
    folders_to_check = set()

    for item in moves:
        src = Path(item["current"])
        dst = Path(item["original"])
        if src.exists():
            try:
                shutil.move(str(src), str(dst))
                reverted_count += 1
                folders_to_check.add(src.parent)
            except Exception as e:
                print(f"Error restoring {src.name}: {e}")
        else:
            print(f"Skipping {src.name}: file no longer at {src}")

    # Clean up empty category subfolders
    for folder in folders_to_check:
        try:
            if folder.exists() and not any(folder.iterdir()):
                folder.rmdir()
        except OSError:
            pass

    # Remove manifest after complete reversal
    manifest_path.unlink()
    print(f"\nUndo complete. Restored {reverted_count}/{len(moves)} files and removed empty folders.")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--undo":
        path_input = input("Enter path of the folder to undo: ").strip().strip('"')
        target = Path(path_input)
        if not target.is_dir():
            print("Invalid directory.")
            return
        undo(target)
        return

    path_input = input("Enter path to organize (or pass --undo as flag): ").strip().strip('"')
    target = Path(path_input)
    if not target.is_dir():
        print("Invalid directory.")
        return

    organize(target)

if __name__ == "__main__":
    main()