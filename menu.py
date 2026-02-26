import tkinter as tk
import subprocess, sys, random, math, time, os
import wave, tempfile, threading

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

SAMPLE_RATE = 44100
TMP_DIR = tempfile.mkdtemp()

def _write_wav(path, samples):
    samples = np.clip(samples, -1, 1)
    data = (samples * 32767).astype(np.int16)
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1); wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE); wf.writeframes(data.tobytes())

def _sine(freq, dur, amp=0.5):
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    return amp * np.sin(2 * np.pi * freq * t)

def _mix(*arrays):
    n = max(len(a) for a in arrays)
    out = np.zeros(n)
    for a in arrays: out[:len(a)] += a
    return out

def gen_menu_ambient():
    """Deeper, slower pad than gameplay — more ominous/atmospheric."""
    dur = 14.0
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    freqs = [82.4, 110, 130.8, 164.8]  # E2, A2, C3, E3
    amps  = [0.20, 0.14, 0.10, 0.07]
    sig = np.zeros_like(t)
    for f, a in zip(freqs, amps):
        sig += a * np.sin(2 * np.pi * f * t)
        sig += a * 0.3 * np.sin(2 * np.pi * f * 2.003 * t)  # subtle overtone
    lfo1 = 0.65 + 0.35 * np.sin(2 * np.pi * 0.08 * t)
    lfo2 = 1.0  + 0.15 * np.sin(2 * np.pi * 0.19 * t + 1.2)
    sig *= lfo1 * lfo2
    fade = 2048
    sig[:fade]  *= np.linspace(0, 1, fade)
    sig[-fade:] *= np.linspace(1, 0, fade)
    _write_wav(os.path.join(TMP_DIR, "menu_ambient.wav"), sig * 0.50)

def gen_hover_tick():
    dur = 0.06
    sig = _sine(1200, dur, 0.25)
    n = len(sig)
    env = np.linspace(1, 0, n) ** 2
    _write_wav(os.path.join(TMP_DIR, "hover.wav"), sig * env)

def gen_click_chime():
    sig = _mix(_sine(880, 0.18, 0.4), _sine(1320, 0.18, 0.2))
    n = len(sig)
    env = np.exp(-np.linspace(0, 5, n))
    _write_wav(os.path.join(TMP_DIR, "click.wav"), sig * env * 0.7)

if HAS_NUMPY:
    gen_menu_ambient(); gen_hover_tick(); gen_click_chime()

_ambient_stop = False
_ambient_proc = None

