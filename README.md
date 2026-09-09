# hermes-plugin-zyte-extract

A [Hermes](https://github.com/NousResearch/hermes-agent) plugin: URL-to-clean-text
extraction via [Zyte's Extract API](https://www.zyte.com/extract/), a paid backstop
for when free extraction tiers are exhausted or insufficient.

## What it does

Registers an extract-only `web_extract` provider backend
(`provides_web_providers: [zyte]`). Calls Zyte's `/v1/extract` endpoint with
`"article": true`, returning clean structured JSON (`article.articleBody`).

## Why Zyte, and why paid

Evaluated alongside Diffbot (which has a recurring free tier — see
[hermes-plugin-diffbot-extract](https://github.com/sergattic/hermes-plugin-diffbot-extract))
as a second, independent paid option. Zyte is pure pay-as-you-go: $0.13 per 1,000
requests, no monthly minimum, with a small free trial credit on signup — no
recurring free tier, but meaningfully cheaper per-call than most alternatives. A
sensible choice to place as a paid backstop *after* every free extraction rung in a
fallback ladder, ahead of pricier paid options.

## Requirements

- A Zyte account and API key: https://www.zyte.com/extract/
- `ZYTE_API_KEY` in the environment. Auth is HTTP Basic with the API key as
  username and an empty password (Zyte's documented scheme).

## Config (`config.yaml`)

```yaml
secrets:
  onepassword:
    env:
      ZYTE_API_KEY: op://<your-vault>/<item>/<field>
```

## Install

```
hermes plugins install sergattic/hermes-plugin-zyte-extract
```

## License

MIT
