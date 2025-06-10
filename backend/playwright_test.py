import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.google.com")
        await asyncio.sleep(5)  # Keep the browser open for 5 seconds
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())