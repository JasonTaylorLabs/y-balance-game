"""
main.py - Y-Balance Game UI and Logic

Implements the Y-Balance Game using Pygame and three laser sensors (LaserArray).
Features robust error handling, user-friendly alerts, and a clean, maintainable structure.

Author: Mark Rowley
"""

#!/usr/bin/env python3
import os, pygame, sys, random, math, time
from sensors import LaserArray

# --- Initialization ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
pygame.init()
info = pygame.display.Info()
SCREEN_W, SCREEN_H = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
clock = pygame.time.Clock()

# --- Constants & Defaults ---
MARGIN, CENTER = 20, (SCREEN_W//2, SCREEN_H//2)
MAX_PX = min(SCREEN_W, SCREEN_H)//2 - MARGIN
USER_ANGLES = [0, 135, 225]
dirs = ['forward','lateral','crossed']
defaults = dict(max_mm=1200.0, tol=5.0, hold=3.0, diff=10.0)

# --- Fonts ---
font = pygame.font.SysFont(None,32)
font_big = pygame.font.SysFont(None,96)
font_title = pygame.font.SysFont(None,48)
font_msg = pygame.font.SysFont(None,32)
f2 = pygame.font.SysFont(None,36)

# --- UI Alert ---
def show_alert(message, title="Error"):
    alert_w, alert_h = 600, 200
    surf = pygame.Surface((alert_w, alert_h)); surf.fill((255,240,240))
    pygame.draw.rect(surf, (200,0,0), surf.get_rect(), 4)
    surf.blit(font_title.render(title, True, (200,0,0)), (30, 20))
    for i, line in enumerate(message.split('\n')):
        surf.blit(font_msg.render(line, True, (0,0,0)), (30, 80 + i*36))
    screen.blit(surf, (SCREEN_W//2 - alert_w//2, SCREEN_H//2 - alert_h//2))
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type in (pygame.KEYDOWN, pygame.QUIT): return
        time.sleep(0.05)

# --- Sensor Driver ---
try:
    lasers = LaserArray(baud=115200)
except Exception as e:
    show_alert(f"Failed to initialize sensors:\n{e}", title="Sensor Error")
    pygame.quit(); sys.exit(1)

# --- Asset Loader ---
def load_image(path, fallback_color=(255,0,0,255), size=None):
    try:
        img = pygame.image.load(path).convert_alpha()
        if size: img = pygame.transform.smoothscale(img, size)
        return img
    except Exception as e:
        show_alert(f"Failed to load asset:\n{path}\n{e}", title="Asset Error")
        surf = pygame.Surface(size if size else (32,32), pygame.SRCALPHA)
        surf.fill(fallback_color)
        return surf

ASSETS = os.path.join(SCRIPT_DIR,'assets') + os.sep
bg_img = load_image(ASSETS+'lock_face_base.png', size=(int(2.2*MAX_PX), int(2.2*MAX_PX)))
bg = bg_img; bg_rect = bg.get_rect(center=CENTER)
pin_img = load_image(ASSETS+'slider_lock_pin_asset.png', size=(SLIDER_SZ, SLIDER_SZ))
pin_gray = pin_img.copy(); pin_gray.fill((150,150,150,255), special_flags=pygame.BLEND_RGBA_MULT)
orig_tgt_img = load_image(ASSETS+'target_asset.png')

# --- Geometry & State ---
ORIGIN_RADIUS_PX = int(MAX_PX * 0.0)
SLIDER_SZ = int(MAX_PX * 0.15)
BASE_TARGET_PX = int(MAX_PX * 0.20)
block_centers = [(CENTER[0] + ORIGIN_RADIUS_PX * math.cos(math.radians(deg-90)),
                  CENTER[1] + ORIGIN_RADIUS_PX * math.sin(math.radians(deg-90))) for deg in USER_ANGLES]
dist_range_px = MAX_PX - ORIGIN_RADIUS_PX
max_mm = defaults['max_mm']
PX_PER_MM = dist_range_px / max_mm
smooth_mm = [0.0, 0.0, 0.0]
alpha = 10.0

# --- Chart UI Fields ---
labels = ['Rod Length (mm):','Tolerance (mm):','Hold Time (s):','Difficulty (%):']
values = [f"{max_mm:.1f}", f"{defaults['tol']:.1f}", f"{defaults['hold']:.1f}", f"{defaults['diff']:.1f}"]
active = 0
start_x, start_y, dy = 50, 300, 50
field_w, field_h = 200, 32
field_rects = [pygame.Rect(start_x+200, start_y + i*dy, field_w, field_h) for i in range(len(labels))]

# --- Game State ---
def reset_game(stage_val=1, start_timer=False):
    global stage, targets, unlocked, lock_start, locked_dist, timer_start, elapsed_time, score, final_beat, confetti
    stage = stage_val
    targets = [random.uniform(0, max_mm) for _ in dirs]
    unlocked = [False]*3
    lock_start = [None]*3
    locked_dist = [None]*3
    timer_start = time.time() if start_timer else None
    elapsed_time = 0.0
    score = 0
    final_beat = False
    confetti.clear()
mode, stage, max_stage = 'chart', 1, 3
sensors_enabled = [True]*3
reset_game()

# --- Helpers ---
def apply_chart_values():
    global max_mm, TOLERANCE, HOLD_TIME, DIFFICULTY, PX_PER_MM
    try:
        max_mm     = float(values[0])
        TOLERANCE  = float(values[1])
        HOLD_TIME  = float(values[2])
        DIFFICULTY = float(values[3])
        PX_PER_MM  = dist_range_px / max_mm
        reset_game()
    except: pass

def draw_target_and_slider(i, deg, display_mm, target_mm, unlocked):
    factor  = 1.0 - (DIFFICULTY/100)*(stage-1)
    size_px = max(4, int(BASE_TARGET_PX * factor))
    tgt_img = pygame.transform.smoothscale(orig_tgt_img, (size_px, size_px))
    ox,oy   = block_centers[i]
    rad     = math.radians(deg - 90)
    tp      = target_mm * PX_PER_MM
    tx,ty   = ox + tp*math.cos(rad), oy + tp*math.sin(rad)
    screen.blit(tgt_img, tgt_img.get_rect(center=(int(tx),int(ty))))
    sp = (display_mm * PX_PER_MM) if display_mm is not None else 0
    sx = ox + sp * math.cos(rad)
    sy = oy + sp * math.sin(rad)
    img = pin_gray if unlocked else pin_img
    screen.blit(img, img.get_rect(center=(int(sx),int(sy))))

def update_and_draw_confetti(dt):
    for _ in range(15): confetti.append(Confetti(*CENTER))
    for p in confetti[:]:
        p.update(dt)
        if p.life <= 0: confetti.remove(p)
    for p in confetti: p.draw(screen)

def draw_chart():
    screen.fill((240,240,240))
    y = 50
    for i,d in enumerate(dirs):
        status = 'On' if sensors_enabled[i] else 'Off'
        raw = lasers.read_distance(i)
        txt = f"{d.title():<8} {status:>3}  "
        txt += "--.- cm" if raw is None else f"{raw/10.0:6.1f} cm"
        screen.blit(f2.render(txt,True,(0,0,0)), (50,y))
        y += 50
    for i,label in enumerate(labels):
        screen.blit(font.render(label,True,(0,0,0)), (start_x, start_y + i*dy))
        clr = (200,200,255) if i==active else (255,255,255)
        pygame.draw.rect(screen, clr, field_rects[i])
        pygame.draw.rect(screen, (0,0,0), field_rects[i], 2)
        screen.blit(font.render(values[i],True,(0,0,0)), (field_rects[i].x+5, field_rects[i].y+5))

def draw_game(dt):
    global final_beat, timer_end, elapsed_time, score
    screen.fill((240,240,240))
    screen.blit(bg, bg_rect)
    all_unlocked = True
    for i,deg in enumerate(USER_ANGLES):
        if not sensors_enabled[i]: all_unlocked = False; continue
        raw_mm = lasers.read_distance(i)
        if raw_mm is None: all_unlocked = False; continue
        raw_mm = min(max(raw_mm, 0), max_mm)
        smooth_mm[i] += (raw_mm - smooth_mm[i]) * min(1.0, alpha * dt)
        if not unlocked[i]:
            if abs(raw_mm - targets[i]) <= TOLERANCE:
                if lock_start[i] is None: lock_start[i] = time.time()
                elif time.time() - lock_start[i] >= HOLD_TIME: unlocked[i] = True
            else: lock_start[i] = None
        if not unlocked[i]: all_unlocked = False
        if unlocked[i] and locked_dist[i] is None: locked_dist[i] = raw_mm
        display_mm = locked_dist[i] if unlocked[i] else smooth_mm[i]
        draw_target_and_slider(i, deg, display_mm, targets[i], unlocked[i])
    return all_unlocked

# --- Main Loop ---
while True:
    try:
        dt = clock.tick(60) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_TAB:
                    if mode=='chart': reset_game(start_timer=True)
                    mode = 'game' if mode=='chart' else 'chart'; continue
                if mode=='chart':
                    if ev.key == pygame.K_UP: active = (active - 1) % len(labels)
                    elif ev.key == pygame.K_DOWN: active = (active + 1) % len(labels)
                    elif ev.key == pygame.K_RETURN: apply_chart_values()
                    elif ev.key == pygame.K_BACKSPACE: values[active] = values[active][:-1]
                    else:
                        c = ev.unicode
                        if c and (c.isdigit() or (c=='.' and '.' not in values[active])): values[active] += c
                else:
                    if ev.key in (pygame.K_1,pygame.K_2,pygame.K_3): sensors_enabled[ev.key - pygame.K_1] = not sensors_enabled[ev.key - pygame.K_1]
                    elif ev.key == pygame.K_r: reset_game(start_timer=True)
        if mode=='chart': draw_chart()
        else:
            done = draw_game(dt)
            if timer_start is not None and not final_beat:
                now = time.time() - timer_start
                ts = font_big.render(f"Time: {now:.2f}s", True, (0,0,0))
                screen.blit(ts, (50,50))
            if not final_beat and done:
                if stage < max_stage:
                    stage += 1
                    reset_game(stage_val=stage, start_timer=False)
                else:
                    final_beat = True
                    timer_end  = time.time()
                    elapsed_time = (timer_end - timer_start) if timer_start else 0.0
                    score = int((DIFFICULTY * 1000) / (elapsed_time + 0.01))
            if final_beat:
                update_and_draw_confetti(dt)
                t_s = font_big.render(f"Time: {elapsed_time:.2f}s", True, (0,0,0))
                s_s = font_big.render(f"Score: {score}", True, (0,0,0))
                screen.blit(t_s, t_s.get_rect(center=(SCREEN_W//2,SCREEN_H//2-50)))
                screen.blit(s_s, s_s.get_rect(center=(SCREEN_W//2,SCREEN_H//2+50)))
        pygame.display.flip()
    except Exception as e:
        print(f"[FATAL] Unhandled exception: {e}")
        pygame.quit(); sys.exit(1)