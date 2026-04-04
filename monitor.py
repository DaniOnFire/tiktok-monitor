import asyncio
import json
import os
import feedparser
from datetime import datetime
from telegram import Bot

# ─── CONFIGURAZIONE ───────────────────────────────────────
TELEGRAM_TOKEN = "8786183518:AAENcmBXOrBUuwCgNILJKadT92BdeF7y1qA"
CHAT_ID        = "291979788"
TIKTOK_USER    = "alessiadeda0"
CHECK_INTERVAL = 300
DATA_FILE      = "last_videos.json"
ORA_INIZIO     = 8.5
ORA_FINE       = 24.0
# ──────────────────────────────────────────────────────────

bot = Bot(token=TELEGRAM_TOKEN)

def is_orario_attivo():
    ora = datetime.now()
    ora_decimale = ora.hour + ora.minute / 60
    return ORA_INIZIO <= ora_decimale < ORA_FINE

def load_known_videos():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_known_videos(video_ids):
    with open(DATA_FILE, "w") as f:
        json.dump(video_ids, f)

def get_latest_videos():
    videos = []
    try:
        url = f"https://rsshub.app/tiktok/user/@{TIKTOK_USER}"
        # Impostiamo headers come se fosse un browser vero
        feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        feed = feedparser.parse(url)

        if feed.entries:
            for entry in feed.entries[:10]:
                title    = entry.get("title", "Nessuna descrizione")
                link     = entry.get("link", "")
                video_id = entry.get("id", link).strip().split("/")[-1]
                videos.append({
                    "id":    video_id,
                    "url":   link,
                    "desc":  title,
                    "likes": 0,
                })
            print(f"[OK] Trovati {len(videos)} video nel feed")
        else:
            print(f"[WARN] Feed vuoto o bloccato")
    except Exception as e:
        print(f"[ERRORE] Recupero video: {e}")
    return videos

async def send_notification(video):
    msg = (
        f"🎵 *Nuovo video su TikTok!*\n\n"
        f"👤 @alessiadeda0\n"
        f"📝 {video['desc']}\n\n"
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
        videos = get_latest_videos()
        if not videos:
            print("[WARN] Nessun video trovato alla prima esecuzione, riprovo tra 30s...")
            await asyncio.sleep(30)
            videos = get_latest_videos()
        known_ids = [v["id"] for v in videos]
        save_known_videos(known_ids)
        print(f"Trovati {len(known_ids)} video esistenti. In attesa di nuovi...")

    while True:
        if is_orario_attivo():
            print(f"[{datetime.now()}] Controllo nuovi video...")
            videos = get_latest_videos()
            new_videos = [v for v in videos if v["id"] not in known_ids]
            if new_videos:
                for video in new_videos:
                    print(f"[NUOVO] {video['desc']}")
                    await send_notification(video)
                    known_ids.append(video["id"])
                save_known_videos(known_ids)
            else:
                print("Nessun nuovo video.")
        else:
            print(f"[{datetime.now()}] Fuori orario, in pausa...")

        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(monitor())
