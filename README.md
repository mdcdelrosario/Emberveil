# ✦ Emberveil

> *where the embers never sleep*

A cozy atmospheric indie game built in Python. Guide fireflies through a dark meadow veiled in shadow — charge ancient zones, bloom emberblooms, cleanse the darkness, and restore harmony to the night.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)

---

## 📸 Overview

Emberveil is a relaxing, mouse-driven game where you use light to push back the dark. Attract glowing fireflies with your cursor, complete a series of ritualistic tasks, and bring the meadow back to life — all set to a procedurally generated ambient soundtrack.

```
✦ Charge the Zones       →   attract fireflies into glowing rings
✦ Awaken the Heart       →   gather embers at the center
✦ Bloom Emberblooms      →   right-click to plant flowers of light
✦ Cleanse the Shadows    →   click dark patches to purify them
✦ Harmony Ritual         →   summon all fireflies for the final rite
```

---

## 🗂 Project Structure

```
Firefly Meadow/
│
├── menu.py          # Main menu — cinematic intro, animated embers, ambient audio
├── emberveil.py     # Core game — all gameplay, task panel, particle system
└── README.md        # This file
```

---

## ⚙️ Requirements

| Dependency | Version | Notes |
|------------|---------|-------|
| Python | 3.8+ | Standard install |
| `tkinter` | built-in | Included with most Python installs |
| `numpy` | any | Required for procedural audio generation |

### Install numpy

```bash
pip install numpy
```

> **Note:** If you're using a virtual environment (recommended):
> ```bash
> python -m venv .venv
> .venv\Scripts\activate       # Windows
> source .venv/bin/activate    # macOS / Linux
> pip install numpy
> ```

### Verify tkinter is available

```bash
python -m tkinter
```

A small test window should appear. If it doesn't, see [Troubleshooting](#-troubleshooting).

---

## 🚀 Running the Game

Always launch via the menu:

```bash
python menu.py
```

Or jump straight into the game:

```bash
python emberveil.py
```

---

## 🎮 Controls

| Input | Action |
|-------|--------|
| `Left-click` | Attract nearby fireflies toward cursor |
| `Left-click + drag` | Continuously guide a stream of fireflies |
| `Right-click` | Plant an emberbloom flower *(unlocks at Task 3)* |
| `Left-click on shadow` | Strike a shadow patch to cleanse it |

---

## 📋 Task Guide

The **Emberveil Journal** panel on the right side of the screen tracks your progress. There are 5 sequential tasks:

### Task 1 — Charge the Zones
Three glowing rings appear around the meadow. Attract fireflies into each ring — the charge percentage climbs as more fireflies stay inside. All three must reach 100%.

### Task 2 — Awaken the Heart
Guide at least **8 fireflies** into the large circle at the center of the screen. The Heart pulses and brightens as it fills.

### Task 3 — Bloom Emberblooms
**Right-click** anywhere on the canvas to plant a flower. Plant **5 emberblooms** to restore color to the meadow. Each bloom triggers a burst of particles.

### Task 4 — Cleanse the Shadows
Five dark patches appear across the meadow. Click each one to damage it — each patch requires **3 hits** and shrinks visibly with each strike. Destroy all of them.

### Task 5 — Harmony Ritual
The final task. Summon **15 fireflies** into the Heart circle simultaneously. The veil lifts. The embers find their home.

---

## 🔊 Audio System

Emberveil generates all audio **procedurally at startup** using `numpy` — no audio files need to be included in the repository.

Sounds are written to a temporary directory and played via the OS audio system:

| Platform | Playback Method |
|----------|----------------|
| Windows | `winsound` (built-in) |
| macOS | `afplay` |
| Linux | `aplay` |

### Sound Effects

| Sound | Trigger |
|-------|---------|
| Menu ambient | Deep E2/A2/C3 drone pad, loops on menu screen |
| Game ambient | Lighter A2/E3/A3 pad, loops during gameplay |
| Zone charge | Ascending arpeggio when a zone fills |
| Emberbloom | Soft descending bell on right-click |
| Cleanse | Frequency sweep when hitting a shadow patch |
| Stage complete | Triumphant chord hit on task completion |
| Victory fanfare | Full ascending melody on final task |
| Timeout | Descending sad tones if time runs out |
| Hover tick | Subtle click on button hover |

