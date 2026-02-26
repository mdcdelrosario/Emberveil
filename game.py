import tkinter as tk
from tkinter import font as tkfont
import random, math, time, os, wave, struct, threading, subprocess, sys, tempfile
import numpy as np

SAMPLE_RATE = 44100
TMP_DIR = tempfile.mkdtemp()

def _write_wav(path, samples):
    samples = np.clip(samples, -1, 1)
    data = (samples * 32767).astype(np.int16)
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(data.tobytes())

def _sine(freq, dur, amp=0.5, sr=SAMPLE_RATE):
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    return amp * np.sin(2 * np.pi * freq * t)

def _envelope(sig, attack=0.01, release=0.1):
    n = len(sig)
    env = np.ones(n)
    a = int(SAMPLE_RATE * attack)
    r = int(SAMPLE_RATE * release)
    if a > 0: env[:a] = np.linspace(0, 1, a)
    if r > 0 and r <= n: env[-r:] = np.linspace(1, 0, r)
    return sig * env

def _mix(*arrays):
    """Add arrays of potentially different lengths by zero-padding shorter ones."""
    n = max(len(a) for a in arrays)
    out = np.zeros(n)
    for a in arrays:
        out[:len(a)] += a
    return out

def gen_ambient():
    """Soft looping night-veil drone: layered sine pads + slow shimmer."""
    dur = 12.0
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    # Pad chord: A2, E3, A3, C#4
    freqs = [110, 164.81, 220, 277.18]
    amps  = [0.18, 0.12, 0.10, 0.07]
    sig = np.zeros_like(t)
    for f, a in zip(freqs, amps):
        # slight detune for warmth
        sig += a * np.sin(2 * np.pi * f * t)
        sig += a * 0.4 * np.sin(2 * np.pi * (f * 1.003) * t)
    # slow shimmer LFO
    lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.15 * t)
    sig *= lfo
    # soft attack/fade for looping
    fade = 1024
    sig[:fade] *= np.linspace(0, 1, fade)
    sig[-fade:] *= np.linspace(1, 0, fade)
    _write_wav(os.path.join(TMP_DIR, "ambient.wav"), sig * 0.55)

def gen_sparkle():
    """Short bright chime: rising sine with fast decay."""
    dur = 0.45
    freq = random.choice([880, 1046, 1318, 1568])
    sig = _mix(_sine(freq, dur, 0.6), _sine(freq * 2, dur, 0.2))
    sig = _envelope(sig, attack=0.005, release=0.35)
    _write_wav(os.path.join(TMP_DIR, "sparkle.wav"), sig)

def gen_zone_charge():
    """Ascending arpeggio when a zone charges."""
    notes = [523, 659, 784, 1046]
    chunks = []
    for n in notes:
        s = _sine(n, 0.12, 0.5)
        s = _envelope(s, 0.01, 0.07)
        chunks.append(s)
    sig = np.concatenate(chunks)
    _write_wav(os.path.join(TMP_DIR, "zone_charge.wav"), sig)

def gen_flower():
    """Soft bloom: descending bell."""
    dur = 0.5
    s1 = _sine(1046, dur, 0.4)
    s2 = _sine(1318, dur, 0.3)   # same duration — pad avoided
    # fade s2 out faster by multiplying a short decay envelope
    fade = np.ones(len(s2))
    half = len(s2) // 2
    fade[half:] = np.linspace(1, 0, len(s2) - half)
    sig = s1 + s2 * fade
    sig = _envelope(sig, 0.005, 0.4)
    _write_wav(os.path.join(TMP_DIR, "flower.wav"), sig)

def gen_cleanse():
    """Dark-to-light sweep."""
    dur = 0.6
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur), endpoint=False)
    freq_sweep = np.linspace(200, 900, len(t))
    sig = 0.5 * np.sin(2 * np.pi * np.cumsum(freq_sweep) / SAMPLE_RATE)
    sig = _envelope(sig, 0.01, 0.3)
    _write_wav(os.path.join(TMP_DIR, "cleanse.wav"), sig)

def gen_stage_complete():
    """Triumphant chord hit."""
    dur = 1.2
    chord = [523, 659, 784, 1046]
    sig = np.zeros(int(SAMPLE_RATE * dur))
    for f in chord:
        s = _sine(f, dur, 0.3)
        s = _envelope(s, 0.01, 0.6)
        sig += s
    _write_wav(os.path.join(TMP_DIR, "stage_done.wav"), sig * 0.7)

def gen_victory():
    """Full harmony fanfare."""
    sig = np.array([])
    melody = [523, 659, 784, 880, 1046, 880, 784, 659, 523*2]
    for note in melody:
        chunk = _mix(_sine(note, 0.18, 0.45), _sine(note*1.5, 0.18, 0.2))
        chunk = _envelope(chunk, 0.01, 0.08)
        sig = np.concatenate([sig, chunk])
    pad = _sine(262, len(sig)/SAMPLE_RATE, 0.2)
    sig = sig + pad[:len(sig)]
    _write_wav(os.path.join(TMP_DIR, "victory.wav"), sig)

