from __future__ import annotations

import sys

from convert_24_to_8 import Convert24To8App, OUTPUT_DIR as OUTPUT_24_TO_8, SOURCE_DIR as SOURCE_24
from convert_8_to_24 import Convert8To24App, OUTPUT_DIR as OUTPUT_8_TO_24, SOURCE_DIR as SOURCE_8


def main() -> int:
    Convert24To8App(SOURCE_24, OUTPUT_24_TO_8).run()
    Convert8To24App(SOURCE_8, OUTPUT_8_TO_24).run()
    print("[完成] LAB3 两个 BMP 转换任务已执行完成")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        raise SystemExit(1)
