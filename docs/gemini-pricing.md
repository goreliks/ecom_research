# Gemini API Pricing (updated March 2026)

Video tokenization: ~258 tokens per second of video

## Models

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Notes |
|---|---|---|---|
| gemini-3.1-pro-preview | $2.00 (<=200k), $4.00 (>200k) | $12.00 (<=200k), $18.00 (>200k) | Best quality, preview |
| gemini-3-flash-preview | $0.50 (text/image/video), $1.00 (audio) | $3.00 | Latest gen, preview |
| gemini-3.1-flash-lite-preview | $0.25 (text/image/video), $0.50 (audio) | $1.50 | Lightweight, preview |
| gemini-2.5-pro | $1.25 (<=200k), $2.50 (>200k) | $10.00 (<=200k), $15.00 (>200k) | Stable, high quality |
| gemini-2.5-flash | $0.30 (text/image/video), $1.00 (audio) | $2.50 | Stable, good balance |
| gemini-2.5-flash-lite | $0.10 (text/image/video), $0.30 (audio) | $0.40 | Cheapest current |
| gemini-2.0-flash | $0.10 (text/image/video), $0.70 (audio) | $0.40 | Deprecated June 2026 |

## Batch API

50% discount on input/output for all models.

## Free tier

- Available for most models (limited rate limits)
- Free tier data may be used for product improvement
- Preview models have more restrictive rate limits

## Sources

- https://ai.google.dev/gemini-api/docs/pricing
- https://cloud.google.com/vertex-ai/generative-ai/pricing