def gen_timeout():
    """Sad descending tone."""
    notes = [523, 440, 370, 294]
    chunks = [_envelope(_sine(n, 0.3, 0.4), 0.01, 0.2) for n in notes]
    _write_wav(os.path.join(TMP_DIR, "timeout.wav"), np.concatenate(chunks))

# Pre-generate all sounds
print("Generating audio assets…")
gen_ambient(); gen_zone_charge(); gen_flower()
gen_cleanse(); gen_stage_complete(); gen_victory(); gen_timeout()
gen_sparkle()
print("Audio ready.")

# ── Playback ──────────────────────────────────
_ambient_proc = None
_sfx_lock = threading.Lock()

def _play_file(path, loop=False):
    plt = sys.platform
    if plt == "win32":
        import winsound
        flags = winsound.SND_FILENAME | winsound.SND_ASYNC
        if loop: flags |= winsound.SND_LOOP
        winsound.PlaySound(path, flags)
        return None
    elif plt == "darwin":
        cmd = ["afplay", path]
    else:
        cmd = ["aplay", "-q", path]
    try:
        return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        return None

def start_ambient():
    global _ambient_proc
    def _loop():
        global _ambient_proc
        while not game_over:
            _ambient_proc = _play_file(os.path.join(TMP_DIR, "ambient.wav"))
            if _ambient_proc:
                _ambient_proc.wait()
            else:
                time.sleep(12)
    t = threading.Thread(target=_loop, daemon=True)
    t.start()

def play_sfx(name):
    def _go():
        with _sfx_lock:
            _play_file(os.path.join(TMP_DIR, f"{name}.wav"))
    threading.Thread(target=_go, daemon=True).start()

WIDTH, HEIGHT   = 1100, 680
PANEL_W         = 260          # right-side task panel
CANVAS_W        = WIDTH - PANEL_W
TIME_LIMIT      = 360

# Night palette
BG_SKY   = "#030C18"
BG_MID   = "#06121F"
BG_GND   = "#040D0A"
C_MOON   = "#EEF4FF"
C_FLY    = "#FFFAAA"
C_FLY_DIM= "#665500"
C_ZONE   = "#3A86FF"
C_HEART  = "#00FFAA"
C_DARK   = "#0A040F"
C_DARK_G = "#3A005A"
C_FLOWER = ["#FF6B9D","#FFD166","#06D6A0","#F4A261","#C77DFF","#A8DADC"]
C_UI_BG  = "#040E1A"
C_PANEL  = "#050F1C"
C_PANEL_BORDER = "#0D2540"
C_ACCENT = "#FFD166"
C_TEXT   = "#8BB8D8"
C_WHITE  = "#E8F4FF"

# Task definitions
STAGES = [
    {
        "title": "Charge the Zones",
        "icon": "◈",
        "color": "#3A86FF",
        "hint": "Attract fireflies into the\nglowing blue rings. Hold\nthem inside to charge.",
        "steps": ["Zone 1 charged", "Zone 2 charged", "Zone 3 charged"],
        "reward": 30,
    },
    {
        "title": "Awaken the Heart",
        "icon": "✦",
        "color": "#00FFAA",
        "hint": "Guide 8+ fireflies into the\nHeart circle at the center\nof the meadow.",
        "steps": ["Gather 8 fireflies at Heart"],
        "reward": 40,
    },
    {
        "title": "Bloom Emberblooms",
        "icon": "❀",
        "color": "#FF6B9D",
        "hint": "Right-click anywhere to\nplant emberblooms and\nrestore color. Plant 5.",
        "steps": ["Plant 5 emberblooms"],
        "reward": 30,
    },
    {
        "title": "Cleanse the Shadows",
        "icon": "☽",
        "color": "#C77DFF",
        "hint": "Left-click shadow patches\nto purify them. Some need\nmultiple clicks.",
        "steps": ["Destroy all 5 shadow patches"],
        "reward": 50,
    },
    {
        "title": "Harmony Ritual",
        "icon": "⊕",
        "color": "#FFD166",
        "hint": "Final task — summon\n15 fireflies into the Heart\nfor the Harmony Ritual.",
        "steps": ["Summon 15 fireflies to Heart"],
        "reward": 100,
    },
]

stage        = 0
fireflies    = []
flowers      = []
dark_spots   = []
zones        = []
particles    = []
score        = 0
combo        = 0
combo_timer  = 0
game_over    = False
start_time   = time.time()
frame        = 0
mouse_pos    = None
step_done    = [False] * 3   # per-stage step completion
stars_data   = []
pid_pool     = []
sparkle_gen  = 0

