FROM mcr.microsoft.com/playwright:v1.49.0-jammy

WORKDIR /app

COPY requirements.txt .

# Используем python3 -m pip вместо чистой команды pip
RUN python3 -m pip install --no-cache-dir -r requirements.txt
RUN python3 -m playwright install chromium

COPY . .

# Указываем явный запуск через python3
CMD ["python3", "bot.py"]
