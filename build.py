import PyInstaller.__main__
import os

def build_app():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Define PyInstaller command arguments
    args = [
        './main.py',
        '--onedir',
        '--windowed',
        '--icon', './assets/images/logo.ico',
        '--name', 'Grayscale Converter',
        '--add-data', f'{current_dir}/assets/fonts/MicrosoftYaHei.ttf:assets/fonts',
        '--add-data', f'{current_dir}/assets/images/logo.ico:assets/images',
    ]

    # Run PyInstaller
    PyInstaller.__main__.run(args)

if __name__ == "__main__":
    build_app()
