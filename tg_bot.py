import asyncio
import base64
import hashlib
import os
import random
import re
import string
from threading import Thread
import aiohttp
from flask import Flask
from telebot.async_telebot import AsyncTeleBot

# Инициализация Flask для Render Web Service
app = Flask(__name__)


@app.route("/")
def home():
  return "Pika API Telegram Bot with Proxy Rotation is running!"


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# Читаем токен из переменных окружения Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = AsyncTeleBot(BOT_TOKEN)

# Список бесплатных прокси для ротации (будут перебираться по очереди или случайно)
PROXY_LIST = [
    # Можете добавлять сюда свои рабочие прокси в формате "http://ip:port" или "socks5://ip:port"
    None,  # Первый запрос попробуем сделать без прокси
    "http://185.162.229.45:80",
    "http://190.61.88.147:8080",
    "http://200.105.215.22:3128",
    "http://43.153.88.125:80",
]


class TempMailAPI:
  """Временная почта Mail.tm"""

  BASE_URL = "https://api.mail.tm"

  def __init__(self, session: aiohttp.ClientSession, proxy: str = None):
    self.session = session
    self.proxy = proxy

  async def create_account(self):
    try:
      async with self.session.get(
          f"{self.BASE_URL}/domains", proxy=self.proxy, timeout=10
      ) as resp:
        if resp.status != 200:
          return None, None, None
        data = await resp.json()
        domain = data["hydra:member"][0]["domain"]

      rand_str = "".join(
          random.choices(string.ascii_lowercase + string.digits, k=8)
      )
      email = f"pika_user_{rand_str}@{domain}"
      password = f"P@ssword_{rand_str}"

      payload = {"address": email, "password": password}
      async with self.session.post(
          f"{self.BASE_URL}/accounts",
          json=payload,
          proxy=self.proxy,
          timeout=10,
      ) as resp:
        if resp.status not in (200, 201):
          return None, None, None

      async with self.session.post(
          f"{self.BASE_URL}/token", json=payload, proxy=self.proxy, timeout=10
      ) as resp:
        if resp.status != 200:
          return None, None, None
        token_data = await resp.json()
        return email, password, token_data.get("token")
    except Exception as e:
      print(f"[Mail Error with proxy {self.proxy}] {e}")
      return None, None, None

  async def get_confirmation_link(
      self, mail_token: str, timeout: int = 45
  ) -> str:
    headers = {"Authorization": f"Bearer {mail_token}"}
    start_time = asyncio.get_event_loop().time()

    while asyncio.get_event_loop().time() - start_time < timeout:
      try:
        async with self.session.get(
            f"{self.BASE_URL}/messages",
            headers=headers,
            proxy=self.proxy,
            timeout=10,
        ) as resp:
          if resp.status == 200:
            data = await resp.json()
            messages = data.get("hydra:member", [])
            if messages:
              msg_id = messages[0]["id"]
              async with self.session.get(
                  f"{self.BASE_URL}/messages/{msg_id}",
                  headers=headers,
                  proxy=self.proxy,
                  timeout=10,
              ) as m_resp:
                detail = await m_resp.json()
                body = detail.get("text") or detail.get("html") or ""
                match = re.search(
                    r'https?://[^\s<>"]+(?:confirm|verify)[^\s<>"]*', body
                )
                if match:
                  return match.group(0)
      except Exception as e:
        print(f"[Mail Polling Error] {e}")
      await asyncio.sleep(3)
    return None


