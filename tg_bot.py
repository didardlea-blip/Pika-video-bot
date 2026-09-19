import os
from threading import Thread
import telebot
from flask import Flask

# Инициализация Flask для Web Service на Render
app = Flask(__name__)


@app.route("/")
def home():
  return "Pika Telegram Bot is running!"


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# Получаем токен из переменных окружения Render
TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def send_welcome(bot_message):
  bot.reply_to(
      bot_message,
      "Привет! Я бот для генерации контента. Отправь мне текстовый промпт.",
  )


@bot.message_handler(func=lambda message: True)
def handle_message(message):
  bot.reply_to(
      message,
      f"Получил ваш промпт: '{message.text}'. Скоро здесь будет интеграция с"
      " Playwright и Pika!",
  )


if __name__ == "__main__":
  # Запускаем Flask-сервер в отдельном потоке
  t = Thread(target=run_flask)
  t.start()

  # Запускаем Telegram-бота
  print("Бот запущен...")
  bot.infinity_polling()
