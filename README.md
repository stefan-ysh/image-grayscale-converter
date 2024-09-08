# image-grayscale-converter

A tool for converting images to grayscale, using the OpenCV library.

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/stefan-ysh/image-grayscale-converter.git
   ```

2. Install the required dependencies:

   ```
   pip install -r ./requirements.txt
   ```

## Usage

1. Run the script:

   ```
   python ./main.py
   ```

## License

MIT License

## Build

```
pyinstaller --onefile --windowed --icon ./1.ico ./main.py -n "Grayscale Converter"

> 打包文件夹
pyinstaller --onedir --windowed --icon ./1.ico ./main.py -n "Grayscale Converter"


pyinstaller --onefile --windowed --icon ./2.ico ./import_points.py -n Points2Image

> 打包文件夹
pyinstaller --onedir --windowed --icon ./2.ico ./import_points.py -n Points2Image

```