# LAB3

《多媒体技术》实验三：BMP 位图文件的解析

## 实现内容

- `bmp_image.py`：使用类手动解析/写回 8 位和 24 位未压缩 BMP 文件
- `convert_24_to_8.py`：读取 `~/Downloads/实验三素材/24位真彩色BMP` 中的 24 位 BMP，转换为 8 位灰度 BMP
- `convert_8_to_24.py`：读取 `~/Downloads/实验三素材/8位伪彩色BMP` 中的 8 位 BMP，转换为 24 位真彩色 BMP
- `main.py`：一次性执行两个实验任务
- `output/`：程序运行后生成的结果文件

## 设计说明

- 未使用 `opencv`、`PIL` 等图像库，直接通过字节流解析 BMP 文件头、信息头、颜色表和像素阵列
- 使用 `BitmapFileHeader`、`BitmapInfoHeader`、`RGBQuad`、`BMPImage` 等类实现面向对象封装
- 支持 BMP 的 4 字节对齐规则
- 24 位转灰度采用公式：`Gray = R * 0.299 + G * 0.587 + B * 0.114`
- 8 位转 24 位时，根据颜色表把每个像素索引展开为 `(R, G, B)`

## 运行方式

```bash
cd /Users/lifuyue/Projects/xmu-mmt/LAB3
python3 main.py
```

也可以分别执行：

```bash
python3 convert_24_to_8.py
python3 convert_8_to_24.py
```

## 输出目录

- `output/24_to_8/`：24 位 BMP 转换后的 8 位灰度 BMP
- `output/8_to_24/`：8 位 BMP 转换后的 24 位真彩色 BMP
