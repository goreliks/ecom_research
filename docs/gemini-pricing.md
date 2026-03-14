# Gemini API Pricing (as of March 2026)

Video tokenization: ~258 tokens per second of video

## Models

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Cost for 16s video (~4,128 tokens) | Notes |
|---|---|---|---|---|
| gemini-2.5-flash | ~$0.15 | ~$1.00 | ~$0.0006 | Stable, good balance |
| gemini-2.5-pro | $1.25 (<=200k), $2.50 (>200k) | $10.00 (<=200k), $15.00 (>200k) | ~$0.005 | Higher quality |
| gemini-3-flash-preview | $0.50 | $3.00 | ~$0.002 | Latest gen, preview |
| gemini-3-pro-preview | $2.00 (<=200k), $4.00 (>200k) | $12.00 (<=200k), $18.00 (>200k) | ~$0.008 | Best quality, preview |
| gemini-2.0-flash-lite | cheapest | cheapest | ~free tier | Deprecated June 2026 |

## Free tier (gemini-2.5-flash)

- 500 requests/day
- Short TikTok videos cost fractions of a cent

## Sources

- https://ai.google.dev/gemini-api/docs/pricing
- https://cloud.google.com/vertex-ai/generative-ai/pricing
