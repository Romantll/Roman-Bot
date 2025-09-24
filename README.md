A multipurpose **Discord bot** built with `discord.py`, featuring K-pop comeback reminders, random idol images, Reddit image fetching, and more!

---

## 📌 Features

- `/hello` – Test greeting command.
- `/ping` – Simple ping-pong latency test.
- `/comebacks` – Shows upcoming K-pop comeback events.
- `/addreminder` – Sets reminders for selected comebacks (1hr, 30min, and exact time).
- `/idolpic` – Shows a random image of a selected idol.
- `/addidolpic` – Adds new image URLs for a specific idol (restricted to allowed users).
- `/randompic` – Fetches a random image from a subreddit.

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/your-username/Roman-Bot.git
cd Roman-Bot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the root directory and include the following keys:

```env
DISCORD_TOKEN=your_discord_token_here
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_custom_user_agent
```

> 🔐 Your `DISCORD_TOKEN` and Reddit credentials must remain secret. Do not share or commit `.env`.

### 4. Google Sheets Integration (Comeback Tracking)

- Create a **Google Service Account** in Google Cloud Console.
- Share your Google Sheet (e.g., "Kpop Comebacks") with the **service account email**.
- Download the service account JSON key and rename it to:
  ```
  kpop-comebacks-credentials.json
  ```
- Place it in the root folder.

The sheet should contain at least the following columns:

| Group | Title | Date       | Time   |
|-------|-------|------------|--------|
| XYZ   | Debut | 2025-10-01 | 6:00PM KST |

---

## 🧠 Commands Overview

| Command         | Description                                               |
|----------------|-----------------------------------------------------------|
| `/hello`        | Replies with "Hello, @user!"                             |
| `/ping`         | Replies with "pong!" for latency testing                 |
| `/comebacks`    | Lists upcoming K-pop comeback events                     |
| `/addreminder`  | Sets a multi-timed reminder for a group comeback         |
| `/idolpic`      | Sends a random idol image from stored JSON               |
| `/addidolpic`   | Adds an idol image URL to the JSON list (admin-only)     |
| `/randompic`    | Sends a random image post from a given subreddit         |

---

## 🛡️ Permissions

Only users with IDs listed in `Allowed_User_IDS` in `main.py` can use:
- `/addidolpic`

---

## 🧪 Testing

You can test using:
```bash
python main.py
```

Make sure your bot is invited to your Discord server with **application commands (slash commands)** enabled.

---

## 🤝 Credits

- Discord Bot via `discord.py`
- Reddit API via `asyncpraw`
- Google Sheets via `gspread`
- Environment handling via `python-dotenv`

---

## 📄 License

MIT License 
