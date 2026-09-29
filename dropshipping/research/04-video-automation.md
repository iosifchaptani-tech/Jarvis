# Research 4: Automatic product videos from n8n

*Research agent report, 2026-09-29. "(unverified)" marks facts the agent could not confirm.*

**Answer:** Keep the owner's **real phone footage** as the main visual. Build the video with a template render API that includes AI voice and word-by-word captions, then send the MP4 to Telegram. Posting stays manual.

## 1. Render APIs (30 s, 1080×1920)

| Tool | Free tier | Cheapest paid | ≈ per video | Voice + captions included | n8n |
|---|---|---|---|---|---|
| **JSON2Video** (used here) | 600 credits, watermark, **non-commercial** | Prepaid **$49.95 = 7,200 credits** (never expire) | **$0.125-0.21** | **Yes, 0 credits** | community node + HTTP |
| Shotstack | 10 credits for 30 days (≈ 20 videos, no watermark) | $0.30/min pay-as-you-go | $0.10-0.15 | TTS + auto captions | verified node |
| Creatomate | 50 credits, output ≤480 px | ~$41-54/mo (unverified) | $0.39-0.51 | captions yes; voice only with your own key | verified node |
| Placid / Bannerbear / Plainly | – | $19-69/mo | $0.47-2.94 | no | – |
| FFmpeg, self-hosted | free | $0 | $0 | build it yourself | Execute Command |

Sources: [JSON2Video pricing](https://json2video.com/pricing/), [credits](https://json2video.com/docs/v2/pricing/credit-consumption), [API](https://json2video.com/docs/v2/api-reference/api-endpoints/movies), [Shotstack](https://shotstack.io/pricing/), [Creatomate credits](https://creatomate.com/llms/credits.md).

**JSON2Video API:**
- Create: `POST https://api.json2video.com/v2/movies` with header `x-api-key`. Returns `{success, project}`.
- Poll: `GET /v2/movies?project=ID` until `movie.status` is `done`, `error` or `timeout`, then read `movie.url`.
- Files are kept about 7 days.
- The POST isn't idempotent, so a retry creates a new render.

**FFmpeg route ($0):**
- Execute Command is **disabled by default since n8n 2.0**, and the image has had no `apk` since 2.1 ([n8n 2.0 changes](https://docs.n8n.io/changelog/v20-breaking-changes)).
- It needs a custom Docker image and isn't available on n8n Cloud.
- Expect 1-2 weekends of setup.

## 2. AI voice

- **ElevenLabs:**
  - The free plan is **non-commercial** and requires attribution.
  - Starter costs $6/mo with a commercial licence.
  - API: $0.08 per 1K characters for v2/v3, $0.04 for Flash ([pricing](https://elevenlabs.io/pricing/api)).
- **OpenAI `gpt-4o-mini-tts`:** about $0.015/min. You must tell listeners the voice is AI.
- **Google Cloud TTS:** a free monthly allowance. **Gemini TTS:** a free tier until 31 Dec 2026 (your data is used to improve Google's products).
- **Built into JSON2Video:** Azure and ElevenLabs voices cost 0 credits.

## 3. AI-generated video b-roll

- **The OpenAI Sora API shut down on 24 Sept 2026.**
- **Cheapest options per clip:**
  - Veo 3.1 Lite: $0.20 per 4 s
  - Kling 2.5 Turbo on fal.ai: $0.21 per 5 s
  - Hailuo 2.3 Fast: $0.19 per 6 s
  - Luma: $0.15-0.30
  - Runway: $0.25
- **Common problems:**
  - Product shapes and logos "morph" between frames.
  - Scenes come out over-styled.
  - You typically need 2-4 attempts per usable clip.
- **Recommendation: don't use AI video in the first 2 weeks.**
  - A product that looks different from the real one is a deception risk.
  - Realistic AI clips need an AI label.
  - Real footage is what TikTok rewards as original.
  - Later: at most one labelled ambient shot per video that doesn't show the product.

## 4. Captions

JSON2Video's `subtitles` element auto-transcribes the voice at 0 credits. Styles include `classic-progressive` (word by word). Alternatives:
- Whisper: $0.006/min
- Deepgram: $200 free credit
- ElevenLabs `/with-timestamps`, which gives exact timing with no transcription

## 5. Pipeline built into workflow 02

1. `/content SKU` writes the scripts.
2. The owner films 3-5 clips, uploads them to Google Drive or Dropbox, and sends `/clips SKU link1 link2 link3`.
3. `/render VIDEO_ID`:
   - The script's voiceover is split into up to 4 scenes: hook with clip 1, demo with clip 2, CJ product photo, then call to action with clip 3.
   - Azure voice and word-by-word captions are added.
   - The render is sent to JSON2Video, and n8n checks it every 20 s (giving up after 10 min).
   - You get the link plus the MP4 on Telegram, with a posting checklist.

**Monthly cost at 3 videos/day:**
- JSON2Video prepaid: about **$19**.
- The free tier works for testing only (watermarked, non-commercial).

## 6. Compliance when posting

- **TikTok:**
  - Turn on **"AI-generated content"** for realistic AI media. A realistic AI voice counts as the safe choice ([TikTok](https://newsroom.tiktok.com/en-us/new-labels-for-disclosing-ai-generated-content)).
  - Reposted or unoriginal content is kept out of For You ([FYF standards](https://www.tiktok.com/safety/en/policies-and-engagement/fyf-standards)).
- **Instagram:** the **AI info** label ([Meta](https://about.fb.com/news/2024/04/metas-approach-to-labeling-ai-generated-content-and-manipulated-media/)).
- **YouTube:** only realistic synthetic scenes need disclosure. AI-written scripts are exempt ([YouTube](https://support.google.com/youtube/answer/14328491)).
- **FTC (US):**
  - No testimonials from people who don't exist or never used the product, and that includes AI avatars.
  - Keep the voice a *brand narrator*. Never have it say "I've used this for months" ([FTC Q&A](https://www.ftc.gov/business-guidance/resources/consumer-reviews-testimonials-rule-questions-answers)).
- **Music:** never bake it into the file. Add a platform sound in each app. TikTok business accounts can only use the Commercial Music Library ([TikTok](https://ads.tiktok.com/help/article/commercial-music-library)).
