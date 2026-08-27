# IELTS Speaking Practice Bot

Production-oriented Telegram bot for IELTS Speaking Part 1 practice.

## Stack

- Python 3.12+
- aiogram 3
- MongoDB + Motor (Atlas or self-hosted)
- Anthropic Claude for question generation and evaluation
- OpenAI Speech-to-Text for voice transcription
- APScheduler for daily reminders
- systemd for server deployment
- Pydantic Settings

## Why OpenAI STT?

Telegram's native voice transcription is an MTProto feature. The documented `messages.transcribeAudio` method is available to user accounts, not bots, so a normal Bot API bot cannot simply request Telegram's generated transcript. This project therefore downloads the Telegram voice message and sends it to the STT provider.

## Features

- `/start` — onboarding, timezone/reminder setup and menu
- `/topic` — generates a fresh IELTS Speaking Part 1 question
- Voice answer — transcribed and evaluated
- Short, friendly IELTS feedback
- `/stat` — days practicing, topics, attempts, average/best score
- Daily reminders
- `/help`
- MongoDB persistence
- Graceful error handling
- Healthcheck endpoint on port 8080

## Server deployment (systemd)

### 1. Prerequisites on the server

- Ubuntu/Debian (or any Linux with systemd)
- Python 3.12+ (`python3`, `python3-venv`)
- MongoDB (Atlas URI in `.env`, or local MongoDB)
- Outbound HTTPS to Telegram, Anthropic, and OpenAI APIs

### 2. Clone and install

```bash
git clone <your-repo-url> ielts-speaking-part1-bot
cd ielts-speaking-part1-bot
sudo bash deploy/install.sh
```

The script will:

- create system user `ielts-bot`
- install the app to `/opt/ielts-speaking-bot`
- create a Python virtualenv and install dependencies
- register and enable `ielts-speaking-bot.service`

### 3. Configure environment

```bash
sudo nano /opt/ielts-speaking-bot/.env
```

See `.env.example` for all variables.

### 4. Start and manage the service

```bash
sudo systemctl start ielts-speaking-bot
sudo systemctl status ielts-speaking-bot
sudo journalctl -u ielts-speaking-bot -f
```

Useful commands:

```bash
sudo systemctl restart ielts-speaking-bot   # after code or .env changes
sudo systemctl stop ielts-speaking-bot
curl http://127.0.0.1:8080/health            # should return {"status":"ok"}
```

### 5. Update after git pull

```bash
cd ielts-speaking-part1-bot
git pull
sudo bash deploy/install.sh
sudo systemctl restart ielts-speaking-bot
```

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in .env
python -m app.main
```

## Environment

See `.env.example`.

Required:

- `BOT_TOKEN`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `MONGODB_URI`

## Important privacy note

The bot stores Telegram user ID, username/name when available, question, transcript, score and feedback. Audio itself is not permanently stored by this application; the Telegram `file_id` is stored so the original message can be referenced. The STT provider receives the downloaded voice file for transcription.

If you publish this bot, add a real privacy policy and obtain the user's consent before processing voice recordings.
