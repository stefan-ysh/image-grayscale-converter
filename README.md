# image-grayscale-converter

A powerful tool for converting images to grayscale and analyzing grayscale intensity, using the OpenCV library.

## Features

- Convert images to grayscale
- Analyze grayscale intensity in selected regions
- Generate charts for grayscale analysis
- Export analysis data to Excel
- Save grayscale images with analysis regions

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/stefan-ysh/image-grayscale-converter.git
   ```

2. Install the required dependencies:

   ```
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

## Usage

1. Run the script:

   ```
   python ./main.py
   ```

2. Use the GUI to:
   - Select an image for analysis
   - Draw rectangles on the image to define analysis regions
   - Adjust the number of analysis points for each region
   - View grayscale intensity charts for each region
   - Export analysis data to Excel
   - Save grayscale images with analysis regions

## Building Executable

> **Note:** If you want to build a standalone executable, you need to install `PyInstaller` first.And open a new terminal in the project directory.

```
pip install pyinstaller
```

To create a standalone executable:

```
pyinstaller --onefile --windowed --icon ./logo.ico ./main.py -n "Grayscale Converter"
```

```
pyinstaller --onedir --windowed --icon ./logo.ico ./main.py -n "Grayscale Converter"
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