def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    r1,g1,b1 = int(c1[1:3],16),int(c1[3:5],16),int(c1[5:7],16)
    r2,g2,b2 = int(c2[1:3],16),int(c2[3:5],16),int(c2[5:7],16)
    return "#{:02x}{:02x}{:02x}".format(
        int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))

def dist(x1,y1,x2,y2): return math.hypot(x1-x2, y1-y2)

def burst(x, y, color, n=14, spread=4):
    for _ in range(n):
        ang = random.uniform(0, math.tau)
        spd = random.uniform(1, spread)
        particles.append(Particle(x, y, color,
            vx=math.cos(ang)*spd, vy=math.sin(ang)*spd,
            life=random.randint(25,55), r=random.uniform(1.5,3.5)))

class Particle:
    __slots__ = ('x','y','vx','vy','life','max_life','r','color')
    def __init__(self, x, y, color, vx=0, vy=0, life=30, r=2):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.r = r
        self.color = color
    def update(self):
        self.x += self.vx; self.y += self.vy
        self.vy += 0.05; self.vx *= 0.97
        self.life -= 1
        return self.life > 0
class Firefly:
    def __init__(self, canvas):
        self.canvas = canvas
        self.x = random.uniform(60, CANVAS_W-60)
        self.y = random.uniform(60, HEIGHT-60)
        self.r = random.uniform(3, 5)
        self.dx = random.uniform(-0.6, 0.6)
        self.dy = random.uniform(-0.6, 0.6)
        self.phase = random.uniform(0, math.tau)
        self.spd = random.uniform(0.7, 1.3)
        self.glow = canvas.create_oval(0,0,1,1, fill="#332200", outline="")
        self.body = canvas.create_oval(0,0,1,1, fill=C_FLY, outline="")

    def move(self, target=None):
        if target and target[0] < CANVAS_W:
            ang = math.atan2(target[1]-self.y, target[0]-self.x)
            self.dx += math.cos(ang) * 0.09 * self.spd
            self.dy += math.sin(ang) * 0.09 * self.spd
        self.dx += random.uniform(-0.04, 0.04)
        self.dy += random.uniform(-0.04, 0.04)
        spd = math.hypot(self.dx, self.dy)
        if spd > 2.8: self.dx, self.dy = self.dx*2.8/spd, self.dy*2.8/spd
        self.x += self.dx; self.y += self.dy
        self.dx *= 0.96; self.dy *= 0.96
        if self.x < 50:  self.dx += 0.15
        if self.x > CANVAS_W-50: self.dx -= 0.15
        if self.y < 50:  self.dy += 0.15
        if self.y > HEIGHT-50: self.dy -= 0.15

    def draw(self, t):
        v = 0.65 + 0.35 * math.sin(t * 3.2 + self.phase)
        ri, gi = int(255*v), int(245*v)
        bi = max(0, int(80*v - 40))
        col = f"#{ri:02x}{gi:02x}{bi:02x}"
        gv  = v * 0.35
        gr, gg = int(100*gv), int(80*gv)
        gcol = f"#{gr:02x}{gg:02x}00"
        gr2 = self.r * 3.8
        self.canvas.coords(self.glow,
            self.x-gr2, self.y-gr2, self.x+gr2, self.y+gr2)
        self.canvas.itemconfig(self.glow, fill=gcol)
        self.canvas.coords(self.body,
            self.x-self.r, self.y-self.r,
            self.x+self.r, self.y+self.r)
        self.canvas.itemconfig(self.body, fill=col)

class Zone:
    def __init__(self, canvas, x, y, r=50):
        self.canvas = canvas
        self.x, self.y = x, y
        self.r = r
        self.charge = 0.0
        self.full = False
        self.pulse = random.uniform(0, math.tau)
        self.ring2 = canvas.create_oval(0,0,1,1, outline="#0A1E3A", width=1)
        self.fill  = canvas.create_oval(0,0,1,1, fill="", outline="")
        self.ring  = canvas.create_oval(0,0,1,1, outline=C_ZONE, width=2)
        self.pct   = canvas.create_text(x, y, text="", fill=C_TEXT, font=("Courier",9))

    def update(self, flies):
        inside = sum(1 for f in flies if dist(f.x,f.y,self.x,self.y) < self.r)
        if inside > 0 and not self.full:
            prev = self.charge
            self.charge = min(1.0, self.charge + 0.004 * inside)
            if self.charge >= 1.0 and prev < 1.0:
                self.full = True
                play_sfx("zone_charge")
                burst(self.x, self.y, C_ZONE, 18)
        elif not self.full:
            self.charge = max(0.0, self.charge - 0.0008)

    def draw(self, t):
        p  = 0.88 + 0.12 * math.sin(t * 2.1 + self.pulse)
        r  = self.r * p
        r2 = self.r * 1.35 * p
        if self.full:
            col, fill_col = C_HEART, "#002A1A"
        else:
            col = lerp_color("#1A4A7A", C_ZONE, self.charge)
            n = int(self.charge * 40)
            fill_col = f"#{n//2:02x}{n:02x}{min(60,n*2):02x}"
        self.canvas.coords(self.ring2, self.x-r2,self.y-r2,self.x+r2,self.y+r2)
        self.canvas.itemconfig(self.ring2, outline=lerp_color("#040E1A",col,0.4))
        self.canvas.coords(self.fill, self.x-r+2,self.y-r+2,self.x+r-2,self.y+r-2)
        self.canvas.itemconfig(self.fill, fill=fill_col)
        self.canvas.coords(self.ring, self.x-r,self.y-r,self.x+r,self.y+r)
        self.canvas.itemconfig(self.ring, outline=col, width=2)
        if self.full:
            self.canvas.itemconfig(self.pct, text="✓", fill=C_HEART)
        else:
            self.canvas.itemconfig(self.pct, text=f"{int(self.charge*100)}%", fill=C_TEXT)

