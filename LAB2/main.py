from __future__ import annotations

from collections import Counter
from pathlib import Path
import string
import sys

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pydub import AudioSegment
import sounddevice as sd
import soundfile as sf


BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_DIR = BASE_DIR / "output"

CAT_IMAGE_FILES = [ASSETS_DIR / f"cat{i}.jpg" for i in range(1, 5)]
MUSIC_FILE = ASSETS_DIR / "music.wav"
TEXT_FILE = ASSETS_DIR / "alphatwice.txt"

COLLAGE_OUTPUT = OUTPUT_DIR / "cat_collage.jpg"
AUDIO_OUTPUT = OUTPUT_DIR / "music_even_seconds_removed.wav"
HIST_OUTPUT = OUTPUT_DIR / "letter_top10_hist.png"

TARGET_IMAGE_SIZE = (320, 320)


def ensure_inputs_exist(paths: list[Path]) -> None:
    missing_paths = [str(path) for path in paths if not path.exists()]
    if missing_paths:
        joined = "\n".join(missing_paths)
        raise FileNotFoundError(f"缺少实验素材文件：\n{joined}")


def create_cat_collage() -> None:
    resized_images = []
    for image_path in CAT_IMAGE_FILES:
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"无法读取图像文件：{image_path}")
        resized_images.append(cv2.resize(image, TARGET_IMAGE_SIZE))

    top_row = cv2.hconcat(resized_images[:2])
    bottom_row = cv2.hconcat(resized_images[2:])
    collage = cv2.vconcat([top_row, bottom_row])

    if not cv2.imwrite(str(COLLAGE_OUTPUT), collage):
        raise IOError(f"无法保存拼贴画：{COLLAGE_OUTPUT}")

    print(f"[图像] 拼贴画已保存到: {COLLAGE_OUTPUT}")


def play_original_music() -> None:
    try:
        samples, sample_rate = sf.read(str(MUSIC_FILE), dtype="float32")
        preview_ms = min(int(len(samples) / sample_rate * 1000), 3000)
        print(f"[音频] 正在播放原始音频预览: {MUSIC_FILE}")
        sd.play(samples, sample_rate)
        sd.sleep(preview_ms)
        sd.stop()
        print(f"[音频] 原始音频预览完成，播放时长约 {preview_ms / 1000:.1f} 秒")
    except Exception as exc:  # pragma: no cover - depends on host audio device
        print(f"[音频] 播放失败，但会继续执行音频处理: {exc}")


def remove_even_second_segments() -> None:
    audio = AudioSegment.from_wav(MUSIC_FILE)
    kept_segments = []

    for start_ms in range(0, len(audio), 1000):
        end_ms = min(start_ms + 1000, len(audio))
        second_index = start_ms // 1000 + 1
        if second_index % 2 == 1:
            kept_segments.append(audio[start_ms:end_ms])

    processed_audio = AudioSegment.empty()
    for segment in kept_segments:
        processed_audio += segment

    processed_audio.export(AUDIO_OUTPUT, format="wav")
    print(f"[音频] 删除偶数秒后的音频已保存到: {AUDIO_OUTPUT}")


def analyze_text_and_plot() -> None:
    text = TEXT_FILE.read_text(encoding="utf-8")
    counts = Counter(char for char in text if char in string.ascii_letters)
    top_10 = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:10]

    if not top_10:
        raise ValueError(f"文本中没有可统计的英文字母: {TEXT_FILE}")

    letters = [item[0] for item in top_10]
    frequencies = [item[1] for item in top_10]

    plt.figure(figsize=(10, 6))
    bars = plt.bar(letters, frequencies, color="#4C72B0")
    plt.title("Top 10 English Letters by Frequency")
    plt.xlabel("Letter")
    plt.ylabel("Count")
    plt.grid(axis="y", linestyle="--", alpha=0.3)

    for bar, frequency in zip(bars, frequencies):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            frequency,
            str(frequency),
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.savefig(HIST_OUTPUT, dpi=200)
    plt.close()

    print("[文本] 出现次数最高的 10 个英文字母:")
    for letter, frequency in top_10:
        print(f"  {letter}: {frequency}")
    print(f"[文本] 直方图已保存到: {HIST_OUTPUT}")


def main() -> int:
    ensure_inputs_exist(CAT_IMAGE_FILES + [MUSIC_FILE, TEXT_FILE])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    create_cat_collage()
    play_original_music()
    remove_even_second_segments()
    analyze_text_and_plot()

    print("[完成] 三项实验任务已全部执行完成")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        raise SystemExit(1)
