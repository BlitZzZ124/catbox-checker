import asyncio
import aiohttp
import random
import string
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = [
    ".mp4", ".png", ".jpg", ".jpeg", ".gif", ".webm", ".mp3",
    ".pdf", ".txt", ".zip", ".rar", ".7z", ".wav", ".bmp", ".svg"
]

# Media extensions for preview
IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"]
VIDEO_EXTENSIONS = [".mp4", ".webm"]
DISALLOWED_EXTENSIONS = [".exe", ".scr", ".cpl", ".jar", ".doc", ".docx"]

# Settings
CONCURRENCY = 20
TOTAL_ATTEMPTS = 0  # 0 = infinite
OUTPUT_FILE = "links.txt"
MAX_RETRIES = 3
WEBHOOK_URL = "YOUR_WEBHOOK_HERE"  # <- Replace this

def print_banner():
    banner = r"""
   ____      _   _                 
  / ___|__ _| |_| |__   ___  _ __  
 | |   / _` | __| '_ \ / _ \| '_ \ 
 | |__| (_| | |_| | | | (_) | | | |
  \____\__,_|\__|_| |_|\___/|_| |_|

        Catbox Link Checker
    """
    print(Fore.CYAN + banner)

def generate_random_filename():
    name = ''.join(random.choices(string.ascii_lowercase, k=6))
    ext = random.choice(ALLOWED_EXTENSIONS)
    return name + ext

async def send_webhook(session, url):
    if not WEBHOOK_URL or WEBHOOK_URL == "YOUR_DISCORD_WEBHOOK_HERE":
        return

    ext = url[-4:].lower()
    embed = {
        "title": "✅ Catbox Link Found",
        "description": f"[Click to view]({url})",
        "color": 0x00ff00
    }

    # Add preview for images/videos
    if ext in IMAGE_EXTENSIONS:
        embed["image"] = {"url": url}
    elif ext in VIDEO_EXTENSIONS:
        embed["video"] = {"url": url}

    payload = {"embeds": [embed]}

    try:
        async with session.post(WEBHOOK_URL, json=payload) as resp:
            if resp.status not in [200, 204]:
                print(f"{Fore.RED}[WEBHOOK ERROR] Status: {resp.status}")
    except Exception as e:
        print(f"{Fore.RED}[WEBHOOK ERROR] → {e}")

async def check_link(session, sem, url):
    async with sem:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Accept": "*/*",
        }

        for attempt in range(1, MAX_RETRIES + 1):
            print(f"{Fore.YELLOW}[CHECKING]{Style.RESET_ALL} {url} (Attempt {attempt})")
            try:
                async with session.get(url, headers=headers, timeout=10, allow_redirects=False) as resp:
                    if resp.status == 200:
                        print(f"{Fore.GREEN}[VALID]   {url}")
                        with open(OUTPUT_FILE, "a") as f:
                            f.write(url + "\n")
                        await send_webhook(session, url)
                        return
                    else:
                        print(f"{Fore.RED}[INVALID] {url} (status: {resp.status})")
                        return
            except Exception as e:
                print(f"{Fore.RED}[ERROR]   {url} → {e}")
                await asyncio.sleep(0.5 * attempt)

async def main():
    print_banner()
    sem = asyncio.Semaphore(CONCURRENCY)
    async with aiohttp.ClientSession() as session:
        attempt = 0
        while True:
            if TOTAL_ATTEMPTS and attempt >= TOTAL_ATTEMPTS:
                break
            attempt += 1
            filename = generate_random_filename()
            url = f"https://files.catbox.moe/{filename}"
            asyncio.create_task(check_link(session, sem, url))
            await asyncio.sleep(0.05)  # small delay to reduce 503s

if __name__ == "__main__":
    asyncio.run(main())