class DarkSpot:
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.x, self.y = x, y
        self.base_r = random.randint(30, 46)
        self.r = self.base_r
        self.hp = 3
        self.pulse = random.uniform(0, math.tau)
        self.g2 = canvas.create_oval(0,0,1,1, fill=C_DARK_G, outline="")
        self.b  = canvas.create_oval(0,0,1,1, fill=C_DARK, outline="")
        self._draw()

    def _draw(self):
        gr = self.r * 1.7
        self.canvas.coords(self.g2, self.x-gr,self.y-gr,self.x+gr,self.y+gr)
        self.canvas.coords(self.b,  self.x-self.r,self.y-self.r,
                                    self.x+self.r,self.y+self.r)

    def hit(self):
        self.hp -= 1
        self.r = int(self.base_r * (self.hp / 3))
        self._draw()
        if self.hp <= 0:
            self.canvas.delete(self.g2); self.canvas.delete(self.b)
            return True
        play_sfx("cleanse")
        return False

    def contains(self, ex, ey): return dist(ex,ey,self.x,self.y) < self.r


root = tk.Tk()
root.title("✦ Emberveil ✦")
root.geometry(f"{WIDTH}x{HEIGHT}")
root.resizable(False, False)
root.configure(bg="#000000")

# Main game canvas (left)
canvas = tk.Canvas(root, bg=BG_SKY, highlightthickness=0,
                   width=CANVAS_W, height=HEIGHT)
canvas.place(x=0, y=0)

# Panel canvas (right)
panel = tk.Canvas(root, bg=C_PANEL, highlightthickness=0,
                  width=PANEL_W, height=HEIGHT)
panel.place(x=CANVAS_W, y=0)


def build_background():
    # Sky gradient
    for i in range(10):
        f = i / 9
        r = int(3 + f*8)
        g = int(12 + f*16)
        b = int(24 + f*10)
        canvas.create_rectangle(0, int(f*(HEIGHT-60)), CANVAS_W,
            int((f+0.12)*(HEIGHT+40)),
            fill=f"#{r:02x}{g:02x}{b:02x}", outline="")
    # Stars
    for _ in range(200):
        sx, sy = random.randint(0,CANVAS_W), random.randint(0, HEIGHT-80)
        sr = random.uniform(0.5, 1.8)
        brt = random.randint(140,255)
        sc = f"#{brt:02x}{brt:02x}{min(255,brt+15):02x}"
        sid = canvas.create_oval(sx-sr,sy-sr,sx+sr,sy+sr, fill=sc, outline="")
        stars_data.append((sid, sx, sy, sr, random.uniform(0, math.tau)))
    # Moon
    MX, MY, MR = CANVAS_W-95, 85, 38
    canvas.create_oval(MX-MR*1.9,MY-MR*1.9,MX+MR*1.9,MY+MR*1.9, fill="#030D1C", outline="")
    canvas.create_oval(MX-MR*1.4,MY-MR*1.4,MX+MR*1.4,MY+MR*1.4, fill="#0A1D30", outline="")
    canvas.create_oval(MX-MR,MY-MR,MX+MR,MY+MR, fill=C_MOON, outline="")
    canvas.create_oval(MX+10-MR*0.38,MY-10-MR*0.38,
                       MX+10+MR*0.38,MY-10+MR*0.38, fill="#D4E8FF", outline="")
    # Tree silhouette
    pts = []
    tx = 0
    while tx <= CANVAS_W+30:
        pts += [tx, HEIGHT - random.randint(8, 60)]
        tx += random.randint(10, 38)
    pts += [CANVAS_W, HEIGHT, 0, HEIGHT]
    canvas.create_polygon(*pts, fill="#020B05", outline="")
    # Ground strip
    for i in range(5):
        f = i / 4
        yy = HEIGHT - 58 + int(f * 58)
        gv = int(f * 16)
        canvas.create_rectangle(0, yy, CANVAS_W, yy+14,
            fill=f"#00{gv:02x}00", outline="")

