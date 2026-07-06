# yt-minimal

> A YouTube client that respects your attention.

No Shorts. No thumbnails. No algorithmic rabbit holes. Just your subscriptions, filtered to real videos.

---

## Motivation

YouTube's default feed is an engagement-maximization machine. Shorts pollute subscription feeds, thumbnails trigger compulsive clicking, and autoplay erodes intent. `yt-minimal` strips all of that — returning a clean, chronological list of videos from channels you actually chose to follow.

## Features

- ✅ **Shorts filtered out** — duration < 3 min and `#shorts` titles removed server-side
- ✅ **No thumbnails** — list-only UI, zero visual bait
- ✅ **Distraction-free playback** — taps through to YouTube via in-app browser (expo-web-browser); no autoplay, no recommended-video rabbit hole
- ✅ **OAuth 2.0** — authenticates with your real YouTube account via Google
- ✅ **Rate limiting** — per-user and per-IP guards on all endpoints
- ✅ **Security headers** — CSP, X-Frame-Options, HSTS middleware

## Architecture

```
┌─────────────────────┐        ┌──────────────────────────┐
│   React Native      │  HTTP  │   FastAPI Backend         │
│   (Expo)            │◄──────►│                           │
│                     │        │  /auth  — OAuth 2.0 flow  │
│   TypeScript        │        │  /feed  — filtered subs   │
└─────────────────────┘        └──────────────┬───────────┘
                                              │
                                              ▼
                                   YouTube Data API v3
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python · FastAPI · slowapi · httpx |
| Mobile | React Native · Expo · TypeScript |
| Auth | OAuth 2.0 (Google / YouTube) |
| Security | Custom middleware · CORS · rate limiting |

## Getting Started

### Backend

```bash
cd backend
cp .env.example .env   # fill in your Google OAuth credentials
pip install -r requirements.txt
uvicorn main:app --reload
```

### Mobile

```bash
cd mobile
npm install
npx expo start
```

Requires a `.env` in `mobile/` pointing to your local or deployed backend URL.

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/auth/login` | Initiate OAuth flow |
| `GET` | `/auth/callback` | OAuth callback handler |
| `GET` | `/feed/` | Filtered subscription feed |
| `POST` | `/auth/refresh` | Renew session JWT (Bearer token required) |

## Roadmap

- [ ] Audio-only playback in mobile client
- [ ] Offline queue / download
- [ ] Self-hostable Docker deployment
- [ ] Playlist support (filtered)

---

**Built by [Andrey Costa](https://andreycosta.com)**
