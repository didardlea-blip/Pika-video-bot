import os
from threading import Thread
import telebot
from flask import Flask
from playwright.sync_api import sync_playwright

# Инициализация Flask для Render Web Service
app = Flask(__name__)


@app.route("/")
def home():
  return "Pika Telegram Bot with Playwright is running!"


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# Читаем токен из переменных окружения Render
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)


def generate_video_with_pika(prompt_text):
  """Функция для автоматизации Pika.art через Playwright"""
  with sync_playwright() as p:
    # Запускаем браузер в headless-режиме с настройками для обхода детект-систем
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ],
    )
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
            " like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    )
    page = context.new_page()

    try:
      print(
          "Открываем Pika.art..."
      )  # Здесь будет логика логина/авторизации и ввода промпта
      page.goto("https://pika.art/", timeout=60000)

      # Временная заглушка, имитирующая процесс генерации
      page.wait_for_timeout(5000)

      browser.close()
      return (
          f"Видео по промпту '{prompt_text}' успешно сгенерировано! (Заглушка"
          " Playwright)"
      )
    except Exception as e:
      browser.close()
      return f"Ошибка при работе с Playwright: {str(e)}"


@bot.message_handler(commands=["start"])
def send_welcome(message):
  bot.reply_to(
      message,
      "Привет! Я бот для генерации видео через Pika.art. Отправь мне текстовый"
      " промпт.",
  )


@bot.message_handler(func=lambda message: True)
def handle_prompt(message):
  user_prompt = message.text
  sent_msg = bot.reply_to(
      message,
      "⏳ Генерирую видео через Pika.art (запуск браузера Playwright)...",
  )

  # Запускаем генерацию (в будущем можно вынести в отдельный поток, чтобы не блокировать бота)
  result_text = generate_video_with_pika(user_prompt)

  bot.edit_message_text(
      result_text, chat_id=message.chat.id, message_id=sent_msg.message_id
  )


if __name__ == "__main__":
  # Запускаем веб-сервер в фоновом потоке
  web_thread = Thread(target=run_web)
  web_thread.daemon = True
  web_thread.start()

  # Запускаем телеграм-бота
  print("Бот с поддержкой Playwright запущен...")
  bot.infinity_polling(none_stop=True)
