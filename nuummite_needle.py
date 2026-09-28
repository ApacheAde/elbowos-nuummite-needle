#!/usr/bin/env python3
"""Nuummite Needle — neon thread-the-eye arcade for ElbowOS."""
from __future__ import annotations

import math
import os
import random
import subprocess
import sys

import pygame

W, H = 1080, 1920
FPS = 30
TITLE = "NUUMMITE NEEDLE"
HANDLE = "x.com/ElbowOS"
VOID = (8, 6, 16)
INK = (16, 12, 28)
GOLD = (255, 196, 72)
COPPER = (255, 122, 48)
INDIGO = (92, 110, 255)
SHEEN = (64, 220, 210)
ROSE = (255, 78, 140)
ICE = (230, 236, 255)
SLAG = (255, 64, 86)


class Spark:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "r")

    def __init__(self, x, y, vx, vy, life, col, r=5):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life, self.col, self.r = life, col, r


class Eye:
    __slots__ = ("x", "y", "vx", "w", "h", "spin", "hue", "done")

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx = random.choice((-1, 1)) * random.uniform(40, 120)
        self.w = random.randint(78, 118)
        self.h = random.randint(36, 54)
        self.spin = random.uniform(-1.4, 1.4)
        self.hue = random.choice((GOLD, INDIGO, SHEEN, COPPER))
        self.done = False


