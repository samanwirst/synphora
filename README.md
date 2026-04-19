# Synphora

**Synphora** is an open-source Telegram-based app for **listening to music in sync with friends**.

You upload tracks to the bot, create a room, and share an invite link. The room creator controls playback (play, pause, seek, next/prev, speed), while listeners stay synchronized in real time.

## Project Status

This is a **fan open-source project**.

I build it **from time to time whenever I have the opportunity**, so the project is evolving gradually.

## Features

- Telegram bot onboarding (`/start`) with per-user profile initialization.
- Audio upload flow through Telegram messages (`F.audio`).
- Room creation from your uploaded track list (`/new_room`).
- Creator authentication with a one-time 6-digit PIN.
- Telegram Mini App auth verification via `init_data` signature.
- Real-time playback sync with Socket.IO.
- Role-based room behavior:
  - **creator**: full playback control
  - **listener**: receive synchronized state updates
- Built-in API proxy routes in Next.js for backend and audio streaming.

## How It Works

1. User sends `/start` to the bot.
2. Bot maps `telegram_user_id -> user_uuid` and creates a user in backend API.
3. User sends audio files to the bot.
4. Bot maps Telegram `file_id -> track_uuid`, saves track IDs to user audiolist.
5. User sends `/new_room`:
   - bot downloads tracks from Telegram,
   - uploads them to `audio_storage`,
   - calls `server /rooms/` to create a room.
6. Server returns `room_id` + one-time PIN.
7. Creator opens Mini App auth page and enters PIN.
8. Client calls `/rooms/{room_id}/auth-pin` with Telegram `init_data`.
9. Server verifies Telegram signature + PIN and returns `control_token`.
10. Room page connects to Socket.IO:
   - creator joins with token,
   - listeners join without token,
   - controls are broadcast as updated room state to everyone.

## Architecture

### 1) `bot/` (Aiogram)

Responsibilities:
- User onboarding and command handling.
- Receiving Telegram audio files.
- Downloading audio from Telegram and uploading to storage API.
- Creating rooms and issuing creator/listener links.

Local data:
- `user_id_storage.db`: Telegram user ID ↔ user UUID.
- `file_id_storage.db`: Telegram file ID ↔ track UUID.

### 2) `server/` (FastAPI)

Responsibilities:
- User API (`/users/*`) and audiolist management.
- Room API (`/rooms/*`): create room, PIN auth, socket role auth, control actions.
- Room playback state and synchronization logic.

Data model details:
- Users are stored in SQLite (`server/users.db`).
- Room state is held in **memory** (`RoomsStore`), including playlist and playback state.

### 3) `audio_storage/` (FastAPI)

Responsibilities:
- Upload audio files.
- Serve `.mp3` files.
- Delete stored files.

Storage location:
- `audio_storage/files/`

### 4) `client/synphora_app/` (Next.js + Socket.IO)

Responsibilities:
- Telegram Mini App UI.
- Creator PIN auth page.
- Room UI with synchronized HTML5 audio playback.
- Socket.IO server (`server.ts`) bridging client events to backend room APIs.
- Next API proxy routes:
  - `/api/server/*` -> backend API
  - `/api/audio/files/*` -> audio storage API

## Tech Stack

- **Bot:** Python, Aiogram 3
- **Backend APIs:** FastAPI
- **Realtime:** Socket.IO
- **Frontend:** Next.js (App Router), React, TypeScript, Telegram UI
- **Storage:** SQLite (user data + bot mappings), filesystem for audio files

## Repository Structure

- `bot/` - Telegram bot service
- `server/` - main backend API (users + rooms)
- `audio_storage/` - audio file storage API
- `client/synphora_app/` - Telegram Mini App + socket server

## Environment Variables

### `bot/.env`

```dotenv
BOT_TOKEN=
SERVER_API_URL=
AUDIO_STORAGE_API_URL=
CLIENT_APP_URL=
API_SECRET_BOT_KEY=
```

### `server/.env`

```dotenv
AUDIO_STORAGE_API_URL=
API_SECRET_BOT_KEY=
BOT_TOKEN=
```

### `audio_storage/.env`

```dotenv
API_SECRET_BOT_KEY=
```

### `client/synphora_app/.env.local`

```dotenv
NEXT_PUBLIC_SOCKET_SERVER_URL=
NEXT_PUBLIC_SERVER_API_URL=
NEXT_PUBLIC_AUDIO_STORAGE_API_URL=
SOCKET_PORT=3001
NEXT_PORT=3000
NEXT_HOSTNAME=127.0.0.1
SOCKET_CORS_ORIGIN=*
```

## Local Run

### Prerequisites

- Python 3.11+
- Node.js 20+
- pnpm
- Telegram bot token
- Public HTTPS domain for Telegram Mini App usage (required by Telegram in real usage)

### 1) Start backend API (`server`)

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2) Start audio storage API (`audio_storage`)

```bash
cd audio_storage
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 3) Start Mini App + Socket server (`client/synphora_app`)

```bash
cd client/synphora_app
pnpm install
pnpm dev
```

This runs both:
- Next.js app
- Socket.IO server (`server.ts`)

### 4) Start Telegram bot (`bot`)

```bash
cd bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Security Notes

- Protected backend endpoints require `X-API-KEY` (`API_SECRET_BOT_KEY`).
- Creator auth requires a one-time PIN.
- PIN protection includes:
  - TTL (24h)
  - max attempts
  - temporary lock on repeated failures
- Creator rights are granted through `control_token`; listeners cannot send control actions.

## Current Limitations

- Room state is in-memory: restart of `server` resets active rooms.
- No distributed room state yet (single-node design).
- Audio files are stored as uploaded and served as `.mp3` names; no transcoding pipeline yet.
- Automated tests are not included yet.

## License

Apache License 2.0. See [LICENSE](./LICENSE).
