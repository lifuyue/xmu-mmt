from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def _read_u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "little", signed=False)


def _read_u32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little", signed=False)


def _read_i32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little", signed=True)


def _align_to_4(value: int) -> int:
    return (value + 3) & ~3


@dataclass
class BitmapFileHeader:
    bf_type: int
    bf_size: int
    bf_reserved1: int
    bf_reserved2: int
    bf_off_bits: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "BitmapFileHeader":
        if len(data) < 14:
            raise ValueError("BMP 文件头长度不足")
        return cls(
            bf_type=_read_u16(data, 0),
            bf_size=_read_u32(data, 2),
            bf_reserved1=_read_u16(data, 6),
            bf_reserved2=_read_u16(data, 8),
            bf_off_bits=_read_u32(data, 10),
        )

    def to_bytes(self) -> bytes:
        return b"".join(
            [
                self.bf_type.to_bytes(2, "little"),
                self.bf_size.to_bytes(4, "little"),
                self.bf_reserved1.to_bytes(2, "little"),
                self.bf_reserved2.to_bytes(2, "little"),
                self.bf_off_bits.to_bytes(4, "little"),
            ]
        )


@dataclass
class BitmapInfoHeader:
    bi_size: int
    bi_width: int
    bi_height: int
    bi_planes: int
    bi_bit_count: int
    bi_compression: int
    bi_size_image: int
    bi_x_pels_per_meter: int
    bi_y_pels_per_meter: int
    bi_clr_used: int
    bi_clr_important: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "BitmapInfoHeader":
        if len(data) < 40:
            raise ValueError("BMP 信息头长度不足")
        return cls(
            bi_size=_read_u32(data, 0),
            bi_width=_read_i32(data, 4),
            bi_height=_read_i32(data, 8),
            bi_planes=_read_u16(data, 12),
            bi_bit_count=_read_u16(data, 14),
            bi_compression=_read_u32(data, 16),
            bi_size_image=_read_u32(data, 20),
            bi_x_pels_per_meter=_read_i32(data, 24),
            bi_y_pels_per_meter=_read_i32(data, 28),
            bi_clr_used=_read_u32(data, 32),
            bi_clr_important=_read_u32(data, 36),
        )

    def to_bytes(self) -> bytes:
        return b"".join(
            [
                self.bi_size.to_bytes(4, "little"),
                self.bi_width.to_bytes(4, "little", signed=True),
                self.bi_height.to_bytes(4, "little", signed=True),
                self.bi_planes.to_bytes(2, "little"),
                self.bi_bit_count.to_bytes(2, "little"),
                self.bi_compression.to_bytes(4, "little"),
                self.bi_size_image.to_bytes(4, "little"),
                self.bi_x_pels_per_meter.to_bytes(4, "little", signed=True),
                self.bi_y_pels_per_meter.to_bytes(4, "little", signed=True),
                self.bi_clr_used.to_bytes(4, "little"),
                self.bi_clr_important.to_bytes(4, "little"),
            ]
        )


@dataclass
class RGBQuad:
    blue: int
    green: int
    red: int
    reserved: int = 0

    @classmethod
    def from_bytes(cls, data: bytes) -> "RGBQuad":
        if len(data) != 4:
            raise ValueError("颜色表项必须为 4 字节")
        return cls(blue=data[0], green=data[1], red=data[2], reserved=data[3])

    def to_bytes(self) -> bytes:
        return bytes([self.blue, self.green, self.red, self.reserved])


