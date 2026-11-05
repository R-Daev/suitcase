import os
from pathlib import Path
from PIL import Image


def convert_image_format(input_path: Path, output_format: str, output_dir: Path | None = None) -> Path:
    """
    Converts an image to a target format (.jpg, .jpeg, .png, .webp, .bmp).
    Automatically converts RGBA modes to RGB for formats that do not support transparency.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    fmt = output_format.lower().lstrip(".")
    if fmt in ("jpeg", "jpg"):
        ext_suffix = ".jpg"
        save_format = "JPEG"
    elif fmt == "png":
        ext_suffix = ".png"
        save_format = "PNG"
    elif fmt == "webp":
        ext_suffix = ".webp"
        save_format = "WEBP"
    elif fmt == "bmp":
        ext_suffix = ".bmp"
        save_format = "BMP"
    else:
        raise ValueError(f"Unsupported format: {output_format}")

    target_dir = output_dir if output_dir else input_path.parent
    output_path = target_dir / f"{input_path.stem}_converted{ext_suffix}"

    with Image.open(input_path) as img:
        if save_format == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output_path, format=save_format)

    return output_path


def resize_or_elongate_image(
    input_path: Path,
    width: int | None = None,
    height: int | None = None,
    scale_factor: float | None = None,
    output_dir: Path | None = None
) -> Path:
    """
    Scales or stretches (elongates) an image.
    Supports proportional scaling or independent width/height modification.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    with Image.open(input_path) as img:
        orig_w, orig_h = img.size

        if scale_factor:
            new_w = max(1, int(orig_w * scale_factor))
            new_h = max(1, int(orig_h * scale_factor))
        elif width and height:
            new_w = max(1, width)
            new_h = max(1, height)
        elif width and not height:
            new_w = max(1, width)
            new_h = max(1, int(orig_h * (width / orig_w)))
        elif height and not width:
            new_h = max(1, height)
            new_w = max(1, int(orig_w * (height / orig_h)))
        else:
            raise ValueError("Provide at least width, height, or a scale factor.")

        resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        target_dir = output_dir if output_dir else input_path.parent
        output_path = target_dir / f"{input_path.stem}_{new_w}x{new_h}{input_path.suffix}"

        if input_path.suffix.lower() in (".jpg", ".jpeg") and resized_img.mode in ("RGBA", "P"):
            resized_img = resized_img.convert("RGB")

        resized_img.save(output_path)

    return output_path


def compress_image(input_path: Path, quality: int = 80, output_dir: Path | None = None) -> tuple[Path, int, int]:
    """
    Compresses an image file.
    Returns: (output_path, original_size_bytes, compressed_size_bytes).
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    orig_size = os.path.getsize(input_path)
    target_dir = output_dir if output_dir else input_path.parent

    with Image.open(input_path) as img:
        suffix = input_path.suffix.lower()
        if suffix in (".jpg", ".jpeg"):
            output_path = target_dir / f"{input_path.stem}_compressed.jpg"
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(output_path, "JPEG", optimize=True, quality=quality)
        elif suffix == ".png":
            # Saves as optimized WebP for high compression ratio
            output_path = target_dir / f"{input_path.stem}_compressed.webp"
            img.save(output_path, "WEBP", quality=quality, method=6)
        else:
            output_path = target_dir / f"{input_path.stem}_compressed{input_path.suffix}"
            img.save(output_path, optimize=True, quality=quality)

    comp_size = os.path.getsize(output_path)
    return output_path, orig_size, comp_size