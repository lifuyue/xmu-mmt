"""Experiment 4: video capture, OpenCV face detection, and dlib landmarks.

Run examples:
    python lab4_video_capture_processing.py --mode opencv
    python lab4_video_capture_processing.py --mode dlib --predictor shape_predictor_68_face_landmarks.dat
    python lab4_video_capture_processing.py --mode dlib --download-predictor

Press q or Esc in the video window to exit.
"""

from __future__ import annotations

import argparse
import bz2
import sys
import urllib.request
from pathlib import Path


PREDICTOR_URL = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
DEFAULT_PREDICTOR = Path("shape_predictor_68_face_landmarks.dat")

cv2 = None
dlib = None


def require_cv2():
    """Import OpenCV lazily so dependency errors can be explained clearly."""
    global cv2
    if cv2 is None:
        try:
            import cv2 as imported_cv2
        except ImportError as exc:
            raise RuntimeError(
                "未安装 opencv-python，请先执行：python -m pip install opencv-python"
            ) from exc
        cv2 = imported_cv2
    return cv2


def require_dlib():
    """Import dlib lazily because only landmark mode needs it."""
    global dlib
    if dlib is None:
        try:
            import dlib as imported_dlib
        except ImportError as exc:
            raise RuntimeError("未安装 dlib，请先执行：python -m pip install dlib") from exc
        dlib = imported_dlib
    return dlib


def download_predictor(destination: Path) -> Path:
    """Download and decompress dlib's 68-point face landmark model."""
    destination = destination.expanduser().resolve()
    if destination.exists():
        print(f"[模型] 已存在：{destination}")
        return destination

    compressed_path = destination.with_suffix(destination.suffix + ".bz2")
    print(f"[模型] 下载：{PREDICTOR_URL}")
    urllib.request.urlretrieve(PREDICTOR_URL, compressed_path)

    print(f"[模型] 解压到：{destination}")
    with bz2.open(compressed_path, "rb") as source, destination.open("wb") as target:
        target.write(source.read())
    compressed_path.unlink(missing_ok=True)
    return destination


def create_face_cascade():
    """Load OpenCV's default Haar cascade classifier for frontal faces."""
    cv = require_cv2()
    cascade_path = Path(cv.data.haarcascades) / "haarcascade_frontalface_default.xml"
    classifier = cv.CascadeClassifier(str(cascade_path))
    if classifier.empty():
        raise RuntimeError(f"无法加载 OpenCV 人脸分类器：{cascade_path}")
    return classifier


def detect_faces_with_opencv(frame, classifier):
    """Detect faces with OpenCV and draw green rectangles."""
    cv = require_cv2()
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    gray = cv.equalizeHist(gray)
    faces = classifier.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(40, 40),
        flags=cv.CASCADE_SCALE_IMAGE,
    )

    for x, y, width, height in faces:
        cv.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 2)
        cv.putText(
            frame,
            "OpenCV face",
            (x, max(20, y - 8)),
            cv.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 0),
            2,
            cv.LINE_AA,
        )
    return len(faces)


def create_dlib_detectors(predictor_path: Path):
    """Create dlib's face detector and shape predictor."""
    dl = require_dlib()
    predictor_path = predictor_path.expanduser().resolve()
    if not predictor_path.exists():
        raise RuntimeError(
            "未找到 68 点模型文件："
            f"{predictor_path}\n"
            "可执行：python lab4_video_capture_processing.py --mode dlib --download-predictor"
        )
    detector = dl.get_frontal_face_detector()
    predictor = dl.shape_predictor(str(predictor_path))
    return detector, predictor


def detect_landmarks_with_dlib(frame, detector, predictor):
    """Detect faces with dlib and draw 68 landmark points on each face."""
    cv = require_cv2()
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    rectangles = detector(gray, 1)

    for rect in rectangles:
        cv.rectangle(
            frame,
            (rect.left(), rect.top()),
            (rect.right(), rect.bottom()),
            (255, 180, 0),
            2,
        )
        shape = predictor(gray, rect)
        for index in range(68):
            point = shape.part(index)
            cv.circle(frame, (point.x, point.y), 2, (0, 0, 255), -1)
            cv.putText(
                frame,
                str(index + 1),
                (point.x + 2, point.y - 2),
                cv.FONT_HERSHEY_SIMPLEX,
                0.25,
                (255, 255, 255),
                1,
                cv.LINE_AA,
            )
    return len(rectangles)


def open_camera(camera_index: int, width: int, height: int):
    """Open the webcam and set a stable capture size."""
    cv = require_cv2()
    capture = cv.VideoCapture(camera_index)
    if not capture.isOpened():
        raise RuntimeError(f"无法打开摄像头：index={camera_index}")
    capture.set(cv.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv.CAP_PROP_FRAME_HEIGHT, height)
    return capture


def run_video_loop(args):
    """Read each frame, process it, and display the real-time result."""
    cv = require_cv2()

    face_classifier = create_face_cascade() if args.mode in {"opencv", "both"} else None
    dlib_detector = dlib_predictor = None
    if args.mode in {"dlib", "both"}:
        dlib_detector, dlib_predictor = create_dlib_detectors(args.predictor)

    capture = open_camera(args.camera, args.width, args.height)
    window_name = f"Experiment 4 - {args.mode}"
    cv.namedWindow(window_name, cv.WINDOW_NORMAL)

    print("[运行] 摄像头已启动，按 q 或 Esc 退出。")
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                print("[警告] 未能读取视频帧，程序结束。")
                break

            if args.mirror:
                frame = cv.flip(frame, 1)

            face_count = 0
            if face_classifier is not None:
                face_count = max(face_count, detect_faces_with_opencv(frame, face_classifier))
            if dlib_detector is not None and dlib_predictor is not None:
                face_count = max(face_count, detect_landmarks_with_dlib(frame, dlib_detector, dlib_predictor))

            cv.putText(
                frame,
                f"faces: {face_count} | press q/ESC to quit",
                (16, 28),
                cv.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 255),
                2,
                cv.LINE_AA,
            )
            cv.imshow(window_name, frame)

            key = cv.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break
    finally:
        capture.release()
        cv.destroyAllWindows()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="实验四：视频捕获与视频处理")
    parser.add_argument(
        "--mode",
        choices=("opencv", "dlib", "both"),
        default="opencv",
        help="opencv：Haar 人脸矩形框；dlib：68 点特征；both：同时显示两种结果",
    )
    parser.add_argument("--camera", type=int, default=0, help="摄像头编号，默认 0")
    parser.add_argument("--width", type=int, default=640, help="视频窗口宽度")
    parser.add_argument("--height", type=int, default=480, help="视频窗口高度")
    parser.add_argument("--mirror", action="store_true", help="水平镜像显示，适合前置摄像头")
    parser.add_argument(
        "--predictor",
        type=Path,
        default=DEFAULT_PREDICTOR,
        help="dlib 68 点模型 shape_predictor_68_face_landmarks.dat 的路径",
    )
    parser.add_argument(
        "--download-predictor",
        action="store_true",
        help="下载并解压 dlib 68 点模型到 --predictor 指定位置",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.download_predictor:
            download_predictor(args.predictor)
        run_video_loop(args)
    except RuntimeError as exc:
        print(f"[错误] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