class BMPImage:
    def __init__(
        self,
        file_header: BitmapFileHeader,
        info_header: BitmapInfoHeader,
        palette: list[RGBQuad],
        pixels: list[list[int | tuple[int, int, int]]],
    ) -> None:
        self.file_header = file_header
        self.info_header = info_header
        self.palette = palette
        self.pixels = pixels

    @property
    def width(self) -> int:
        return self.info_header.bi_width

    @property
    def height(self) -> int:
        return abs(self.info_header.bi_height)

    @property
    def bit_count(self) -> int:
        return self.info_header.bi_bit_count

    @classmethod
    def from_file(cls, path: str | Path) -> "BMPImage":
        path = Path(path)
        data = path.read_bytes()
        file_header = BitmapFileHeader.from_bytes(data[:14])
        if file_header.bf_type != 0x4D42:
            raise ValueError(f"不是有效的 BMP 文件: {path}")

        info_header = BitmapInfoHeader.from_bytes(data[14:54])
        if info_header.bi_size != 40:
            raise ValueError("仅支持 BITMAPINFOHEADER(40 字节)")
        if info_header.bi_planes != 1:
            raise ValueError("BMP 文件的 biPlanes 必须为 1")
        if info_header.bi_compression != 0:
            raise ValueError("仅支持未压缩 BMP 文件")
        if info_header.bi_bit_count not in (8, 24):
            raise ValueError("仅支持 8 位或 24 位 BMP 文件")

        palette = cls._read_palette(data, file_header, info_header)
        pixels = cls._read_pixels(data, file_header, info_header)
        return cls(file_header, info_header, palette, pixels)

    @staticmethod
    def _read_palette(
        data: bytes,
        file_header: BitmapFileHeader,
        info_header: BitmapInfoHeader,
    ) -> list[RGBQuad]:
        if info_header.bi_bit_count != 8:
            return []

        palette_colors = info_header.bi_clr_used or 256
        palette_start = 14 + info_header.bi_size
        palette_end = file_header.bf_off_bits
        palette_bytes = data[palette_start:palette_end]
        required_length = palette_colors * 4
        if len(palette_bytes) < required_length:
            raise ValueError("8 位 BMP 颜色表数据不完整")

        palette = []
        for offset in range(0, required_length, 4):
            palette.append(RGBQuad.from_bytes(palette_bytes[offset : offset + 4]))
        return palette

    @staticmethod
    def _read_pixels(
        data: bytes,
        file_header: BitmapFileHeader,
        info_header: BitmapInfoHeader,
    ) -> list[list[int | tuple[int, int, int]]]:
        width = info_header.bi_width
        height = abs(info_header.bi_height)
        bottom_up = info_header.bi_height > 0
        line_bytes = _align_to_4((width * info_header.bi_bit_count) // 8)
        pixel_data = data[file_header.bf_off_bits :]

        rows: list[list[int | tuple[int, int, int]]] = []
        for row_index in range(height):
            row_offset = row_index * line_bytes
            row_data = pixel_data[row_offset : row_offset + line_bytes]
            if len(row_data) < line_bytes:
                raise ValueError("像素数据长度不足")

            if info_header.bi_bit_count == 24:
                row = []
                for column in range(width):
                    base = column * 3
                    blue = row_data[base]
                    green = row_data[base + 1]
                    red = row_data[base + 2]
                    row.append((red, green, blue))
            else:
                row = list(row_data[:width])
            rows.append(row)

        if bottom_up:
            rows.reverse()
        return rows

    def to_grayscale_8bit(self) -> "BMPImage":
        if self.bit_count != 24:
            raise ValueError("仅支持将 24 位 BMP 转换为 8 位灰度 BMP")

        gray_pixels: list[list[int]] = []
        for row in self.pixels:
            gray_row: list[int] = []
            for red, green, blue in row:  # type: ignore[misc]
                gray = int(red * 0.299 + green * 0.587 + blue * 0.114 + 0.5)
                gray_row.append(gray)
            gray_pixels.append(gray_row)

        gray_palette = [RGBQuad(i, i, i, 0) for i in range(256)]
        return self._build_new_image(bit_count=8, palette=gray_palette, pixels=gray_pixels)

    def to_truecolor_24bit(self) -> "BMPImage":
        if self.bit_count != 8:
            raise ValueError("仅支持将 8 位 BMP 转换为 24 位 BMP")
        if not self.palette:
            raise ValueError("8 位 BMP 缺少颜色表")

        rgb_pixels: list[list[tuple[int, int, int]]] = []
        for row in self.pixels:
            rgb_row: list[tuple[int, int, int]] = []
            for pixel_index in row:  # type: ignore[assignment]
                color = self.palette[pixel_index]
                rgb_row.append((color.red, color.green, color.blue))
            rgb_pixels.append(rgb_row)

        return self._build_new_image(bit_count=24, palette=[], pixels=rgb_pixels)

    def _build_new_image(
        self,
        bit_count: int,
        palette: list[RGBQuad],
        pixels: list[list[int | tuple[int, int, int]]],
    ) -> "BMPImage":
        width = self.width
        height = self.height
        row_size = _align_to_4((width * bit_count) // 8)
        image_size = row_size * height
        palette_size = len(palette) * 4
        off_bits = 14 + 40 + palette_size
        file_size = off_bits + image_size

        file_header = BitmapFileHeader(
            bf_type=0x4D42,
            bf_size=file_size,
            bf_reserved1=0,
            bf_reserved2=0,
            bf_off_bits=off_bits,
        )
        info_header = BitmapInfoHeader(
            bi_size=40,
            bi_width=width,
            bi_height=height,
            bi_planes=1,
            bi_bit_count=bit_count,
            bi_compression=0,
            bi_size_image=image_size,
            bi_x_pels_per_meter=self.info_header.bi_x_pels_per_meter,
            bi_y_pels_per_meter=self.info_header.bi_y_pels_per_meter,
            bi_clr_used=len(palette) if palette else 0,
            bi_clr_important=0,
        )
        return BMPImage(file_header, info_header, palette, pixels)

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.to_bytes())

    def to_bytes(self) -> bytes:
        header_bytes = self.file_header.to_bytes() + self.info_header.to_bytes()
        palette_bytes = b"".join(color.to_bytes() for color in self.palette)
        pixel_bytes = self._encode_pixels()
        return header_bytes + palette_bytes + pixel_bytes

    def _encode_pixels(self) -> bytes:
        row_bytes = bytearray()
        width = self.width

        if self.bit_count == 24:
            raw_row_size = width * 3
        else:
            raw_row_size = width
        line_bytes = _align_to_4(raw_row_size)
        padding = b"\x00" * (line_bytes - raw_row_size)

        for row in reversed(self.pixels):
            if self.bit_count == 24:
                encoded_row = bytearray()
                for red, green, blue in row:  # type: ignore[misc]
                    encoded_row.extend([blue, green, red])
            else:
                encoded_row = bytearray(row)  # type: ignore[arg-type]
            row_bytes.extend(encoded_row)
            row_bytes.extend(padding)
        return bytes(row_bytes)