class PikaEngine:
  """Движок регистрации и генерации Pika.art с ротацией прокси"""

  def __init__(self):
    self.supabase_host = "xrcfahrzkjpblmrsaknx.supabase.co"
    self.api_key = "sb_publishable_HTxwdzVcJvk01MQMOCQCmg_KULx5ESC"

  @staticmethod
  def generate_pkce():
    code_verifier = (
        base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8").rstrip("=")
    )
    code_challenge = (
        base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode("utf-8")).digest()
        )
        .decode("utf-8")
        .rstrip("=")
    )
    return code_verifier, code_challenge

  async def update_config(self, session: aiohttp.ClientSession, proxy: str):
    try:
      async with session.get(
          "https://create.pika.art", proxy=proxy, timeout=10
      ) as resp:
        html = await resp.text()
      js_links = re.findall(r'src="(/_next/static/[^"]+\.js)"', html)
      for link in js_links:
        async with session.get(
            f"https://create.pika.art{link}", proxy=proxy, timeout=10
        ) as js_resp:
          js_text = await js_resp.text()
          host_match = re.search(r"([a-z0-9]+\.supabase\.co)", js_text)
          key_match = re.search(r"(sb_publishable_[A-Za-z0-9_]+)", js_text)
          if host_match and key_match:
            self.supabase_host = host_match.group(1)
            self.api_key = key_match.group(1)
            break
    except Exception as e:
      print(f"[Config Update Warning] {e}")

  async def register_with_proxy_rotation(
      self, session: aiohttp.ClientSession
  ):
    """Пробует зарегистрироваться, перебирая прокси из списка при неудаче"""
    shuffled_proxies = list(PROXY_LIST)
    random.shuffle(shuffled_proxies)

    for proxy in shuffled_proxies:
      print(f"[*] Попытка регистрации через прокси: {proxy}")
      try:
        await self.update_config(session, proxy)
        mail_api = TempMailAPI(session, proxy=proxy)
        email, password, mail_token = await mail_api.create_account()
        if not email:
          continue

        _, code_challenge = self.generate_pkce()
        signup_url = f"https://{self.supabase_host}/auth/v1/signup?redirect_to=https%3A%2F%2Fcreate.pika.art%2Fauth%2Fconfirm%3Fto%3D%252Fapps"
        headers = {
            "authority": self.supabase_host,
            "apikey": self.api_key,
            "authorization": f"Bearer {self.api_key}",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://create.pika.art",
            "referer": "https://create.pika.art/",
        }
        payload = {
            "email": email,
            "password": password,
            "code_challenge": code_challenge,
            "code_challenge_method": "s256",
        }

        async with session.post(
            signup_url, headers=headers, json=payload, proxy=proxy, timeout=10
        ) as resp:
          if resp.status not in (200, 201):
            continue

        confirm_link = await mail_api.get_confirmation_link(mail_token)
        if not confirm_link:
          continue

        async with session.get(
            confirm_link, proxy=proxy, allow_redirects=True, timeout=10
        ) as confirm_resp:
          if confirm_resp.status == 200:
            return email, password, proxy
      except Exception as e:
        print(f"[!] Ошибка с прокси {proxy}: {e}")
        continue
    return None, None, None

  async def login(
      self, session: aiohttp.ClientSession, email: str, password: str, proxy: str
  ) -> str:
    url = f"https://{self.supabase_host}/auth/v1/token?grant_type=password"
    headers = {"apikey": self.api_key, "content-type": "application/json"}
    payload = {"email": email, "password": password}

    async with session.post(
        url, headers=headers, json=payload, proxy=proxy, timeout=10
    ) as resp:
      if resp.status == 200:
        data = await resp.json()
        return data.get("access_token")
    return None

  async def create_video(
      self, session: aiohttp.ClientSession, token: str, prompt: str, proxy: str
  ) -> str:
    gen_url = "https://create-api.pika.art/v1/generate"
    headers = {
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "origin": "https://create.pika.art",
    }
    payload = {
        "promptText": prompt,
        "options": {"aspectRatio": "16:9", "frameRate": 24},
    }

    async with session.post(
        gen_url, headers=headers, json=payload, proxy=proxy, timeout=15
    ) as resp:
      if resp.status in (200, 201):
        data = await resp.json()
        return data.get("id") or data.get("job_id")
    return None

  async def poll_video(
      self, session: aiohttp.ClientSession, token: str, job_id: str, proxy: str
  ) -> str:
    status_url = f"https://create-api.pika.art/v1/jobs/{job_id}"
    headers = {"authorization": f"Bearer {token}"}

    for _ in range(35):
      await asyncio.sleep(8)
      try:
        async with session.get(
            status_url, headers=headers, proxy=proxy, timeout=10
        ) as resp:
          if resp.status == 200:
            data = await resp.json()
            status = data.get("status")
            if status == "finished" or "videoUrl" in data:
              return data.get("videoUrl") or data.get("resultUrl")
            elif status == "failed":
              return None
      except Exception:
        continue
    return None


engine = PikaEngine()


@bot.message_handler(commands=["start"])
async def send_welcome(message):
  await bot.reply_to(
      message,
      "👋 Привет! Бот настроен с **авторотацией прокси**.\n\nНапиши мне промпт"
      " на английском языке, и я зарегистрирую аккаунт через рабочий прокси и"
      " сгенерирую видео!\n\nПример: `A futuristic cyberpunk city, neon"
      " lights, 8k`",
      parse_mode="Markdown",
  )


@bot.message_handler(func=lambda message: True)
async def process_prompt(message):
  prompt = message.text
  status_msg = await bot.reply_to(
      message, "⏳ [1/4] Ищем рабочий прокси и создаем аккаунт..."
  )

  async with aiohttp.ClientSession() as session:
    email, password, used_proxy = await engine.register_with_proxy_rotation(
        session
    )
    if not email:
      await bot.edit_message_text(
          "❌ Все прокси заблокированы или недоступны. Попробуйте позже.",
          message.chat.id,
          status_msg.message_id,
      )
      return

    await bot.edit_message_text(
        "🔐 [2/4] Авторизация в системе Pika...",
        message.chat.id,
        status_msg.message_id,
    )

    token = await engine.login(session, email, password, used_proxy)
    if not token:
      await bot.edit_message_text(
          "❌ Ошибка входа в сгенерированный аккаунт.",
          message.chat.id,
          status_msg.message_id,
      )
      return

    job_id = await engine.create_video(session, token, prompt, used_proxy)
    if not job_id:
      await bot.edit_message_text(
          "❌ Не удалось отправить промпт на генерацию.",
          message.chat.id,
          status_msg.message_id,
      )
      return

    await bot.edit_message_text(
        "🎬 [3/4] Видео создается (около 1-2 минут)...",
        message.chat.id,
        status_msg.message_id,
    )

    video_url = await engine.poll_video(session, token, job_id, used_proxy)
    if not video_url:
      await bot.edit_message_text(
          "❌ Ошибка во время рендеринга видео.",
          message.chat.id,
          status_msg.message_id,
      )
      return

    await bot.edit_message_text(
        "📥 [4/4] Отправка готового видео...",
        message.chat.id,
        status_msg.message_id,
    )

    try:
      await bot.send_video(
          message.chat.id,
          video_url,
          caption=f"✨ **Промпт:** {prompt}",
          parse_mode="Markdown",
      )
      await bot.delete_message(message.chat.id, status_msg.message_id)
    except Exception:
      await bot.edit_message_text(
          f"🎉 **Видео успешно готово!**\n\nСсылка на скачивание:\n{video_url}",
          message.chat.id,
          status_msg.message_id,
      )


if __name__ == "__main__":
  # Запускаем веб-сервер Flask для Render
  web_thread = Thread(target=run_web)
  web_thread.daemon = True
  web_thread.start()

  print("🤖 Бот с ротацией прокси запущен...")
  # Используем стандартный polling с таймаутом, чтобы избегать ошибки 409 Conflict
  asyncio.run(bot.infinity_polling(timeout=20))

