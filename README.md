# Candy Home Assistant component

[![Run tests](https://github.com/ofalvai/home-assistant-candy/actions/workflows/test.yml/badge.svg)](https://github.com/ofalvai/home-assistant-candy/actions/workflows/test.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![codecov](https://codecov.io/gh/ofalvai/home-assistant-candy/branch/main/graph/badge.svg?token=HE0AIQOGAD)](https://codecov.io/gh/ofalvai/home-assistant-candy)

Custom component for [Home Assistant](https://homeassistant.io) that integrates Candy/Haier/Simply-Fi home appliances.


## Features
- Supported appliances:
   - washing machine 
   - tumble dryer
   - oven
   - dishwasher
- Uses the local API and its status endpoint
- Creates various sensors, such as device state and remaining time. Everything else is exposed as sensor attributes
- **Write commands** (experimental): Pause/Resume buttons per device, plus a generic `candy.send_command` service for sending arbitrary parameters to the device's `http-write.json` endpoint

## Write commands

In addition to read-only sensors, the integration exposes a few services to send commands back to the device. The write protocol is **not officially documented**, and on most modern Candy/Hoover devices the command is XOR-encrypted with the same key used for reading status, then hex-encoded and sent as the `data` parameter:

```
http://<ip>/http-write.json?encrypted=1&data=<hex>
```

### Services

| Service | When to use |
|---|---|
| `candy.send_raw_command` | You have a captured hex blob (e.g. from mitmproxy or an old config) and want to replay it. |
| `candy.send_plaintext_command` | You know the plaintext command format. The integration XOR-encrypts it with your device key automatically. |
| `candy.decrypt_data` | You have a captured hex blob and want to learn its plaintext format. The plaintext is logged at WARNING level in the Home Assistant log. |
| `candy.send_command` | Legacy: sends key/value pairs as plain URL params (only works on non-encrypted models). |

#### Example: replay a captured hex command

```yaml
service: candy.send_raw_command
data:
  entry_id: <your_candy_config_entry_id>
  data: "3F150810065C5F423F153B185E5E45270D0B2C005E5148341E2F055151"
```

#### Example: send a plaintext command (auto-encrypted)

```yaml
service: candy.send_plaintext_command
data:
  entry_id: <your_candy_config_entry_id>
  plaintext: "WashProgr=13&Temp=40&WiFiStatus=1"
```

#### Example: decrypt a captured hex blob to learn its format

```yaml
service: candy.decrypt_data
data:
  entry_id: <your_candy_config_entry_id>
  data: "3F150810065C5F423F153B185E5E45270D0B2C005E5148341E2F055151"
```

Then check the Home Assistant log for a line like `candy.decrypt_data result: ...` containing the plaintext.

## Installation

1. Install [HACS](https://hacs.xyz/)
2. Go to the integrations list in HACS and search for `Candy Simply-Fi`
4. Restart Home Assistant
5. Go to the Integrations page, click Add integrations and select `Candy`
6. Complete the config flow

## Configuration

You need the IP address of the machine and the encryption key. This can be guessed with [CandySimplyFi-tool](https://github.com/MelvinGr/CandySimplyFi-tool).


## My device isn't supported. Can you help?

Yes. If you have an appliance that is not supported yet, or you see an error, head over to the [Discussions section](https://github.com/ofalvai/home-assistant-candy/discussions/categories/device-support-improvements). Open a new thread or comment to an existing one with the following information:

- The status API response of your device (use [CandySimplyFi-tool](https://github.com/MelvinGr/CandySimplyFi-tool) to get the JSON)
- A brief explanation of what each field means in the response and how it changes based on the device state, eg. _The `SpinSp` field is probably the spin speed divided by 100, I have seen values 6, 8, 10 and 12 in the response_
