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

import requests
import os
import uuid
from urllib.parse import urlparse

def download_file(url, save_directory="uploads"):
    """
    Download a file from a URL and save it locally
    
    Args:
        url (str): The URL of the file to download
        save_directory (str): Directory to save the file (default: "downloads")
    
    Returns:
        str: Path to the downloaded file or None if download failed
    """
    try:
        # Create the save directory if it doesn't exist
        os.makedirs(save_directory, exist_ok=True)
        
        # Get the filename with a random one
        filename = "generated_image_{}.png".format(uuid.uuid4())
        
        # Full path to save the file
        file_path = os.path.join(save_directory, filename)
        
        # Download the file
        print(f"Downloading file from: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Save the file
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        print(f"File downloaded successfully: {file_path}")
        return filename
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # The URL provided by the user
    url = "https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/7d/eb/20251105/c703e801/db01c00e-b614-40dc-99c3-8e46686c7bc8-1.png?Expires=1762956644&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=UU0EwyEfZS72AAdVjRavgHaK8U4%3D"
    
    # Download the file
    downloaded_file = download_file(url)
    
    if downloaded_file:
        print(f"Successfully downloaded: {downloaded_file}")
    else:
        print("Failed to download the file")