build_background()

HX, HY, HR = CANVAS_W // 2, HEIGHT // 2 + 15, 68
heart_ring   = canvas.create_oval(HX-HR,HY-HR,HX+HR,HY+HR, outline="#152A3A", width=2)
heart_inner  = canvas.create_oval(HX-HR//2,HY-HR//2,HX+HR//2,HY+HR//2,
                                   outline="#0D1E2E", width=1)
heart_label  = canvas.create_text(HX, HY+HR+16, text="Heart of the Veil",
    fill="#1A3A5C", font=("Georgia", 9, "italic"))

status_bg = canvas.create_rectangle(0,0,1,1, fill="#000814", outline="", state="hidden")
status_id = canvas.create_text(CANVAS_W//2, HY-HR-40, text="",
    fill=C_ACCENT, font=("Georgia", 14, "bold"), state="hidden")

def show_status(msg, color=C_ACCENT):
    canvas.itemconfig(status_id, text=msg, fill=color, state="normal")
    tw = len(msg) * 8 + 24
    canvas.coords(status_bg,
        CANVAS_W//2-tw//2, HY-HR-56,
        CANVAS_W//2+tw//2, HY-HR-24)
    canvas.itemconfig(status_bg, state="normal")
    root.after(2400, lambda: (
        canvas.itemconfig(status_id, state="hidden"),
        canvas.itemconfig(status_bg, state="hidden")
    ))

# cursor ring
cursor_ring = canvas.create_oval(0,0,1,1, outline=C_ACCENT, width=1)
cursor_dot  = canvas.create_oval(0,0,1,1, fill=C_ACCENT, outline="")

def build_panel():
    p = panel

    # Header
    p.create_rectangle(0, 0, PANEL_W, HEIGHT, fill=C_PANEL, outline="")
    p.create_line(0, 0, 0, HEIGHT, fill=C_PANEL_BORDER, width=2)
    p.create_rectangle(0, 0, PANEL_W, 52, fill="#040C18", outline="")
    p.create_text(PANEL_W//2, 26, text="✦  Emberveil Journal  ✦",
        fill=C_ACCENT, font=("Georgia", 11, "bold"))
    p.create_line(10, 52, PANEL_W-10, 52, fill=C_PANEL_BORDER, width=1)

    # Score / timer block
    p.create_rectangle(10, 58, PANEL_W-10, 110, fill="#050F1A",
        outline=C_PANEL_BORDER)

build_panel()

# Dynamic panel items
panel_score  = panel.create_text(PANEL_W//2, 74, text="Score  0",
    fill=C_HEART, font=("Courier", 13, "bold"))
panel_timer  = panel.create_text(PANEL_W//2, 95, text="6:00",
    fill=C_ACCENT, font=("Courier", 12, "bold"))

# Divider
panel.create_line(10, 116, PANEL_W-10, 116, fill=C_PANEL_BORDER)

# Active task box
panel.create_rectangle(10, 122, PANEL_W-10, 290, fill="#040C18",
    outline=C_PANEL_BORDER)
task_icon_id    = panel.create_text(26, 140, text="◈",
    fill=C_ZONE, font=("Arial", 14, "bold"))
task_title_id   = panel.create_text(44, 140, anchor="w", text="Charge the Zones",
    fill=C_WHITE, font=("Georgia", 10, "bold"))
task_hint_id    = panel.create_text(PANEL_W//2, 176, text="",
    fill=C_TEXT, font=("Georgia", 9, "italic"), width=PANEL_W-30, justify="center")
task_reward_id  = panel.create_text(PANEL_W//2, 225, text="Reward: +30 pts",
    fill="#7A5A00", font=("Courier", 9))

# Step checklist (3 items max)
step_ids = []
for i in range(3):
    yx = 240 + i * 18
    chk = panel.create_text(22, yx, text="○", fill="#3A5A7A", font=("Courier",9))
    lbl = panel.create_text(35, yx, anchor="w", text="",
        fill=C_TEXT, font=("Georgia", 9), width=PANEL_W-45)
    step_ids.append((chk, lbl))

# Progress bar
panel.create_rectangle(10, 292, PANEL_W-10, 306, fill="#060F1A", outline=C_PANEL_BORDER)
progress_bar = panel.create_rectangle(10, 292, 10, 306, fill=C_ZONE, outline="")

# Divider
panel.create_line(10, 312, PANEL_W-10, 312, fill=C_PANEL_BORDER)

# Stage list (all stages, small)
panel.create_text(PANEL_W//2, 322, text="— All Tasks —",
    fill="#1A3A5C", font=("Georgia", 8, "italic"))
stage_labels = []
for i, s in enumerate(STAGES):
    y = 336 + i * 22
    icon_id = panel.create_text(20, y, text=s["icon"],
        fill="#1A3050", font=("Arial", 9))
    name_id = panel.create_text(32, y, anchor="w", text=s["title"],
        fill="#1A3050", font=("Georgia", 8), width=PANEL_W-40)
    stage_labels.append((icon_id, name_id))

# Divider
panel.create_line(10, 452, PANEL_W-10, 452, fill=C_PANEL_BORDER)

# Combo display
combo_bg  = panel.create_rectangle(10, 458, PANEL_W-10, 486,
    fill="#060A10", outline=C_PANEL_BORDER)
combo_lbl = panel.create_text(PANEL_W//2, 471, text="",
    fill="#FF6B9D", font=("Courier", 12, "bold"))

# Controls reference
panel.create_line(10, 492, PANEL_W-10, 492, fill=C_PANEL_BORDER)
panel.create_text(PANEL_W//2, 502, text="Controls",
    fill="#1A3A5C", font=("Georgia", 8, "bold"))
controls = [
    ("Left-click", "Attract fireflies / Cleanse"),
    ("Right-click","Plant emberbloom"),
    ("Drag",       "Continuously attract"),
]
for i,(k,v) in enumerate(controls):
    y = 516 + i * 16
    panel.create_text(16, y, anchor="w", text=f"▸ {k}",
        fill=C_ACCENT, font=("Courier", 7, "bold"))
    panel.create_text(90, y, anchor="w", text=v,
        fill=C_TEXT, font=("Georgia", 7))

# Exit button
exit_btn = tk.Button(panel, text="✕  EXIT", fg=C_TEXT, bg="#06101A",
    font=("Courier", 9, "bold"), borderwidth=0, relief="flat",
    activebackground="#1A3050", activeforeground="white",
    command=root.destroy, cursor="hand2")
exit_btn.place(x=PANEL_W//2-35, y=HEIGHT-34, width=70, height=24)

# ── Panel update function ──────────────────────
def refresh_panel():
    s = STAGES[min(stage, len(STAGES)-1)]

    # Active task card
    panel.itemconfig(task_icon_id, text=s["icon"], fill=s["color"])
    panel.itemconfig(task_title_id, text=f"Task {stage+1}  ·  {s['title']}", fill=s["color"])
    panel.itemconfig(task_hint_id,  text=s["hint"])
    panel.itemconfig(task_reward_id, text=f"Reward: +{s['reward']} pts")

    # Steps
    raw_steps = s["steps"]
    for i, (chk, lbl) in enumerate(step_ids):
        if i < len(raw_steps):
            done = step_done[i] if i < len(step_done) else False
            panel.itemconfig(chk, text="●" if done else "○",
                fill=C_HEART if done else "#3A5A7A")
            panel.itemconfig(lbl, text=raw_steps[i],
                fill=C_HEART if done else C_TEXT)
        else:
            panel.itemconfig(chk, text="")
            panel.itemconfig(lbl, text="")

    # Stage list highlight
    for i, (icon_id, name_id) in enumerate(stage_labels):
        if i < stage:
            panel.itemconfig(icon_id, fill="#2A6A4A")
            panel.itemconfig(name_id, fill="#2A6A4A")
        elif i == stage:
            panel.itemconfig(icon_id, fill=s["color"])
            panel.itemconfig(name_id, fill=C_WHITE)
        else:
            panel.itemconfig(icon_id, fill="#152030")
            panel.itemconfig(name_id, fill="#152030")

    # Progress bar
    pct = stage / len(STAGES)
    panel.coords(progress_bar, 10, 292, 10 + int((PANEL_W-20)*pct), 306)
    col = lerp_color(C_ZONE, C_HEART, pct)
    panel.itemconfig(progress_bar, fill=col)

def spawn_zones():
    positions = [(200, 200), (CANVAS_W-180, 200), (CANVAS_W//2, HEIGHT-170)]
    for (x,y) in positions:
        zones.append(Zone(canvas, x, y))

def spawn_dark():
    for _ in range(5):
        x = random.randint(120, CANVAS_W-120)
        y = random.randint(100, HEIGHT-120)
        dark_spots.append(DarkSpot(canvas, x, y))

def draw_particles():
    global particles
    for pid in pid_pool:
        try: canvas.delete(pid)
        except: pass
    pid_pool.clear()
    alive = []
    for p in particles:
        if p.update() and 0 < p.x < CANVAS_W and 0 < p.y < HEIGHT:
            alive.append(p)
            a = p.life / p.max_life
            r2 = max(0.5, p.r * a)
            pid_pool.append(
                canvas.create_oval(p.x-r2,p.y-r2,p.x+r2,p.y+r2,
                    fill=p.color, outline=""))
    particles = alive
    
def twinkle_stars(t):
    for (sid, sx, sy, sr, phase) in stars_data:
        v = 0.45 + 0.55 * math.sin(t * 1.4 + phase)
        b = int(100 + 155 * v)
        col = f"#{b:02x}{b:02x}{min(255,b+20):02x}"
        canvas.itemconfig(sid, fill=col)

def animate_heart(t):
    p  = 0.90 + 0.10 * math.sin(t * 1.9)
    r  = HR * p
    r2 = HR * 0.44 * p
    prog = stage / max(1, len(STAGES) - 1)
    col = lerp_color("#152A3A", C_HEART, prog)
    canvas.coords(heart_ring, HX-r,HY-r,HX+r,HY+r)
    canvas.coords(heart_inner,HX-r2,HY-r2,HX+r2,HY+r2)
    canvas.itemconfig(heart_ring, outline=col, width=2)
    canvas.itemconfig(heart_inner, outline=lerp_color(col,"#000000",0.6))

def check_tasks():
    global stage, score, step_done, game_over

    if game_over: return

    if stage == 0:
        full = [z.full for z in zones]
        step_done = full + [False] * max(0, 3 - len(full))
        if all(full):
            _advance(0)

    elif stage == 1:
        cnt = sum(1 for f in fireflies if dist(f.x,f.y,HX,HY)<HR)
        step_done = [cnt >= 8, False, False]
        canvas.itemconfig(heart_label,
            text=f"Heart  {cnt} / 8", fill=C_TEXT)
        if cnt >= 8:
            _advance(1)
            spawn_dark()

    elif stage == 2:
        done = len(flowers) >= 5
        step_done = [done, False, False]
        canvas.itemconfig(heart_label,
            text=f"Emberblooms: {len(flowers)} / 5", fill=C_TEXT)
        if done:
            _advance(2)

    elif stage == 3:
        rem = len(dark_spots)
        step_done = [rem == 0, False, False]
        canvas.itemconfig(heart_label,
            text=f"Shadows left: {rem}", fill=C_TEXT)
        if rem == 0:
            _advance(3)

    elif stage == 4:
        cnt = sum(1 for f in fireflies if dist(f.x,f.y,HX,HY)<HR)
        step_done = [cnt >= 15, False, False]
        canvas.itemconfig(heart_label,
            text=f"Heart  {cnt} / 15", fill=C_TEXT)
        if cnt >= 15:
            play_sfx("victory")
            victory()

def _advance(s_idx):
    global stage, score, step_done
    score += STAGES[s_idx]["reward"]
    stage += 1
    step_done = [False, False, False]
    play_sfx("stage_done")
    burst(HX, HY, STAGES[s_idx]["color"], 24)
    show_status(f"✦  {STAGES[s_idx]['title']}  Complete!", STAGES[s_idx]["color"])
    canvas.itemconfig(heart_label, text="Heart of the Veil", fill="#1A3A5C")
    refresh_panel()

def victory():
    global game_over
    game_over = True
    ov = canvas.create_rectangle(0,0,CANVAS_W,HEIGHT, fill="#000814",stipple="gray50")
    for i in range(4):
        root.after(i*150, lambda: burst(
            random.randint(100,CANVAS_W-100),
            random.randint(100,HEIGHT-100), C_HEART, 22, 5))
    canvas.create_text(CANVAS_W//2, HEIGHT//2-60,
        text="✦  EMBERVEIL RESTORED  ✦",
        fill=C_HEART, font=("Georgia", 28, "bold"))
    canvas.create_text(CANVAS_W//2, HEIGHT//2-18,
        text="The embers glow. The darkness sleeps.",
        fill=C_TEXT, font=("Georgia", 13, "italic"))
    canvas.create_text(CANVAS_W//2, HEIGHT//2+22,
        text=f"Final Score  ·  {score}",
        fill=C_ACCENT, font=("Courier", 18, "bold"))
    canvas.create_text(CANVAS_W//2, HEIGHT//2+60,
        text="You brought harmony back to the veil.",
        fill="#3A5A7A", font=("Georgia", 10, "italic"))
    panel.itemconfig(panel_score, text=f"Score  {score}", fill=C_ACCENT)

def timeout():
    global game_over
    game_over = True
    play_sfx("timeout")
    canvas.create_rectangle(0,0,CANVAS_W,HEIGHT, fill="#03060C",stipple="gray75")
    canvas.create_text(CANVAS_W//2, HEIGHT//2-24,
        text="The veil grows dark…", fill="#5A2A7A",
        font=("Georgia", 22, "italic"))
    canvas.create_text(CANVAS_W//2, HEIGHT//2+20,
        text=f"Score: {score}", fill=C_TEXT, font=("Courier", 13))
    canvas.create_text(CANVAS_W//2, HEIGHT//2+50,
        text="The veil awaits. Try again.", fill="#2A3A5A",
        font=("Georgia", 10, "italic"))

def on_move(e):
    global mouse_pos
    if e.x < CANVAS_W: mouse_pos = (e.x, e.y)
    else: mouse_pos = None

def on_press(e):
    global mouse_pos, score, combo, combo_timer
    mouse_pos = (e.x, e.y)
    # Cleanse
    if stage == 3:
        for spot in dark_spots[:]:
            if spot.contains(e.x, e.y):
                burst(spot.x, spot.y, "#C77DFF", 14)
                if spot.hit():
                    dark_spots.remove(spot)
                    score += 15 + combo
                    combo = min(combo+1, 6)
                    combo_timer = 90
                else:
                    score += 4
                break
    # Sparkle on click
    play_sfx("sparkle")
    gen_sparkle()  # regenerate with new freq
    burst(e.x, e.y, C_FLY_DIM, 6, 2)

def on_release(e):
    global mouse_pos
    mouse_pos = None

def on_right(e):
    global score, combo, combo_timer
    if e.x >= CANVAS_W: return
    if stage < 2:
        show_status("Emberblooms unlock at Task 3!", "#3A86FF")
        return
    col = random.choice(C_FLOWER)
    # Draw 6-petal flower
    for i in range(6):
        ang = i * math.tau / 6
        px = e.x + math.cos(ang) * 11
        py = e.y + math.sin(ang) * 11
        canvas.create_oval(px-6,py-6,px+6,py+6, fill=col, outline="")
    # Center
    canvas.create_oval(e.x-4,e.y-4,e.x+4,e.y+4, fill="#FFFAAA", outline="")
    flowers.append((e.x, e.y))
    play_sfx("flower")
    burst(e.x, e.y, col, 10, 3)
    combo = min(combo+1, 6)
    combo_timer = 90
    score += 5 + combo

canvas.bind("<Motion>",           on_move)
canvas.bind("<Button-1>",         on_press)
canvas.bind("<B1-Motion>",        on_move)
canvas.bind("<ButtonRelease-1>",  on_release)
canvas.bind("<Button-3>",         on_right)

def loop():
    global frame, combo, combo_timer
    if game_over:
        draw_particles()
        return
    t  = time.time() - start_time
    frame += 1

    # Timer
    remaining = max(0, TIME_LIMIT - int(t))
    mm, ss = remaining // 60, remaining % 60
    tcol = C_ACCENT if remaining > 30 else "#FF4444"
    panel.itemconfig(panel_timer, text=f"{mm}:{ss:02d}", fill=tcol)
    if remaining == 0:
        timeout(); return

    # Score / combo
    panel.itemconfig(panel_score, text=f"Score  {score}")
    if combo_timer > 0:
        combo_timer -= 1
        panel.itemconfig(combo_lbl, text=f"×{combo}  COMBO", fill="#FF6B9D")
    else:
        combo = max(0, combo-1)
        panel.itemconfig(combo_lbl, text="" if combo == 0 else f"×{combo}", fill="#FF6B9D")

    # Stars
    if frame % 4 == 0: twinkle_stars(t)

    # Zones
    for z in zones:
        z.update(fireflies)
        z.draw(t)

    # Heart
    animate_heart(t)

    # Fireflies + ambient sparks
    for f in fireflies:
        f.move(mouse_pos)
        f.draw(t)
        if random.random() < 0.012:
            particles.append(Particle(
                f.x+random.uniform(-3,3), f.y+random.uniform(-3,3),
                C_FLY_DIM,
                vx=random.uniform(-0.3,0.3), vy=random.uniform(-0.7,-0.1),
                life=random.randint(12,28), r=1.1))

    # Cursor
    if mouse_pos:
        mx, my = mouse_pos
        canvas.coords(cursor_ring, mx-14,my-14,mx+14,my+14)
        canvas.coords(cursor_dot, mx-2,my-2,mx+2,my+2)
    else:
        canvas.coords(cursor_ring, 0,0,1,1)
        canvas.coords(cursor_dot, 0,0,1,1)

    # Random scatter
    if random.randint(0,70) == 0:
        sample = random.sample(fireflies, random.randint(1,4))
        for f in sample:
            f.dx += random.uniform(-1.2,1.2)
            f.dy += random.uniform(-1.2,1.2)

    # Particles
    draw_particles()

    check_tasks()
    refresh_panel()

    root.after(28, loop)

fireflies = [Firefly(canvas) for _ in range(28)]
spawn_zones()
refresh_panel()
start_ambient()
loop()
root.mainloop()