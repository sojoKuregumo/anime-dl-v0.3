#..........This Bot Made By [RAHAT](https://t.me/r4h4t_69)..........#
#..........Anyone Can Modify This As He Likes..........#
#..........Just one request: do not remove my credit...#

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import MessageNotModified
from plugins.queue import add_to_queue, remove_from_queue
from plugins.direct_link import get_dl_link
from plugins.headers import *
from plugins.file import *
from plugins.commands import user_queries
from helper.database import *
from config import DOWNLOAD_DIR
from bs4 import BeautifulSoup
import os
import re
import requests
import ssl
import subprocess
import shlex
import time
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

episode_data = {}


# ===== TLS Adapter for handshake fix =====
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        try:
            ctx.set_ciphers('DEFAULT@SECLEVEL=1')
        except Exception:
            pass
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

session_tls = requests.Session()
session_tls.mount("https://", TLSAdapter())

# ---------- aria2 helper ----------
def aria2_download_with_progress(url, out_dir, out_name, msg=None, user_id=None,
                                  max_conn=12, split=12, min_split_size="1M", poll_interval=1.5):
    """
    Run aria2c to download the file (multi-connection). While it's running,
    poll the file size and update 'msg' every poll_interval seconds to show progress.
    Returns full path on success, raises Exception on failure.
    """
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, out_name)

    # Try HEAD to get total size
    try:
        head = session_tls.head(url, allow_redirects=True, timeout=15)
        total = int(head.headers.get("content-length", 0))
    except Exception:
        total = 0

    cmd = [
        "aria2c",
        "-x", str(max_conn),
        "-s", str(split),
        "--min-split-size=" + min_split_size,
        "--allow-overwrite=true",
        "--auto-file-renaming=false",
        "-o", out_name,
        "-d", out_dir,
        "--check-certificate=true",
        "--console-log-level=warn",
        url
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    last_update = 0.0

    try:
        while proc.poll() is None:
            # support cancel (if implemented)
            if user_id is not None and globals().get("active_downloads", {}).get(user_id, {}).get("cancel"):
                proc.terminate()
                proc.wait(timeout=5)
                if os.path.exists(out_path):
                    try: os.remove(out_path)
                    except: pass
                raise Exception("Download cancelled by user")

            # check partial file size
            size = os.path.getsize(out_path) if os.path.exists(out_path) else 0

            now = time.time()
            if msg and (now - last_update) >= poll_interval:
                if total > 0:
                    percent = size / total * 100
                    bar_len = 20
                    filled = int(bar_len * size / total)
                    bar = "█" * filled + "░" * (bar_len - filled)
                    text = f"Downloading: {os.path.basename(out_path)}\n[{bar}] {percent:.1f}%\n{size/1024/1024:.2f}MB / {total/1024/1024:.2f}MB"
                else:
                    text = f"Downloading: {os.path.basename(out_path)}\nDownloaded: {size/1024/1024:.2f} MB (size unknown)"
                try:
                    msg.edit_text(text)
                except Exception:
                    pass
                last_update = now

            time.sleep(0.25)

        # finished
        ret = proc.returncode
        stderr = proc.stderr.read() if proc.stderr else ""
        if ret != 0:
            raise Exception(f"aria2c failed (code {ret}): {stderr[:400]}")
        if not os.path.exists(out_path):
            raise Exception("aria2c finished but file not found")
        if msg:
            try:
                msg.edit_text(f"Download complete: {os.path.basename(out_path)}")
            except:
                pass
        return out_path

    except Exception:
        try:
            proc.terminate()
        except:
            pass
        raise

# ---------- wrapper: try aria2, fallback to python downloader ----------
def download_helper(url, out_dir, out_name, progress_msg=None, user_id=None):
    """
    Attempt aria2 first. If aria2 missing or fails, fallback to existing safe_download.
    Returns downloaded file path on success.
    """
    try:
        subprocess.run(["aria2c", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        try:
            path = aria2_download_with_progress(url, out_dir, out_name, msg=progress_msg, user_id=user_id)
            return path
        except Exception as e:
            if progress_msg:
                try:
                    progress_msg.edit_text("aria2c failed, falling back to single-connection downloader...")
                except:
                    pass
            print("aria2 failed, falling back:", e)
    except Exception:
        if progress_msg:
            try:
                progress_msg.edit_text("aria2c not found, using internal downloader...")
            except:
                pass

    out_path = os.path.join(out_dir, out_name)
    # Re-use your existing safe_download function for fallback
    safe_download(url, out_path)
    if progress_msg:
        try:
            progress_msg.edit_text("Download complete (fallback).")
        except:
            pass
    return out_path


# ========= ANIME DETAILS =========
@Client.on_callback_query(filters.regex(r"^anime_"))
def anime_details(client, callback_query):
    session_id = callback_query.data.split("anime_")[1]
    query = user_queries.get(callback_query.message.chat.id, "")
    search_url = f"https://animepahe.ru/api?m=search&q={query.replace(' ', '+')}"
    response = session.get(search_url).json()

    anime = next(anime for anime in response['data'] if anime['session'] == session_id)
    title = anime['title']
    anime_link = f"https://animepahe.ru/anime/{session_id}"

    message_text = (
        f"**🎬 Title**: {title}\n"
        f"**📺 Type**: {anime['type']}\n"
        f"**🎯 Episodes**: {anime['episodes']}\n"
        f"**📌 Status**: {anime['status']}\n"
        f"**🍂 Season**: {anime['season']}\n"
        f"**📅 Year**: {anime['year']}\n"
        f"**⭐ Score**: {anime['score']}\n"
        f"[🔗 Anime Link]({anime_link})\n\n"
        f"**Bot Made By**\n"
        f"    **[RAHAT](tg://user?id=1235222889)**"
    )

    episode_data[callback_query.message.chat.id] = {
        "session_id": session_id,
        "poster": anime['poster'],
        "title": title
    }

    episode_button = InlineKeyboardMarkup([[InlineKeyboardButton("📜 Episodes", callback_data="episodes")]])
    client.send_photo(
        chat_id=callback_query.message.chat.id,
        photo=anime['poster'],
        caption=message_text,
        reply_markup=episode_button
    )

# ========= EPISODE LIST =========
@Client.on_callback_query(filters.regex(r"^episodes$"))
def episode_list(client, callback_query, page=1):
    session_data = episode_data.get(callback_query.message.chat.id)
    if not session_data:
        return callback_query.message.reply_text("❌ Session ID not found.")

    session_id = session_data['session_id']
    episodes_url = f"https://animepahe.ru/api?m=release&id={session_id}&sort=episode_asc&page={page}"
    response = session.get(episodes_url).json()

    last_page = int(response["last_page"])
    episodes = response['data']

    episode_data[callback_query.message.chat.id].update({
        'current_page': page,
        'last_page': last_page,
        'episodes': {ep['episode']: ep['session'] for ep in episodes}
    })

    episode_buttons = [
        [InlineKeyboardButton(f"🎬 Episode {ep['episode']}", callback_data=f"ep_{ep['episode']}")]
        for ep in episodes
    ]

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"page_{page - 1}"))
    if page < last_page:
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"page_{page + 1}"))
    if nav_buttons:
        episode_buttons.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(episode_buttons)

    try:
        if callback_query.message.reply_markup != reply_markup:
            callback_query.message.edit_reply_markup(reply_markup)
    except MessageNotModified:
        pass

