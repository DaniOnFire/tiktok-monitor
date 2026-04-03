import asyncio
import json
import os
from datetime import datetime
from telegram import Bot
from TikTokApi import TikTokApi

# ─── CONFIGURAZIONE ───────────────────────────────────────
TELEGRAM_TOKEN = "8786183518:AAGlH8j4ettuMtdQ8TKYRIcsGpTs7M8GStA"
CHAT_ID        = "291979788"
TIKTOK_USER    = "alessiadeda0"
CHECK_INTERVAL = 300
DATA_FILE      = "last_videos.json"
MS_TOKEN       = "RCtJqmMZGDUkUu3mrEg9-6uEVqpTCZgWjdfahWLJ9A55ESxKjQNJaE3QaaD6TCo-uKLKOVev-eJuGKH5HvPhlDJA6oNXE7k-9UAEFAzHLYzuZMaM13MNK-Mlg3Zih7cwjlMVliFMkeG8"
# ──────────────────────────────────────────────────────────

bot = Bot(token=TELEGRAM_TOKEN)

def load_known_videos():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_known_videos(video_ids):
    with open(DATA_FILE, "w") as f:
        json.dump(video_ids, f)

async def get_latest_videos(username):
    videos = []
    try:
        async with TikTokApi() as api:
            await api.create_sessions(
                ms_tokens=[MS_TOKEN],
                num_sessions=1,
                sleep_after=3,
                headless=True
            )
            user = api.user(username)
            async for video in user.videos(count=10):
                videos.append({
                    "id":    str(video.id),
                    "url":   f"https://www.tiktok.com/@{username}/video/{video.id}",
                    "desc":  video.as_dict.get("desc", "Nessuna descrizione"),
                    "likes": video.as_dict.get("stats", {}).get("diggCount", 0),
                })
    except Exception as e:
        print(f"[ERRORE] Recupero video: {e}")
    return videos

async def send_notification(video):
    msg = (
        f"🎵 *Nuovo video su TikTok!*\n\n"
        f"👤 @alessiadeda0\n"
        f"📝 {video['desc']}\n"
        f"❤️ {video['likes']} like\n\n"
        f"🔗 [Guarda il video]({video['url']})"
    )
    await bot.send_message(
        chat_id=CHAT_ID,
        text=msg,
        parse_mode="Markdown"
    )

async def monitor():
    print(f"[{datetime.now()}] Monitoraggio avviato per @alessiadeda0")
    known_ids = load_known_videos()

    if not known_ids:
        print("Prima esecuzione: salvo i video esistenti...")
        videos = await get_latest_videos(TIKTOK_USER)
        known_ids = [v["id"] for v in videos]
        save_known_videos(known_ids)
        print(f"Trovati {len(known_ids)} video esistenti. In attesa di nuovi...")

    while True:
        print(f"[{datetime.now()}] Controllo nuovi video...")
        videos = await get_latest_videos(TIKTOK_USER)

        new_videos = [v for v in videos if v["id"] not in known_ids]

        if new_videos:
            for video in new_videos:
                print(f"[NUOVO] {video['desc']}")
                await send_notification(video)
                known_ids.append(video["id"])
            save_known_videos(known_ids)
        else:
            print("Nessun nuovo video.")

        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(monitor())