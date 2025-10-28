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
    "Mozilla/5.0 (Linux; Android 13; J9110) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6943.39 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; 802SO) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6803.81 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SO-51B Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.92 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Xperia 1 V Build/TP1A.220624.009) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6097.97 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; XQ-CT54 Build/UKQ1.230819.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6160.58 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; 802SO Build/RP1A.200720.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SO-51C Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6450.47 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SOG03 Build/SP1A.210812.020) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.96 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; J9110 Build/TQ1A.230105.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6943.39 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SO-62B Build/UKQ1.231108.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.43 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; A204SH Build/UKQ1.231108.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.43 Mobile Safari/537.36 YJApp-ANDROID jp.co.yahoo.android.yjtop/3.204.0",
    "Mozilla/5.0 (Linux; Android 15; SH-52D Build/SC36B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.207 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SH-53C Build/S7040) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.93 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SH-54D Build/SB069) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.93 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SH-RM15 Build/SA045) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/140.0.7339.207 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SH-53C Build/S7040; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; AQUOS sense7 Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6450.47 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SHV47 Build/SP1A.210812.015) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.96 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; AQUOS R8 Build/SC36B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.207 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SH-51B Build/V72RD50C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.39 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; A101FC Build/V82RS43B; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.207 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; F-51B Build/V72RD50C; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.39 Mobile Safari/537.36 Instagram/359.0.0.59.89",
    "Mozilla/5.0 (Linux; Android 11; F-02L Build/V71R045A; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.207 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/527.0.0.47.108]",
    "Mozilla/5.0 (Linux; Android 12; FCG01 Build/V44RK67A; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.207 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; 801FJ Build/V48R056B; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.207 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; FCNT FCG01 Build/V82RK43B; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.107 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; Arrows U Build/SP1A.210812.016) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; F-41B Build/V45R058B; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.7258.94 Mobile Safari/537.36 JP/ja_JP",
    "Mozilla/5.0 (Linux; Android 11; F-51A Build/V45R047A; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.119 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; FCG01 Build/V82RS43B; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.7258.94 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; U; Android 4.2.2; ja-jp; F-02F Build/V21R66B) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30",
    "Mozilla/5.0 (Linux; U; Android 4.2.2; ja-jp; F-03F Build/V18R40A) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30",
    "Mozilla/5.0 (Linux; Android 13; SH-53C Build/S7040; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.43 Mobile Safari/537.36 FUJITSU/DOCOMO",
    "Mozilla/5.0 (Linux; U; Android 4.1.2; ja-jp; SH-02E Build/S9290) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30",
    "Mozilla/5.0 (Linux; Android 11; F-02L Build/V71R045A; wv) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.207 Mobile Safari/537.36 FUJITSU/DOCOMO",
    "Mozilla/5.0 (Linux; Android 9; 802SO Build/PQ3A.190801.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.86 Mobile Safari/537.36 SOV-### DOCOMO",
    "Mozilla/5.0 (Linux; Android 12; SHV47 Build/SP1A.210812.015) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.96 Mobile Safari/537.36 DOCOMO/SHV47",
    "Mozilla/5.0 (Linux; Android 13; F-51B Build/V72RD50C) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.39 Mobile Safari/537.36 FUJITSU/DOCOMO",
    "Mozilla/5.0 (Linux; Android 14; RMX3700 Build/UKQ1.230919.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.93 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Realme GT5 Build/TQ3A.230805.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6450.47 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; RMX3850 Build/UP1A.231005.007) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.207 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Realme 11 Pro+ Build/TQ3A.230805.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.6985.80 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B Build/UKQ1.240121.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.93 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S926N Build/UP1A.240105.003) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.207 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-F946U Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6450.47 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/138.1 Mobile/15E148 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) GSA/271.3.546369769 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/141.0.7390.58 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Apple Silicon Mac OS X 15_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15"
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