# ========= PAGINATION =========
@Client.on_callback_query(filters.regex(r"^page_"))
def navigate_pages(client, callback_query):
    new_page = int(callback_query.data.split("_")[1])
    session_data = episode_data.get(callback_query.message.chat.id)

    if not session_data:
        return callback_query.message.reply_text("❌ Session ID not found.")

    if new_page < 1:
        callback_query.answer("You're already on the first page.", show_alert=True)
    elif new_page > session_data.get('last_page', 1):
        callback_query.answer("You're already on the last page.", show_alert=True)
    else:
        episode_list(client, callback_query, page=new_page)

# ========= FETCH DOWNLOAD LINKS =========
@Client.on_callback_query(filters.regex(r"^ep_"))
def fetch_download_links(client, callback_query):
    episode_number = int(callback_query.data.split("_")[1])
    user_id = callback_query.message.chat.id
    session_data = episode_data.get(user_id)

    if not session_data or 'episodes' not in session_data:
        return callback_query.message.reply_text("❌ Episode not found.")

    episode_data[user_id]['current_episode'] = episode_number
    episode_url = f"https://animepahe.ru/play/{session_data['session_id']}/{session_data['episodes'][episode_number]}"

    soup = BeautifulSoup(session.get(episode_url).content, "html.parser")
    download_links = soup.select("#pickDownload a.dropdown-item")
    if not download_links:
        return callback_query.message.reply_text("❌ No download links found.")

    download_buttons = [
        [InlineKeyboardButton(link.get_text(strip=True), callback_data=f"dl_{link['href']}")]
        for link in download_links
    ]
    callback_query.message.reply_text("📥 Select a download link:", reply_markup=InlineKeyboardMarkup(download_buttons))

