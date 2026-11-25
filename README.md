# LLM Subscription Limits

Prototype Home Assistant custom integration for monitoring LLM subscription usage.
Only OpenCode Go is implemented. Other providers are future work, not promised.

## OpenCode Go

The integration polls the [documented OpenCode Go usage API](https://opencode.ai/docs/console/go/#usage)
every five minutes and creates percentage sensors for the five-hour, weekly and
monthly windows. Each includes `status`, `resets_at`, and an estimated
`window_started_at`. Monthly start is estimated as one calendar month before
reset; the provider does not supply that start. Forecasts are estimates.

One Go account is supported per Home Assistant instance in this prototype:
the usage API does not provide an immutable account ID. Reauthentication
retains sensor identities. Other providers will use separate configuration entries.

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
