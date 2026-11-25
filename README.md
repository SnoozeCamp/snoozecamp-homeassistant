# SnoozeCamp for Home Assistant

Home Assistant integration for [SnoozeCamp](https://snoozecamp.com): keeps the parking climatisation of a
Volkswagen ID. running overnight and shows the vehicle's state. A SnoozeCamp worker (an Android phone with
the SnoozeCamp worker app) is required.

*Deutsch: siehe [unten](#deutsch).*

## Installation

### HACS (recommended)

1. In HACS, search for **SnoozeCamp**.
2. Install it and restart Home Assistant.

### Manual

Copy `custom_components/snoozecamp` into your `config/custom_components/` folder and restart Home Assistant.

## Setup

**Settings → Devices & services → Add integration → SnoozeCamp.** There are two ways to connect:

| Mode | URL | Token |
|---|---|---|
| **Online** | `https://app.snoozecamp.com` | Create one in the SnoozeCamp app under *Settings* |
| **Local (Wi-Fi)** | `http://PHONE-IP:8765` | In the worker app under *Settings → Home Assistant on Wi-Fi* |

Both offer the same entities. The local mode needs no internet and no server, but the phone and Home
Assistant must be on the same network. It uses plain HTTP, so only use it on a network you trust, and give
the phone a fixed IP address in your router.

You can add both modes; each vehicle then appears twice.

## Entities per vehicle

| Type | Entities |
|---|---|
| Sensor | Range, battery, charge target, target temperature, climate time left, camping ends, last reading, phone battery (*) |
| Binary sensor | Charging, climate running, worker online, lock (only for models whose VW app shows it), phone on power (*) |
| Switch | Climate (one run / stop), camping (duration in the integration options, default 8 hours), charging (start / stop, needs worker 1.5.1 and a plugged-in cable) |
| Number | Target temperature |
| Button | Read status now |

(*) Battery of the worker phone itself, for example to switch its plug off at 80 % or to warn when it runs low.
These appear once you switch on *Phone battery* in the worker settings (worker 1.5.2 or later).

Locking and unlocking are not supported; the lock state is shown only.

Changes arrive as a live stream, so states update within seconds after the worker has read the car.

## Notes

- The token is stored by Home Assistant. Anyone holding it can read the vehicle state and start or stop the
  climatisation or charging. Revoke it in the app (online) or create a new one in the worker (local) if it leaks.
- Set a battery floor in the SnoozeCamp app; the camping mode stops the climatisation there.
- SnoozeCamp is not affiliated with Volkswagen.

## Deutsch

SnoozeCamp hält die Standklimatisierung eines VW ID. über Nacht am Laufen. Diese Integration zeigt den
Fahrzeugstand in Home Assistant und schaltet Klima, Camping und Laden (Laden ab Worker 1.5.1, Kabel muss stecken).

- **Installation:** In HACS nach **SnoozeCamp** suchen, installieren, Home Assistant neu starten.
- **Online:** URL `https://app.snoozecamp.com`, Token aus der SnoozeCamp-App (Einstellungen).
- **Lokal im WLAN:** URL `http://IP-DES-HANDYS:8765`, Token aus dem Worker (Einstellungen → Home Assistant im
  WLAN). Unverschlüsselt, nur im eigenen Netz nutzen; dem Handy im Router eine feste IP geben.
- **Handy-Akku:** Im Worker unter Einstellungen → *Handy-Akku* einschalten (ab Worker 1.5.2). Dann gibt es die
  Sensoren *Handy-Akku* und *Handy am Strom*, etwa um die Steckdose bei 80 % abzuschalten.
- Ver- und Entriegeln gibt es nicht, der Schlosszustand wird nur angezeigt.
