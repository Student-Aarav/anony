# Anony 🍊

Anony is the horny-but-wholesome AI confessional. It talks to **Grok 4.1 Fast**
through [OpenRouter](https://openrouter.ai/), remembers the last six spicy
messages, and wipes the slate the second you hit Reset. Think of it as therapy
with fewer co-pays and slightly more innuendo.

> “Talk to me about anything and just press reset and no one will know… unless
> you brag about it on Twitter.”

## What you get (besides questionable life choices)

- 🧠 **Dual personalities**: a CLI (`main.py`) and a web UI (`app.py` +
  `static/index.html`). Both whisper the same lightly flirty system prompt to
  Grok so replies feel human, but not HR-violation human.
- 📝 **Session memory**: up to 6 user/assistant pairs per session. More than
  that and Anony politely forgets like your ex reading your diary.
- 🔒 **Reset button**: instantly nukes history because sometimes you need to
  ghost your own brain.
- 🧯 **Security goodies**: secure cookies, CSP, prompt length limits, and all
  that boring but essential stuff so no one peeps your pillow talk.

## Quick start (PC only, because mobile people can fend for themselves)

1. Install deps:
   ```powershell
   pip install -r requirements.txt
   ```
2. Set secrets locally (never commit these—seriously):
   ```powershell
   setx OPENROUTER_API_KEY "sk-or-v1-your-real-key"
   setx FLASK_SECRET_KEY "make-it-long-and-spicy"
   ```
   Restart your terminal so Python can sniff them.

### CLI flavor

```powershell
python main.py
```
Type, giggle, repeat. Exit with `exit`/`quit` when you’ve overshared.

### Web flavor

```powershell
python app.py
```
Then open <http://localhost:5000>. You’ll see the orange/white UI, the response
card on top, and Send/Reset buttons ready to enable or erase your crimes.

## Deploying without flashing your keys

1. Push the repo to GitHub—`.env` is already ignored, so you won’t leak secrets.
2. On Cloudflare, run:
   ```bash
   wrangler secret put OPENROUTER_API_KEY
   wrangler secret put FLASK_SECRET_KEY
   ```
3. Swap the in-memory `HISTORY_STORE` for Workers KV (or Redis) when you’re
   ready to scale gossip.
4. Serve `static/` as your Pages assets and wire `/api/*` to the Worker version
   of `app.py` (or an equivalent handler).

## Under the hood (because you’re curious)

- Sends `system + history + user` messages to `x-ai/grok-4.1-fast` via
  `https://openrouter.ai/api/v1/chat/completions`.
- Cookies: `HttpOnly; Secure; SameSite=Strict`, so JS can’t steal your session.
- CSP + safety headers so random scripts can’t do the nasty in your DOM.
- Prompt length capped at 2k chars to block essay-length confessions.

## FAQ nobody asked for

**Can I see the API key in the browser?** No, the frontend only talks to
`/api/*`. Keys live server-side like a chaste Victorian secret.

**What if someone steals my laptop?** That’s on you, but rotate the keys and
log out before you leave your machine unattended with the incognito tab open.

**Is this legal?** I am not your lawyer, therapist, or mom. Use at your own
risk, but at least you’ll look stylish doing it.

Now go forth and overshare responsibly.***