def _play(path):
    plt = sys.platform
    try:
        if plt == "win32":
            import winsound
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return None
        elif plt == "darwin":
            return subprocess.Popen(["afplay", path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            return subprocess.Popen(["aplay", "-q", path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except: return None

def start_ambient():
    if not HAS_NUMPY: return
    def _loop():
        global _ambient_stop, _ambient_proc
        while not _ambient_stop:
            _ambient_proc = _play(os.path.join(TMP_DIR, "menu_ambient.wav"))
            if _ambient_proc: _ambient_proc.wait()
            else: time.sleep(14)
    threading.Thread(target=_loop, daemon=True).start()

def stop_ambient():
    global _ambient_stop, _ambient_proc
    _ambient_stop = True
    if _ambient_proc:
        try: _ambient_proc.terminate()
        except: pass

def sfx(name):
    if not HAS_NUMPY: return
    threading.Thread(
        target=lambda: _play(os.path.join(TMP_DIR, f"{name}.wav")),
        daemon=True).start()
    
W, H = 860, 560

# Deep ember-night palette
C_BG       = "#04080F"
C_SKY_MID  = "#07111C"
C_SKY_HOR  = "#0E1F12"   # slight green-teal at horizon — veil effect
C_EMBER    = "#FFB830"
C_EMBER2   = "#FF7A00"
C_GLOW     = "#FF4500"
C_MIST     = "#0A1E28"
C_TITLE    = "#FFD080"
C_SUBTITLE = "#5A8090"
C_BTN_FG   = "#8BB8C8"
C_BTN_HLT  = "#FFB830"
C_RULE     = "#1A3040"
C_FOOTER   = "#1E3545"
C_MOON     = "#E8F0FF"

FONT_TITLE    = ("Georgia", 44, "italic")
FONT_TITLE_SM = ("Georgia", 13, "italic")
FONT_SUB      = ("Courier New", 11, "italic")
FONT_BTN      = ("Courier New", 12)
FONT_HINT     = ("Courier New", 9, "italic")

def lerp(a, b, t): return a + (b - a) * t
def lerp_color(c1, c2, t):
    t = max(0, min(1, t))
    r1,g1,b1 = int(c1[1:3],16),int(c1[3:5],16),int(c1[5:7],16)
    r2,g2,b2 = int(c2[1:3],16),int(c2[3:5],16),int(c2[5:7],16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))

class Ember:
    """Rising glowing ember particle."""
    def __init__(self):
        self.reset(initial=True)

    def reset(self, initial=False):
        self.x  = random.uniform(0, W)
        self.y  = H + random.uniform(0, 80) if not initial else random.uniform(0, H)
        self.vx = random.uniform(-0.25, 0.25)
        self.vy = random.uniform(-0.6, -0.2)
        self.r  = random.uniform(1.2, 3.2)
        self.life = random.uniform(0.3, 1.0)
        self.max_life = self.life
        self.phase = random.uniform(0, math.tau)
        self.color_idx = random.random()  # 0=amber, 1=orange-red

    @property
    def color(self):
        pulse = 0.6 + 0.4 * math.sin(time.time() * 3 + self.phase)
        alpha = (self.life / self.max_life) * pulse
        if self.color_idx < 0.5:
            r, g, b = 255, int(184 * alpha), int(48 * alpha)
        else:
            r, g, b = 255, int(122 * alpha), 0
        r = min(255, int(r * alpha))
        g = min(255, int(g))
        b = min(255, int(b))
        return f"#{r:02x}{g:02x}{b:02x}"

    def update(self):
        wobble = math.sin(time.time() * 2.1 + self.phase) * 0.18
        self.x += self.vx + wobble
        self.y += self.vy
        self.life -= 0.004
        if self.life <= 0 or self.y < -20:
            self.reset()


class MistLayer:
    """Slow horizontal mist band."""
    def __init__(self, y, speed, alpha, width):
        self.x = random.uniform(-width, W)
        self.y = y
        self.speed = speed
        self.alpha = alpha
        self.w = width
        self.h = random.randint(18, 45)
        self.phase = random.uniform(0, math.tau)

    def update(self):
        self.x += self.speed
        if self.x > W + self.w:
            self.x = -self.w - random.uniform(0, 200)


class Star:
    def __init__(self):
        self.x = random.uniform(0, W)
        self.y = random.uniform(0, H * 0.55)
        self.r = random.uniform(0.5, 1.8)
        self.phase = random.uniform(0, math.tau)
        self.speed = random.uniform(0.8, 2.2)
        self.base_bright = random.randint(130, 220)

    def color(self, t):
        v = 0.5 + 0.5 * math.sin(t * self.speed + self.phase)
        b = int(self.base_bright * v)
        return f"#{b:02x}{b:02x}{min(255, b+18):02x}"


root = tk.Tk()
root.title("Emberveil")
root.resizable(False, False)
root.configure(bg=C_BG)

# Center on screen
sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()
root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

canvas = tk.Canvas(root, width=W, height=H, bg=C_BG,
                   highlightthickness=0)
canvas.pack()

def build_static_bg():
    # Sky gradient — top dark navy → horizon teal-green
    bands = 14
    for i in range(bands):
        f = i / (bands - 1)
        r = int(4  + f * 10)
        g = int(8  + f * 23)
        b = int(15 + f * 14)
        y1 = int(f * H)
        y2 = int((f + 1/bands) * H) + 2
        canvas.create_rectangle(0, y1, W, y2,
            fill=f"#{r:02x}{g:02x}{b:02x}", outline="")

    # Moon — upper left, slightly off-center for asymmetry
    MX, MY, MR = 155, 105, 42
    for halo_r, halo_alpha in [(MR*2.8, "#04080F"), (MR*2.0, "#060C15"),
                                (MR*1.5, "#09141F")]:
        canvas.create_oval(MX-halo_r, MY-halo_r, MX+halo_r, MY+halo_r,
            fill=halo_alpha, outline="")
    canvas.create_oval(MX-MR, MY-MR, MX+MR, MY+MR, fill=C_MOON, outline="")
    # Moon shadow (crescent effect)
    canvas.create_oval(MX-MR+9, MY-MR-6, MX+MR+9, MY+MR-6,
        fill="#D0DCFF", outline="")

    # Treeline silhouette — layered depth
    def treeline(seed, y_base, h_range, step_range, color):
        random.seed(seed)
        pts = [0, H]
        x = 0
        while x <= W + 40:
            pts += [x, y_base - random.randint(*h_range)]
            x += random.randint(*step_range)
        pts += [W, H]
        canvas.create_polygon(*pts, fill=color, outline="")
        random.seed()  # reset

    treeline(42,  H-10, (5, 70),  (8, 32),  "#020B05")  # far back
    treeline(77,  H-5,  (10, 90), (10, 38), "#010804")  # mid
    treeline(13,  H,    (15, 110),(12, 42), "#010603")  # close

    # Ground glow — warm ember light from below
    for i in range(6):
        f = i / 5
        yy = H - 60 + int(f * 60)
        rv = int(f * 28)
        gv = int(f * 12)
        canvas.create_rectangle(0, yy, W, yy + 14,
            fill=f"#{rv:02x}{gv:02x}00", outline="")

build_static_bg()

stars = [Star() for _ in range(160)]
star_ids = []
for s in stars:
    sid = canvas.create_oval(s.x-s.r, s.y-s.r, s.x+s.r, s.y+s.r,
        fill="#888888", outline="")
    star_ids.append(sid)

# Mist layers
mist_layers = [
    MistLayer(H * 0.72, 0.18, 0.4, random.randint(180, 320))
    for _ in range(7)
]
mist_ids = []
for _ in mist_layers:
    mid = canvas.create_rectangle(0, 0, 1, 1, fill=C_MIST, outline="", state="hidden")
    mist_ids.append(mid)

# Embers
embers = [Ember() for _ in range(55)]
ember_ids = []
for _ in embers:
    eid = canvas.create_oval(0, 0, 1, 1, fill=C_EMBER, outline="")
    ember_ids.append(eid)


# Decorative horizontal rules
canvas.create_line(W//2 - 180, H//2 - 68, W//2 + 180, H//2 - 68,
    fill=C_RULE, width=1)
canvas.create_line(W//2 - 80,  H//2 + 52, W//2 + 80,  H//2 + 52,
    fill=C_RULE, width=1)

# Tiny icon above title
canvas.create_text(W//2, H//2 - 85, text="✦",
    fill=C_EMBER, font=("Georgia", 11))

# Title — main
title_shadow = canvas.create_text(W//2 + 2, H//2 - 36 + 2,
    text="Emberveil",
    fill="#200800", font=FONT_TITLE)
title_id = canvas.create_text(W//2, H//2 - 36,
    text="Emberveil",
    fill=C_TITLE, font=FONT_TITLE)

# Subtitle
sub_id = canvas.create_text(W//2, H//2 + 12,
    text="where the embers never sleep",
    fill=C_SUBTITLE, font=FONT_SUB)

# ── Animated title glow (updated in loop) ──
title_glow_id = canvas.create_text(W//2, H//2 - 36,
    text="Emberveil",
    fill=C_BG, font=FONT_TITLE)   # starts as bg color (invisible)


BTN_Y_START = H // 2 + 72
BTN_GAP     = 46

class EmberButton(tk.Button):
    """Hand-crafted button matching the Emberveil aesthetic."""
    def __init__(self, master, text, command, accent=False):
        super().__init__(master,
            text=text, command=command,
            bg=C_BG, fg=C_BTN_FG if not accent else C_EMBER,
            activebackground="#0E1A10",
            activeforeground=C_EMBER,
            font=FONT_BTN,
            relief="flat", bd=0,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=C_RULE,
            width=20, pady=10,
        )
        self._accent = accent
        self._hovered = False
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)

    def _enter(self, _=None):
        self._hovered = True
        self.config(
            bg="#0B1810",
            fg=C_BTN_HLT,
            highlightbackground=C_EMBER,
        )
        sfx("hover")

    def _leave(self, _=None):
        self._hovered = False
        self.config(
            bg=C_BG,
            fg=C_BTN_FG if not self._accent else C_EMBER,
            highlightbackground=C_RULE,
        )

def start_game():
    sfx("click")
    stop_ambient()
    root.after(180, lambda: (root.destroy(),
        __import__('subprocess').call([sys.executable, "game.py"])))

def exit_game():
    sfx("click")
    stop_ambient()
    root.after(150, root.destroy)

btn_start = EmberButton(root, text="✦  Enter the Veil", command=start_game, accent=True)
btn_start.place(relx=0.5, rely=0.0, anchor="n",
    x=0, y=BTN_Y_START)

btn_exit = EmberButton(root, text="    Leave",         command=exit_game)
btn_exit.place(relx=0.5, rely=0.0, anchor="n",
    x=0, y=BTN_Y_START + BTN_GAP)

# ── Version / Footer ──
canvas.create_text(W//2, H - 18,
    text="v1.0  ·  use the light  ·  find the veil",
    fill=C_FOOTER, font=FONT_HINT)

# ── Small ember icon flanking title ──
canvas.create_text(W//2 - 112, H//2 - 36, text="⋅", fill="#5A3010", font=("Georgia", 18))
canvas.create_text(W//2 + 112, H//2 - 36, text="⋅", fill="#5A3010", font=("Georgia", 18))

fade_overlay = canvas.create_rectangle(0, 0, W, H, fill="#000000", outline="")
fade_alpha   = 1.0      # 1.0 = black, 0.0 = fully visible
reveal_done  = False

STIPPLE_STEPS = [
    (1.00, ""),
    (0.85, "gray75"),
    (0.65, "gray50"),
    (0.40, "gray25"),
    (0.15, "gray12"),
    (0.00, None),       # None = remove overlay
]
fade_step = 0
fade_start = time.time()

def advance_fade():
    global fade_step, reveal_done
    if fade_step >= len(STIPPLE_STEPS):
        canvas.delete(fade_overlay)
        reveal_done = True
        return
    threshold, stipple = STIPPLE_STEPS[fade_step]
    if stipple is None:
        canvas.delete(fade_overlay)
        reveal_done = True
        return
    elif stipple == "":
        canvas.itemconfig(fade_overlay, fill="#000000", stipple="")
    else:
        canvas.itemconfig(fade_overlay, fill="#000000", stipple=stipple)
    fade_step += 1
    root.after(320, advance_fade)

root.after(200, advance_fade)

frame = 0

def loop():
    global frame
    frame += 1
    t = time.time()

    # Stars twinkle
    if frame % 3 == 0:
        for i, s in enumerate(stars):
            canvas.itemconfig(star_ids[i], fill=s.color(t))

    # Mist drift
    for i, m in enumerate(mist_layers):
        m.update()
        wave_h = m.h + int(math.sin(t * 0.4 + m.phase) * 5)
        canvas.coords(mist_ids[i],
            m.x, m.y, m.x + m.w, m.y + wave_h)
        # subtle teal-grey mist
        rv = int(10 + math.sin(t * 0.3 + m.phase) * 3)
        canvas.itemconfig(mist_ids[i],
            fill=f"#{rv:02x}{rv+8:02x}{rv+12:02x}",
            state="normal")

    # Embers
    for i, e in enumerate(embers):
        e.update()
        gr = e.r * (1.5 + 0.5 * (e.life / e.max_life))
        canvas.coords(ember_ids[i],
            e.x - gr, e.y - gr, e.x + gr, e.y + gr)
        canvas.itemconfig(ember_ids[i], fill=e.color)

    # Title glow pulse
    glow_v = abs(math.sin(t * 1.2))  # always 0..1, never negative
    r_glow = max(0, min(255, int(90 * glow_v)))
    g_glow = max(0, min(255, int(35 * glow_v)))
    glow_col = f"#{r_glow:02x}{g_glow:02x}00"
    canvas.itemconfig(title_glow_id, fill=glow_col)

    # Subtitle fade-shimmer
    sv = 0.65 + 0.35 * math.sin(t * 0.7 + 1.0)
    sr = max(0, min(255, int(90 * sv)))
    sg = max(0, min(255, int(128 * sv)))
    sb = max(0, min(255, int(144 * sv)))
    canvas.itemconfig(sub_id, fill=f"#{sr:02x}{sg:02x}{sb:02x}")

    # Ensure overlay stays on top during fade
    if not reveal_done:
        canvas.tag_raise(fade_overlay)

    root.after(28, loop)

start_ambient()
loop()
root.mainloop()