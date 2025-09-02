FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Устанавливаем tree для красивого вывода
RUN apt-get update && apt-get install -y --no-install-recommends tree && rm -rf /var/lib/apt/lists/*

# Копируем только необходимые файлы
COPY . .

# Проверяем структуру файлов
RUN tree -h

EXPOSE 8080

CMD ["python", "bot.py"]