# ========= DOWNLOAD WITH TLS RETRY =========
def safe_download(url, path, retries=3):
    for attempt in range(retries):
        try:
            with session_tls.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in r.iter_content(1024 * 64):
                        f.write(chunk)
            return True
        except Exception as e:
            print(f"[Retry {attempt+1}] Download failed: {e}")
            time.sleep(2 + attempt)
            try:
                url = get_dl_link(url)  # refresh link if expired
            except:
                pass
    raise Exception("Failed to download after retries.")

# ========= DOWNLOAD AND UPLOAD =========
@Client.on_callback_query(filters.regex(r"^dl_"))
def download_and_upload_file(client, callback_query):
    download_url = callback_query.data.split("dl_")[1]
    try:
        direct_link = get_dl_link(download_url)
    except Exception as e:
        return callback_query.message.reply_text(f"❌ Error generating link: {e}")

    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Unknown User"
    add_to_queue(user_id, username, direct_link)

    ep_num = episode_data.get(user_id, {}).get('current_episode', 'Unknown')
    title = episode_data.get(user_id, {}).get('title', 'Unknown Title')

    button_title = next((b.text for row in callback_query.message.reply_markup.inline_keyboard for b in row if b.callback_data == f"dl_{download_url}"), "Unknown Source")
    resolution = re.search(r"\b\d{3,4}p\b", button_title)
    resolution = resolution.group() if resolution else button_title
    type_ = "Dub" if 'eng' in button_title.lower() else "Sub"
    file_name = sanitize_filename(f"[{type_}] [{create_short_name(title)}] [EP {ep_num}] [{resolution}].mp4")

    random_str = random_string(5)
    user_dir = os.path.join(DOWNLOAD_DIR, str(user_id), random_str)
    os.makedirs(user_dir, exist_ok=True)
    download_path = os.path.join(user_dir, file_name)

    dl_msg = callback_query.message.reply_text(f"📥 **Added to queue:**\n`{file_name}`\n⏳ Downloading...")

    try:
        # Try aria2 first, fall back to internal safe_download
        downloaded_path = download_helper(direct_link, user_dir, file_name, progress_msg=dl_msg, user_id=user_id)
        # download_helper returns the actual downloaded file path
        download_path = downloaded_path
        dl_msg.edit_text("✅ Download complete. 📤 Uploading...")

        thumb_path = None
        thumb_data = get_thumbnail(user_id) or episode_data.get(user_id, {}).get("poster")
        if thumb_data:
            if thumb_data.startswith("http"):
                r = requests.get(thumb_data, stream=True)
                thumb_path = os.path.join(user_dir, "thumb.jpg")
                with open(thumb_path, "wb") as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
            else:
                thumb_path = client.download_media(thumb_data)

        caption = get_caption(user_id) or file_name
        send_and_delete_file(client, callback_query.message.chat.id, download_path, thumb_path, caption, user_id)

        remove_from_queue(user_id, direct_link)
        dl_msg.edit_text("🎉 **Episode Uploaded Successfully!**")

        if thumb_path and os.path.exists(thumb_path): os.remove(thumb_path)
        if os.path.exists(user_dir): remove_directory(user_dir)

    except Exception as e:
        callback_query.message.reply_text(f"❌ Error: {e}")


# ========= HELP / CLOSE =========
@Client.on_callback_query()
def callback_query_handler(client, callback_query):
    if callback_query.data == "help":
        callback_query.message.edit_text(
            "📖 **How to use the bot:**\n\n"
            "1️⃣ `/anime <name>` - Search for an anime\n"
            "2️⃣ `/set_thumb` - Set custom thumbnail\n"
            "3️⃣ `/options` - Set upload type\n"
            "4️⃣ `/queue` - See active downloads\n"
            "5️⃣ `/set_caption` - Custom caption\n"
            "6️⃣ `/see_caption` - View caption\n"
            "7️⃣ `/del_caption` - Remove caption",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close")]])
        )
    elif callback_query.data == "close":
        callback_query.message.delete()
