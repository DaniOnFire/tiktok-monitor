import asyncio
import json
import os
import requests
from datetime import datetime
from telegram import Bot
import xml.etree.ElementTree as ET

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
        url = f"https://rsshub.app/tiktok/user/@alessiadeda0"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=15)
        
        # Pulizia del testo prima del parsing
        testo = r.text
        testo = testo.encode('utf-8', errors='replace').decode('utf-8')
        
        root = ET.fromstring(testo)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        # Prova prima con items standard RSS
        items = root.findall('.//item')
        # Se non trova nulla prova con entry Atom
        if not items:
            items = root.findall('.//atom:entry', ns)

        for item in items[:10]:
            title = item.findtext('title') or item.findtext('atom:title', namespaces=ns) or "Nessuna descrizione"
            link  = item.findtext('link') or item.findtext('atom:link', namespaces=ns) or ""
            guid  = item.findtext('guid') or item.findtext('atom:id', namespaces=ns) or link
            video_id = guid.strip().split("/")[-1]
            videos.append({
                "id":   video_id,
                "url":  link.strip(),
                "desc": title.strip(),
                "likes": 0,
            })
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