> Audio is **optional** — the game runs silently if `numpy` is not installed or if the OS audio command is unavailable.

---

## 🧩 Architecture

### `menu.py`
- Procedural sky gradient + 3-layer treeline silhouette
- 160 individually twinkling stars
- 55 rising ember particles with wobble physics
- 7 slow mist bands with sine-wave height variation
- Cinematic black stipple fade-in on launch
- `EmberButton` class with hover/leave animations
- Launches `emberveil.py` (falls back to `game.py` if not found)

### `emberveil.py`

**Rendering pipeline (per frame, ~30fps):**
1. Star twinkle pass
2. Zone charge update + draw
3. Heart pulse animation
4. Firefly movement + draw (28 agents)
5. Ambient sparkle particle emission
6. Particle system update + draw
7. Task check logic
8. Panel refresh

**Key classes:**

| Class | Description |
|-------|-------------|
| `Firefly` | Agent with velocity, wobble phase, glow halo, soft wall repulsion |
| `Zone` | Charging ring with fill percentage, pulse animation, color lerp |
| `DarkSpot` | 3-HP shadow patch that shrinks on hit |
| `Particle` | Lightweight spark with gravity, fade-out, lifetime |

**Audio engine:**
- All waveforms generated with `numpy` sine synthesis
- `_mix(*arrays)` helper zero-pads arrays before summing to prevent shape mismatch errors
- All RGB color values are clamped with `max(0, min(255, ...))` to prevent invalid hex crashes
- Playback in daemon threads so it never blocks the UI

---

## 🐛 Troubleshooting

### `ModuleNotFoundError: No module named 'tkinter'`
tkinter is not always included in Python on Linux. Install it with:
```bash
# Debian / Ubuntu
sudo apt-get install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

### No sound on Linux
Make sure `aplay` (part of `alsa-utils`) is installed:
```bash
sudo apt-get install alsa-utils
```

### Game file not found when clicking "Enter the Veil"
The menu looks for `emberveil.py` first, then falls back to `game.py`. Make sure your game file is in the **same directory** as `menu.py`.

### Window appears off-screen
The window auto-centers on launch. If it's still off-screen, try changing the resolution values at the top of the file:
```python
W, H = 860, 560   # menu.py
WIDTH, HEIGHT = 1100, 680   # emberveil.py
```

### `TclError: invalid color name`
All dynamic colors must be 6-digit hex (`#RRGGBB`). If you extend the code, always clamp RGB channels:
```python
r = max(0, min(255, int(value)))
color = f"#{r:02x}{g:02x}{b:02x}"
```

---

## 🎨 Color Palette

| Name | Hex | Used For |
|------|-----|---------|
| Deep Night | `#04080F` | Background |
| Ember Gold | `#FFB830` | Fireflies, accents |
| Ember Orange | `#FF7A00` | Particle glow |
| Heart Teal | `#00FFAA` | Zone charged, heart |
| Zone Blue | `#3A86FF` | Zone rings |
| Shadow Purple | `#C77DFF` | Dark spot glow |
| Bloom Pink | `#FF6B9D` | Emberbloom |
| Moon White | `#E8F0FF` | Moon |
| Veil Horizon | `#0E1F12` | Sky horizon tint |

---

## 🌱 Extending the Game

### Adding a new task
1. Add an entry to the `STAGES` list in `emberveil.py`
2. Add a new `elif stage == N:` block in `check_tasks()`
3. Call `_advance(N)` when the condition is met
4. The panel and progress bar update automatically

### Adding a new sound
1. Write a `gen_mysound()` function using `_sine()` and `_mix()`
2. Call it in the audio generation block at the top
3. Trigger it with `play_sfx("mysound")`

### Changing firefly count
```python
fireflies = [Firefly(canvas) for _ in range(28)]  # change 28
```

---

## 📄 License

MIT License — free to use, modify, and distribute. Attribution appreciated.

---

<div align="center">

*The embers glow. The darkness sleeps.*

**✦ Emberveil ✦**

</div>
