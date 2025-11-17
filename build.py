import PyInstaller.__main__
import os

def get_data_files():
    data_files = [
        'Home.html',
        'DreamCanvas.html',
        'DreamViewer.html',
        'kaiti.ttf'
    ]
    return [f'{src}{os.pathsep}.' for src in data_files]

if __name__ == '__main__':
    # Basic PyInstaller arguments
    args = [
        'app.py',
        '--name=DreamWeaver',
        '--onefile',
        '--windowed', # Use --windowed for GUI apps, equivalent to --noconsole
    ]

    # Add data files
    for data_file in get_data_files():
        args.extend(['--add-data', data_file])

    PyInstaller.__main__.run(args)
