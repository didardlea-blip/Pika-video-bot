  async def create_video(
      self, session: aiohttp.ClientSession, token: str, prompt: str, proxy: str
  ) -> str:
    try:
      gen_url = "https://create-api.pika.art/v1/generate"
      headers = {
          "authorization": f"Bearer {token}",
          "content-type": "application/json",
          "origin": "https://create.pika.art",
          "user-agent": (
              "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
              " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
          ),
      }
      payload = {
          "promptText": prompt,
          "options": {"aspectRatio": "16:9", "frameRate": 24},
      }

      async with session.post(
          gen_url, headers=headers, json=payload, proxy=proxy, timeout=15
      ) as resp:
        resp_text = await resp.text()
        print(f"[Pika API Response {resp.status}]: {resp_text}")  # <--- Выведет точную причину в лог Render
        if resp.status in (200, 201):
          data = await resp.json()
          return data.get("id") or data.get("job_id")
    except Exception as e:
      print(f"[Create Video Error Exception]: {e}")
    return None
