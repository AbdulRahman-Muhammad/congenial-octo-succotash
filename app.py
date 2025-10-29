import asyncio
from playwright.async_api import async_playwright
import random
import os
import hashlib
import time
from urllib.parse import urlparse, urljoin
from stem import Signal
from stem.control import Controller

URL_TO_VISIT = os.environ.get("TARGET_URL", "https://colle-pedia.blogspot.com/")
RUNNER_ID = os.environ.get("RUNNER_ID", "1")
TOR_SOCKS5 = os.environ.get("PROXY_URL", "socks5://127.0.0.1:9051")
CONTROL_PORT = int(os.environ.get("CONTROL_PORT", "9151"))

USER_AGENTS = [
    # Samsung
    "Mozilla/5.0 (Linux; Android 14; SM-S928B Build/UKQ1.240121.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.93 Mobile Safari/537.36",
    
    # Sony
    "Mozilla/5.0 (Linux; Android 14; Xperia 1 V Build/TP1A.220624.009) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.207 Mobile Safari/537.36",
    
    # Realme
    "Mozilla/5.0 (Linux; Android 14; RMX3850 Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.207 Mobile Safari/537.36",
    
    # Xiaomi
    "Mozilla/5.0 (Linux; Android 14; 22127RK46C Build/UKQ1.230919.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.93 Mobile Safari/537.36",
    
    # Sharp
    "Mozilla/5.0 (Linux; Android 14; AQUOS R8 Build/SC36B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.207 Mobile Safari/537.36",
    
    # Fujitsu
    "Mozilla/5.0 (Linux; Android 13; F-51B Build/V72RD50C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.39 Mobile Safari/537.36",
    
    # iPhone (iOS)
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/605.1.15",
    
    # Windows 11
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/141.0.7390.58 Safari/537.36",
    
    # macOS 15 (Apple Silicon)
    "Mozilla/5.0 (Macintosh; Apple Silicon Mac OS X 15_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
    
    # Linux Desktop (Ubuntu)
    "Mozilla/5.0 (X11; Linux x86_64; Ubuntu 24.04) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.93 Safari/537.36"
]

def get_ua():
    seed = hashlib.sha256(f"{time.time_ns()}-{os.urandom(16)}".encode()).hexdigest()
    random.seed(int(seed, 16))
    random.shuffle(USER_AGENTS)
    ua = random.choice(USER_AGENTS)
    return ua

async def signal_newnym():
    try:
        with Controller.from_port(port=CONTROL_PORT) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            print(f"[Runner {RUNNER_ID}] Tor NEWNYM signal sent successfully.")
        await asyncio.sleep(5)
    except Exception as e:
        print(f"[Runner {RUNNER_ID}] Tor NEWNYM error: {e}")

async def visit_with_browser():
    base_netloc = urlparse(URL_TO_VISIT).netloc
    proxy_config = {"server": TOR_SOCKS5}

    async with async_playwright() as p:
        browser = None
        try:
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy_config,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            context = await browser.new_context(
                user_agent=get_ua()
            )
            page = await context.new_page()

            print(f"[Runner {RUNNER_ID}] Visiting main page: {URL_TO_VISIT}")
            await page.goto(URL_TO_VISIT, wait_until="domcontentloaded", timeout=60000)

            await page.wait_for_selector('a[href*=".html"]', timeout=20000)
            link_locators = page.locator('a[href*=".html"]')
            all_links = await link_locators.all()
            internal_links = [
                urljoin(URL_TO_VISIT, await link.get_attribute('href'))
                for link in all_links
                if await link.get_attribute('href') and urlparse(urljoin(URL_TO_VISIT, await link.get_attribute('href'))).netloc == base_netloc
            ]

            if not internal_links:
                print(f"[Runner {RUNNER_ID}] No valid internal links, closing browser.")
                await browser.close()
                return

            pages_to_visit = random.sample(internal_links, min(3, len(internal_links)))
            for link in pages_to_visit:
                print(f"[Runner {RUNNER_ID}] Visiting: {link}")
                await page.goto(link, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(random.uniform(1,3))

            print(f"[Runner {RUNNER_ID}] Done visiting 3 pages. Closing browser to change IP...")
            await browser.close()
        except Exception as e:
            print(f"[Runner {RUNNER_ID}] Error: {e}")
            if browser:
                await browser.close()

async def main():
    while True:
        await visit_with_browser()

if __name__ == "__main__":
    asyncio.run(main())
