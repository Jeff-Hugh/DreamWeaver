# Copyright (C) 2025 <name of author>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import PyInstaller.__main__
import os

def get_data_files():
    data_files = [
        'Home.html',
        'DreamCanvas.html',
        'DreamViewer.html',
        'kaiti.ttf'
    ]
    # On Windows, use semicolon as separator; on Unix-like systems, use colon
    separator = ';' if os.name == 'nt' else ':'
    return [f'{src}{separator}.' for src in data_files]

if __name__ == '__main__':
    # Basic PyInstaller arguments
    args = [
        'app.py',
        '--name=DreamWeaver',
        '--onefile'
    ]

    # Add data files
    for data_file in get_data_files():
        args.extend(['--add-data', data_file])

    PyInstaller.__main__.run(args)
