import sys
import json
import shutil
import logging
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
LOG_FILENAME = "organizer.log"


def setup_logger(log_dir: Path) -> logging.Logger:
    """Configures a dedicated file logger for the target directory."""
    logger = logging.getLogger("Suitcase")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if re-initialized
    if not logger.handlers:
        log_path = log_dir / LOG_FILENAME
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_destination_category(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    for category, extensions in EXT_MAPPING.items():
        if ext in extensions:
            return category
    return "Others"


def get_unique_destination_path(target_dir: Path, filename: str, logger: logging.Logger) -> Path:
    dest = target_dir / filename
    if not dest.exists():
        return dest

    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 1
    while True:
        candidate = target_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            logger.warning(f"File collision: '{filename}' will be saved as '{candidate.name}'")
            return candidate
        counter += 1


def plan_moves(target_dir: Path, logger: logging.Logger) -> list[tuple[Path, Path]]:
    moves = []
    ignored_names = {"organizer.py", MANIFEST_NAME, LOG_FILENAME}

    for entry in target_dir.iterdir():
        if entry.is_file() and entry.name not in ignored_names:
            category = get_destination_category(entry)
            dest_folder = target_dir / category
            dest_path = get_unique_destination_path(dest_folder, entry.name, logger)
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
    logger = setup_logger(target_dir)
    logger.info(f"--- Starting organize session on: {target_dir} ---")

    moves = plan_moves(target_dir, logger)
    if not moves:
        print("No loose files found to organize.")
        logger.info("Scan completed: No loose files found to organize.")
        return

    print("\n--- Move Preview (Dry Run) ---")
    for src, dst in moves:
        print(f"{src.name:<30} -> {dst.parent.name}/{dst.name}")
    print(f"Total files to organize: {len(moves)}\n")

    confirm = input("Execute these moves? (yes/no): ").strip().lower()
    if confirm not in ("y", "yes"):
        print("Operation cancelled. No files were moved.")
        logger.info("Organize operation cancelled by user during dry run.")
        return

    successful_moves = []
    for src, dst in moves:
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(src), str(dst))
            successful_moves.append((src, dst))
            logger.info(f"Moved: '{src.name}' -> '{dst.relative_to(target_dir)}'")
        except Exception as e:
            error_msg = f"Failed to move '{src.name}': {e}"
            print(error_msg)
            logger.error(error_msg)

    if successful_moves:
        save_manifest(target_dir, successful_moves)
        print(f"\nDone. Successfully organized {len(successful_moves)}/{len(moves)} files.")
        print(f"Manifest written to: {target_dir / MANIFEST_NAME}")
        print(f"Log written to: {target_dir / LOG_FILENAME}")
        logger.info(f"Organize session complete. Moved {len(successful_moves)}/{len(moves)} files.")


def undo(target_dir: Path) -> None:
    logger = setup_logger(target_dir)
    logger.info(f"--- Starting undo session on: {target_dir} ---")

    manifest_path = target_dir / MANIFEST_NAME
    if not manifest_path.exists():
        msg = f"Error: No undo manifest ({MANIFEST_NAME}) found in {target_dir}."
        print(msg)
        logger.warning(msg)
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    moves = data.get("moves", [])
    if not moves:
        print("Manifest is empty; nothing to undo.")
        logger.info("Manifest was empty; nothing to undo.")
        return

    print(f"\n--- Undo Preview ---")
    print(f"Restoring {len(moves)} files back to base folder: {target_dir}")
    for item in moves:
        print(f"{Path(item['current']).name:<30} -> Root folder")

    confirm = input("\nProceed with undo? (yes/no): ").strip().lower()
    if confirm not in ("y", "yes"):
        print("Undo cancelled.")
        logger.info("Undo operation cancelled by user.")
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
                logger.info(f"Reverted: '{src.name}' -> '{dst.name}'")
            except Exception as e:
                error_msg = f"Failed to revert '{src.name}': {e}"
                print(error_msg)
                logger.error(error_msg)
        else:
            skip_msg = f"Skipping '{src.name}': file not found at {src}"
            print(skip_msg)
            logger.warning(skip_msg)

    # Clean up empty category subfolders
    for folder in folders_to_check:
        try:
            if folder.exists() and not any(folder.iterdir()):
                folder.rmdir()
                logger.info(f"Removed empty directory: '{folder.name}'")
        except OSError as e:
            logger.warning(f"Could not remove directory '{folder.name}': {e}")

    manifest_path.unlink()
    print(f"\nUndo complete. Restored {reverted_count}/{len(moves)} files.")
    logger.info(f"Undo session complete. Restored {reverted_count}/{len(moves)} files.")


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