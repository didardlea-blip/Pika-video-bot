import os
import asyncio
from playwright.async_api import async_playwright
import telebot

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Бот с Playwright работает на Render!")

# Пример функции автоматизации с оптимизацией памяти
async def run_browser_task():
    async with async_playwright() as p:
        # Важные флаги, чтобы Chromium не вылетал по недостатку RAM
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--single-process'
            ]
        )
        page = await browser.new_page()
        await page.goto("https://example.com")
        title = await page.title()
        await browser.close()
        return title

if __name__ == '__main__':
    bot.infinity_polling()
