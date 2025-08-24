#..........This Bot Made By [RAHAT](https://t.me/r4h4t_69)..........#
#..........Anyone Can Modify This As He Likes..........#
#..........Just one requests do not remove my credit..........#

import os
import subprocess
import asyncio
import aria2p
from config import DOWNLOAD_DIR

# Initialize aria2
def init_aria2():
    # Create aria2 configuration
    aria2_config = f"""
dir={DOWNLOAD_DIR}
file-allocation=prealloc
continue=true
max-connection-per-server=16
min-split-size=1M
split=16
max-concurrent-downloads=10
max-overall-download-limit=0
max-download-limit=0
"""

    # Write config to file
    with open("aria2.conf", "w") as f:
        f.write(aria2_config)
    
    # Start aria2 process
    aria2_process = subprocess.Popen([
        "aria2c", 
        "--enable-rpc", 
        "--rpc-listen-all=false", 
        "--rpc-listen-port=6800",
        "--rpc-secret=secret",
        "--daemon=true",
        "--conf-path=aria2.conf"
    ])
    
    # Initialize aria2p client
    aria2 = aria2p.API(
        aria2p.Client(
            host="http://localhost",
            port=6800,
            secret="secret"
        )
    )
    
    return aria2, aria2_process

# Initialize aria2 on import
aria2_client, aria2_process = init_aria2()

async def download_with_aria2(url, file_name, message):
    """
    Downloads a file using aria2 for better performance
    """
    try:
        # Add download to aria2
        download = await aria2_client.add_uri(
            [url],
            {"out": file_name, "dir": DOWNLOAD_DIR}
        )
        
        # Monitor download progress
        while download.is_active:
            await asyncio.sleep(2)
            progress = download.progress
            await message.edit_text(f"Downloading... {progress:.2f}%")
            
            if progress == 100:
                break
                
        return os.path.join(DOWNLOAD_DIR, file_name)
        
    except Exception as e:
        await message.edit_text(f"Download error: {e}")
        return None

def cleanup_aria2():
    """Cleanup aria2 process"""
    if aria2_process:
        aria2_process.terminate()
