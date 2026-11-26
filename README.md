# LLM Subscription Limits

[![Open in Home Assistant Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=y-decimal&repository=ha-llm-subscription-limit-integration&category=integration)

Prototype Home Assistant custom integration for monitoring LLM subscription usage.
Only OpenCode Go is implemented. Other providers are future work, not promised.

Brand icon: the `chart-donut` glyph from [Material Design Icons](https://pictogrammers.com/library/mdi/icon/chart-donut/)
(Pictogrammers), Apache-2.0 — see [LICENSES/MDI-Apache-2.0.txt](LICENSES/MDI-Apache-2.0.txt).
It is the same glyph the sensors use, re-scaled and filled with a gradient.

## OpenCode Go

The integration polls the [documented OpenCode Go usage API](https://opencode.ai/docs/console/go/#usage)
every five minutes and creates percentage sensors for the five-hour, weekly and
monthly windows. Each includes `status`, `resets_at`, and an estimated
`window_started_at`. Monthly start is estimated as one calendar month before
reset; the provider does not supply that start. Forecasts are estimates.

One Go account is supported per Home Assistant instance in this prototype:
the usage API does not provide an immutable account ID. Reauthentication
retains sensor identities. Other providers will use separate configuration entries.

## Settings and controls

Each provider is a **device** (`OpenCode Go`) holding its usage sensors.
Integration-wide settings live on a separate **service device**,
`LLM Subscription Limits`, so they are not named after one provider:

| Entity | What it does |
|---|---|
| `number.llm_subscription_limits_poll_interval` | Minutes between polls, 1–60, default 5. Applies to every provider and is stored in the integration's own settings file, so it survives restarts. |
| `button.llm_subscription_limits_refresh_now` | Fetches every provider immediately and restarts the interval. |

Both are `CONFIG` entities, so they appear under *Configuration* on the device
page rather than as primary controls. The interval is global on purpose: a
single clock matches how people think about "how often does this update". If a
provider later needs its own cadence, an optional per-provider override can be
added on its device without moving the global value.

## Install

Add this repository by URL as an Integration custom repository in Marketplace,
then install it. Depending on your Home Assistant version, a restart may be
required; follow the installation prompt.
Add **LLM Subscription Limits** under Settings > Devices & services and
provide an eligible OpenCode Go API key. Do not post the key in a chat.

Home Assistant stores the key as config-entry connection data. It is not
encrypted by this integration; protect Home Assistant backups and administrator
access. The key is only sent to the fixed HTTPS OpenCode endpoint. Home
Assistant and trusted custom integrations have access to their environment.
Errors do not include provider response bodies or credentials.

This direct approach is independent of OpenCode itself. If you already use a
REST/bridge setup, do not replace it without a migration plan: new entities
have separate unique IDs and history does not automatically carry over.

## Dashboard example

Install the companion [LLM Subscription Limit Card](https://github.com/y-decimal/ha-llm-subscription-limit-card)
separately as a Marketplace Dashboard repository. Reload the browser, then
choose the card and its sensor in the dashboard's visual editor.
Actual entity IDs can differ: select the newly created entity in the UI.
The card derives its forecast from the sensor state and estimated window start;
history fills as Home Assistant records readings.

## Releasing

Marketplace shows the latest **GitHub release tag**, not the commit hash, so every
shipped change needs a release. The tag and `manifest.json` `version` must match
(a leading `v` in the tag is fine).

1. Bump `version` in `custom_components/llm_subscription_limits/manifest.json`.
2. Commit and push to `main`.
3. Create a release tagged `vX.Y.Z` on `main`.

Versions follow semantic versioning: patch for fixes, minor for new providers or
options, major for breaking config changes. Bump only when shipped behaviour
changes — documentation, CI and metadata commits do not need a release, so the
version keeps meaning something. The card repository is versioned the same way,
independently of this one.

## Development

The provider adapter owns API access and normalization; each future provider
must own its authentication and coordinator. Sensor unique IDs are scoped
to a provider and stable across key rotation. Config-entry schemas are
versioned; future incompatible changes must include migrations. No generic
provider interface is frozen before a second provider has been implemented.

Run provider unit tests with `python -m unittest discover -s tests` and
`aiohttp` installed; Home Assistant
config flow and lifecycle tests require a matching HA test environment.
The CI definitions run HACS and hassfest validators, but have not been run
until a commit is pushed and the GitHub Actions results are inspected.
