# Jarvis

A simple voice assistant for Windows. Talk to him or type to him, and he answers out loud.

## How to start Jarvis

1. Make sure **Python** is installed. If it isn't, get it from https://www.python.org/downloads/
   and tick **"Add python.exe to PATH"** during the install.
2. Download this folder, unzip it, and **double-click `START_JARVIS.bat`**.
3. In the black window:
   - **Press ENTER, then talk.** Wait until it says `Listening... speak now.`
   - Or **type** a message and press ENTER.
   - Type `exit` (or say "goodbye") to close him.

The window shows each step, like `Listening...`, `You said: ...` and `Thinking...`.
If Jarvis goes quiet, that text tells you where he got stuck.

## Things he can do without anything extra

- "What time is it?" / "What's the date?"
- "Open YouTube" / "Open Google"
- "Search cute cats" (opens a Google search)

## Your Pivendo store

- "Open my store" / "Open Shopify" / "Open n8n" / "Open CJ" opens that page.
- With an API key, you can ask about the store, e.g. "What's next for my store?" or
  "Which shipping method for a US drill order?". Jarvis answers from the status part of
  `PLAN-30-DAYS.md`, so keep that file up to date (Claude does this).
- Jarvis only works while his window is open and you talk to him. The work that happens
  while you sleep (research, order alerts, support drafts, the evening report) is done by
  the n8n automations in `dropshipping/`, and they report to you in Telegram.

## Let him answer any question (optional)

Jarvis uses Claude to answer questions. For that he needs a **Claude API key**. The key is
separate from a claude.ai subscription, and the API is paid per use:

1. Get a key at https://console.anthropic.com/ (API keys section).
2. In the Jarvis folder, make a text file named `api_key.txt`.
3. Paste the key into it (just the key, nothing else) and save.
4. Start Jarvis again.

`api_key.txt` is ignored by git, so it won't be uploaded to GitHub by accident.

To save money, Jarvis answers simple questions with a cheap, fast model (**quick mode**)
and only uses the smarter, pricier one (**smart mode**) when you ask him to explain, write,
plan, compare or solve something, or ask a long question. Say "think hard" to force smart
mode. The window shows which mode he used.

## If something doesn't work

| What you see | What to do |
|---|---|
| `The microphone could not be started` | Plug in a mic and allow it in Windows: Settings > Privacy & security > Microphone. You can still type meanwhile. |
| `I didn't hear anything` | Talk right after pressing ENTER, a bit louder or closer to the mic. |
| `I can't reach the speech service` | The speech-to-text needs internet. Check your connection. |
| `My API key was rejected` | The key in `api_key.txt` is wrong. Copy it again. |
| `out of credit` | Add credit to your account at console.anthropic.com. |