class Game:
    def __init__(self, record: bool):
        self.record = record
        self.surf = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.font_lg = pygame.font.Font(None, 64)
        self.font_md = pygame.font.Font(None, 44)
        self.font_sm = pygame.font.Font(None, 30)
        self.reset()

    def reset(self) -> None:
        self.px = W * 0.5
        self.py = H * 0.72
        self.vx = 0.0
        self.score = 0
        self.lives = 3
        self.pulse = 0.0
        self.cool = 0.0
        self.over = False
        self.shake = 0.0
        self.combo = 0
        self.scroll = 0.0
        self.sparks: list[Spark] = []
        self.eyes: list[Eye] = []
        self.trail: list[tuple[float, float]] = []
        self.stars = [
            (random.randrange(W), random.randrange(H), random.uniform(0.25, 1.8))
            for _ in range(90)
        ]
        for i in range(7):
            self.eyes.append(Eye(random.randint(180, W - 180), 220 + i * 210))

    def burst(self, x, y, col, n=14) -> None:
        for _ in range(n):
            a = random.random() * 6.2832
            s = random.uniform(70, 340)
            self.sparks.append(
                Spark(x, y, s * math.cos(a), s * math.sin(a), random.uniform(0.18, 0.48), col, random.randint(3, 7))
            )

    def _spawn(self) -> None:
        self.eyes.append(Eye(random.randint(170, W - 170), -40))

    def autoplay(self) -> None:
        if self.over:
            if self.cool <= 0:
                self.reset()
            return
        nxt = None
        best = 1e9
        for e in self.eyes:
            if e.done or e.y > self.py - 20:
                continue
            d = self.py - e.y
            if 40 < d < best:
                best, nxt = d, e
        if nxt is None:
            self.vx += (W * 0.5 - self.px) * 0.004
            return
        lead = nxt.vx * 0.28
        self.vx += ((nxt.x + lead) - self.px) * 0.012

    def _clip(self) -> None:
        if self.cool > 0 or self.over:
            return
        self.lives -= 1
        self.combo = 0
        self.shake = 0.28
        self.cool = 0.55
        self.burst(self.px, self.py, SLAG, 18)
        if self.lives <= 0:
            self.over = True
            self.cool = 1.4

    def update(self, dt: float) -> None:
        self.pulse += dt
        self.cool = max(0.0, self.cool - dt)
        self.shake = max(0.0, self.shake - dt)
        if self.record:
            self.autoplay()
        if self.over:
            self._fx(dt)
            return
        self.vx *= 0.90
        self.px = max(90.0, min(W - 90.0, self.px + self.vx * dt * 60))
        speed = 210 + min(160, self.score * 0.35)
        self.scroll += speed * dt
        self.trail.append((self.px, self.py))
        if len(self.trail) > 28:
            self.trail.pop(0)
        keep = []
        for e in self.eyes:
            e.y += speed * dt
            e.x += e.vx * dt
            if e.x < 130 or e.x > W - 130:
                e.vx *= -1
                e.x = max(130, min(W - 130, e.x))
            if e.y > H + 60:
                continue
            if not e.done and abs(e.y - self.py) < 16:
                dx = abs(self.px - e.x)
                if dx < e.w * 0.38:
                    e.done = True
                    self.combo += 1
                    self.score += 10 + self.combo * 4
                    self.burst(e.x, e.y, e.hue, 16)
                elif dx < e.w * 0.72:
                    e.done = True
                    self._clip()
            keep.append(e)
        self.eyes = keep
        while len(self.eyes) < 8:
            self._spawn()
        self._fx(dt)

    def _fx(self, dt: float) -> None:
        alive = []
        for sp in self.sparks:
            sp.life -= dt
            if sp.life <= 0:
                continue
            sp.x += sp.vx * dt
            sp.y += sp.vy * dt
            alive.append(sp)
        self.sparks = alive

    def handle(self, ev) -> None:
        if ev.type != pygame.KEYDOWN:
            return
        if ev.key == pygame.K_r:
            self.reset()
        if self.over:
            return
        if ev.key in (pygame.K_LEFT, pygame.K_a):
            self.vx -= 18
        if ev.key in (pygame.K_RIGHT, pygame.K_d):
            self.vx += 18

    def draw(self, s: pygame.Surface) -> None:
        s.fill(VOID)
        ox = int(math.sin(self.pulse * 40) * 9 * self.shake)
        oy = int(math.cos(self.pulse * 31) * 7 * self.shake)
        for sx, sy, sc in self.stars:
            yy = int((sy + self.scroll * 0.35 * sc) % H)
            tw = 18 + int(20 * math.sin(self.pulse * 2.2 + sx * 0.01))
            col = (30 + tw, 24 + tw // 2, 48 + tw)
            pygame.draw.circle(s, col, (sx + ox, yy + oy), 1 if sc < 0.9 else 2)
        pygame.draw.rect(s, INK, (36, 236, W - 72, 1460), border_radius=40)
        pygame.draw.rect(s, INDIGO, (36, 236, W - 72, 1460), 3, border_radius=40)
        for i in range(6):
            yy = int((self.scroll * 0.6 + i * 280) % 1460) + 236
            pygame.draw.line(s, (28, 22, 52), (60, yy), (W - 60, yy), 2)
        for e in self.eyes:
            ex, ey = int(e.x) + ox, int(e.y) + oy
            tilt = math.sin(self.pulse * e.spin) * 0.18
            rx, ry = e.w, int(e.h + 4 * math.sin(self.pulse * 5 + e.x))
            box = pygame.Rect(0, 0, rx * 2, ry * 2)
            box.center = (ex, ey)
            pygame.draw.ellipse(s, e.hue, box, 7)
            inner = box.inflate(-28, -16)
            pygame.draw.ellipse(s, (12, 10, 22), inner)
            pygame.draw.ellipse(s, ICE if e.done else e.hue, inner, 2)
            if tilt:
                pygame.draw.line(s, e.hue, (ex - rx + 8, ey), (ex + rx - 8, ey), 2)
        if len(self.trail) > 1:
            pts = [(int(x) + ox, int(y) + oy - (len(self.trail) - i) * 7) for i, (x, y) in enumerate(self.trail)]
            if len(pts) >= 2:
                pygame.draw.lines(s, INDIGO, False, pts, 6)
                pygame.draw.lines(s, GOLD, False, pts, 2)
        px, py = int(self.px) + ox, int(self.py) + oy
        glow = 16 + int(6 * math.sin(self.pulse * 8))
        pygame.draw.circle(s, (40, 28, 12), (px, py), 22 + glow)
        pygame.draw.circle(s, GOLD, (px, py), 18)
        pygame.draw.circle(s, ICE, (px - 4, py - 5), 6)
        pygame.draw.circle(s, COPPER, (px, py + 2), 7)
        for sp in self.sparks:
            pygame.draw.circle(s, sp.col, (int(sp.x) + ox, int(sp.y) + oy), max(1, int(sp.r * sp.life * 2)))
        title = self.font_lg.render(TITLE, True, GOLD)
        s.blit(title, title.get_rect(center=(W // 2, 78)))
        handle = self.font_sm.render(HANDLE, True, SHEEN)
        s.blit(handle, handle.get_rect(center=(W // 2, 128)))
        meta = self.font_md.render(f"SCORE  {self.score}    LIVES  {max(0, self.lives)}", True, COPPER)
        s.blit(meta, meta.get_rect(center=(W // 2, 186)))
        hint = self.font_sm.render("A / D  steer the filament    R reset", True, ICE)
        s.blit(hint, hint.get_rect(center=(W // 2, H - 48)))
        if self.over:
            over = self.font_md.render("THE THREAD SNAPPED", True, SLAG)
            s.blit(over, over.get_rect(center=(W // 2, 250)))

    def play(self) -> None:
        screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption(TITLE)
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                else:
                    self.handle(ev)
            keys = pygame.key.get_pressed()
            if not self.over:
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.vx -= 42 * dt * 60
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.vx += 42 * dt * 60
            self.update(dt)
            self.draw(self.surf)
            screen.blit(self.surf, (0, 0))
            pygame.display.flip()

    def record_mp4(self, path: str) -> None:
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "20", "-preset", "fast", "-movflags", "+faststart", path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        frames = FPS * 15
        for i in range(frames):
            self.update(1.0 / FPS)
            self.draw(self.surf)
            proc.stdin.write(pygame.image.tostring(self.surf, "RGB"))
            if i % 30 == 0:
                print(f"frame {i}/{frames}", flush=True)
        proc.stdin.close()
        rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed: {rc}")
        print("wrote", path)


def main() -> None:
    record = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
    play = "--play" in sys.argv
    if record or not play:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    g = Game(record or not play)
    if record or not play:
        out = os.environ.get("ELBOWOS_MP4", "/home/workdir/artifacts/NUUMMITE_NEEDLE_ElbowOS.mp4")
        g.record_mp4(out)
    else:
        g.play()
    pygame.quit()


if __name__ == "__main__":
    main()
