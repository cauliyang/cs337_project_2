# How to Open Web UI

## Quick Start (3 Steps)

### 1. Start Action Server

Open Terminal 1:

```bash
source .venv/bin/activate
cd rasa
rasa run actions
```

Keep this terminal open ✅

### 2. Start Rasa Server

Open Terminal 2:

```bash
source .venv/bin/activate
cd rasa
rasa run --enable-api --cors "*"
```

Keep this terminal open ✅

### 3. Open Web Interface

```bash
# macOS/Linux
open index.html

# Windows
start index.html
```

That's it! The chat interface should open in your browser.

---

## Test It Works

Type in the chat:

```
hi
```

You should get a response from the bot.

---

## If Something Goes Wrong

**Connection error?**

```bash
# Kill processes and restart
kill -9 $(lsof -ti:5005)
kill -9 $(lsof -ti:5055)

# Start again (steps 1 & 2)
```

**No styling?**
Make sure `index.html`, `style.css`, and `script.js` are in the same folder.

---

## Stop Everything

1. Close browser tab
2. Press `Ctrl+C` in both terminals
