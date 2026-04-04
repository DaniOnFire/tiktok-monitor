import asyncio
import json
import os
import requests
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

# Cookie presi da Chrome
SESSION_ID   = "41d66333816c3399037d05a73c832cf2"
MS_TOKEN     = "nk8hu-HTZLF2EK-wMeup4CoOMDR0dC2kECXKPmBqCq9ZQleT5G-FQUYNbEKq_ESqLYj8aQWLg69NacxmgkO1KEpQnhIEw-PVsoKoesTjvPuwFdt4wuotDHh7RgSjeaqDmA6MFBajM65g"
TT_WEBID     = "1%7C9Elw1GanP2L6lN2KghVEvlS6eAzb_Z7QknMavrsydk0%7C1775311193%7C53be0394e13ba3c7b2dc902c3dc71070a1d7aeb0a8d54841176ee36e0374917c"
# ──────────────────────────────────────────────────────────

bot = Bot(token=TELEGRAM_TOKEN)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.tiktok.com/",
    "Cookie": f"sessionid={SESSION_ID}; msToken={MS_TOKEN}; tt_webid_v2={TT_WEBID};"
}

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

def get_user_secuid(username):
    url = f"https://www.tiktok.com/api/user/detail/?uniqueId={username}&aid=1988&app_language=it&device_platform=web_pc"
    r = requests.get(url, headers=HEADERS, timeout=10)
    data = r.json()
    return data["userInfo"]["user"]["secUid"]

def get_latest_videos(sec_uid):
    videos = []
    try:
        url = f"https://www.tiktok.com/api/post/item_list/?secUid={sec_uid}&count=10&cursor=0&aid=1988&device_platform=web_pc"
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        for item in data.get("itemList", []):
            videos.append({
                "id":    item["id"],
                "url":   f"https://www.tiktok.com/@{TIKTOK_USER}/video/{item['id']}",
                "desc":  item.get("desc", "Nessuna descrizione"),
                "likes": item.get("stats", {}).get("diggCount", 0),
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
    
    print("Recupero secUid utente...")
    sec_uid = get_user_secuid(TIKTOK_USER)
    print(f"secUid trovato: {sec_uid[:20]}...")

    known_ids = load_known_videos()

    if not known_ids:
        print("Prima esecuzione: salvo i video esistenti...")
        videos = get_latest_videos(sec_uid)
        known_ids = [v["id"] for v in videos]
        save_known_videos(known_ids)
        print(f"Trovati {len(known_ids)} video esistenti. In attesa di nuovi...")

    while True:
        if is_orario_attivo():
            print(f"[{datetime.now()}] Controllo nuovi video...")
            videos = get_latest_videos(sec_uid)

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
