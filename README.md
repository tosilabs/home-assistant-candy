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

In addition to read-only sensors, the integration can send commands back to the device. The write protocol is **not officially documented**; on encrypted Candy/Hoover devices the command is XOR-encrypted with the same key used for reading status, then hex-encoded and sent as the `data` parameter:

```
http://<ip>/http-write.json?encrypted=1&data=<hex>
```

### Plaintext command format (washing machines)

Reverse-engineered from real captured commands:

| Action | Plaintext template |
|---|---|
| Start program | `Write=1&Pa=0&Sel=0&PrNm=<N>&StSt=1[&Temp=<T>][&SLevTgt=<L>][&SpdTgt=<S>][&SpdDef=<S>]&Stm=0&RecipeId=0&CheckUpState=0` |
| Stop program | `Write=1&StSt=0&DelMd=0&PrNm=<N>` |
| Pause | `Write=1&Pa=1` |
| Resume | `Write=1&Pa=0` |

### High-level services

```yaml
# Start program 13 at 40°C, spin 15
service: candy.washing_machine_start
data:
  entry_id: <your_candy_config_entry_id>
  program: 13
  temp: 40
  spin_target: 15
  spin_default: 10
```

```yaml
# Stop the current program
service: candy.washing_machine_stop
data:
  entry_id: <your_candy_config_entry_id>
  # `program` is optional — defaults to the current program from device status
```

```yaml
service: candy.washing_machine_pause
data:
  entry_id: <your_candy_config_entry_id>
```

### Low-level services

| Service | When to use |
|---|---|
| `candy.send_raw_command` | Replay a captured hex blob (e.g. from mitmproxy). |
| `candy.send_plaintext_command` | Send your own plaintext; the integration auto-encrypts with your device key. |
| `candy.decrypt_data` | Decrypt a captured hex blob to learn its plaintext format. The result is logged at WARNING level. |
| `candy.send_command` | Legacy: sends key/value pairs as plain URL params (only works on non-encrypted models). |

```yaml
# Replay a captured hex blob
service: candy.send_raw_command
data:
  entry_id: <your_candy_config_entry_id>
  data: "3F150810065C5F423F153B185E5E45270D0B2C005E5148341E2F055151"

# Or auto-encrypt arbitrary plaintext
service: candy.send_plaintext_command
data:
  entry_id: <your_candy_config_entry_id>
  plaintext: "Write=1&Pa=0&Sel=0&PrNm=4&StSt=1&Stm=0&RecipeId=0&CheckUpState=0"

# Or decrypt a captured blob to learn its format (check log for result)
service: candy.decrypt_data
data:
  entry_id: <your_candy_config_entry_id>
  data: "3F150810065C5F423F153B185E5E45270D0B2C005E5148341E2F055151"
```

The high-level `washing_machine_*` services have only been verified against a Candy washing machine with this format. If your model speaks a different dialect, capture a working command from the Candy/hOn app, decrypt it via `candy.decrypt_data`, and either send the discovered plaintext via `candy.send_plaintext_command` or open an issue with the format.

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
