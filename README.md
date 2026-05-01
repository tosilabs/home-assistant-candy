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

In addition to read-only sensors, the integration exposes a few ways to send commands back to the device:

### Buttons

Each appliance device gets two buttons in Home Assistant:
- `button.pause` — pauses the running cycle (`Pause=1`, `WiFiStatus=1`)
- `button.resume` — resumes a paused cycle (`Pause=0`, `WiFiStatus=1`)

These payloads are based on community reverse-engineering and may not work on every model.

### Services

- `candy.pause` — same as the Pause button, but as a service.
- `candy.resume` — same as the Resume button, but as a service.
- `candy.send_command` — send arbitrary key/value parameters to `http-write.json`. Use this when you know the parameter names accepted by your specific model (e.g. start a wash program, change temperature, set spin speed).

Example: start a wash program (parameter names vary by model — these are illustrative):

```yaml
service: candy.send_command
data:
  entry_id: <your_candy_config_entry_id>
  params:
    WashProgr: 13
    Temp: 40
    SpinSpeed: 8
    OpzProg: p
    WiFiStatus: 1
```

The write protocol is **not officially documented**. If a built-in command doesn't work for your appliance, capture the requests sent by the official Candy/Hoover/hOn app (e.g. with mitmproxy) and replay the parameters via `candy.send_command`.

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
