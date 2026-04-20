from __future__ import annotations

from pathlib import Path
import sys

from bmp_image import BMPImage


BASE_DIR = Path(__file__).resolve().parent
SOURCE_DIR = Path("/Users/lifuyue/Downloads/实验三素材/8位伪彩色BMP")
OUTPUT_DIR = BASE_DIR / "output" / "8_to_24"


class Convert8To24App:
    def __init__(self, source_dir: Path, output_dir: Path) -> None:
        self.source_dir = source_dir
        self.output_dir = output_dir

    def run(self) -> None:
        bmp_files = sorted(self.source_dir.glob("*.bmp"))
        if not bmp_files:
            raise FileNotFoundError(f"未找到 8 位 BMP 素材目录: {self.source_dir}")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        for bmp_file in bmp_files:
            image = BMPImage.from_file(bmp_file)
            truecolor_image = image.to_truecolor_24bit()
            output_path = self.output_dir / f"{bmp_file.stem}_truecolor_24bit.bmp"
            truecolor_image.save(output_path)
            print(f"[8->24] {bmp_file.name} -> {output_path}")


def main() -> int:
    Convert8To24App(SOURCE_DIR, OUTPUT_DIR).run()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        raise SystemExit(1)
