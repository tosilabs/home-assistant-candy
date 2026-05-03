# Candy / Hoover Simply‑Fi për Home Assistant

> Ky projekt është një **fork/përshtatje** e integrimit origjinal të krijuar nga **@ofalvai**.  
> Repo origjinale: https://github.com/ofalvai/home-assistant-candy

Integrim custom për Home Assistant që lidh pajisjet Candy/Hoover/Haier Simply‑Fi në rrjet lokal dhe lejon:
- monitorim sensori,
- nisje/ndalim/pause/resume programesh,
- konfigurim programesh nga Home Assistant.

---

## Çfarë ofron ky fork

Ky version është përshtatur për rastin tonë me fokus në:
- organizim më të qartë të entiteteve (Controls / Configuration / Sensors),
- përshkrime programi në shqip (`description_sq`),
- kategorizim programesh në shqip (`category_sq`, `profile_sq`),
- sinkronizim më të mirë të disa parametrave të programeve (p.sh. `opt_mask` për washing machine),
- sjellje më e butë në restart kur pajisja është offline (retry në background pa dështim të setup-it).

---

## Pajisjet e suportuara
- Washing machine
- Tumble dryer
- Oven
- Dishwasher

---

## Instalimi (HACS)
1. Hape **HACS → Integrations**.
2. Shto këtë repo si custom repository (nëse nuk është shtuar).
3. Instalo integrimin.
4. Restart Home Assistant.
5. Shko te **Settings → Devices & Services → Add Integration → Candy**.

> Që HACS të shohë versionet e reja, duhet release/tag i ri në GitHub.

---

## Konfigurimi
Duhet:
- IP e pajisjes,
- çelësi i enkriptimit (kur modeli e kërkon).

Për nxjerrjen e key/IP mund të përdoret mjeti i komunitetit:
https://github.com/MelvinGr/CandySimplyFi-tool

---

## Entitetet kryesore

### Controls
- Start
- Stop
- Pause
- Resume

### Configuration
- Program select
- Temperature
- Spin speed
- Soil level
- Steam

### Sensors
- Machine status
- Phase
- Time remaining
- Program
- Error
- dhe sensorë të tjerë sipas llojit të pajisjes.

---

## Metadata në shqip për programet
Ky fork shton atribute shtesë te `select` e programeve:
- `category_sq` – kategoria (p.sh. Cycles, Baby Care, Health & Hygiene)
- `profile_sq` – profil i shpejtë (temperaturë/rpm ose nxehtësi)
- `description_sq` – përshkrim i shkurtër në shqip

Kjo e bën dashboard-in më të kuptueshëm gjatë përzgjedhjes së programeve.

---

## Shënim i rëndësishëm
Nëse pajisjet janë fikur gjatë restart-it të Home Assistant:
- integrimi nuk duhet të ngelet me “Failed setup”
- provon sërish automatikisht derisa pajisja bëhet reachable.

---

## Kreditet
- Krijuesi i integrimit origjinal: **@ofalvai**  
  https://github.com/ofalvai/home-assistant-candy
- Kontributet dhe reverse-engineering nga komuniteti Home Assistant / Candy Simply‑Fi.

