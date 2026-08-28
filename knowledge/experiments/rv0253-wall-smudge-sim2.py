# -*- coding: utf-8 -*-
# classic 墙渲染离线像素模拟 v2：复刻 classic 合成管线，输出 PNG 图像直观对比
# 场景：边界墙常亮（visi=1）+ 邻近地板记忆暗（166）——真实游戏里两者天然错位
# 变体：
#   A v0.25.0  雾层墙像素=自身值，无墙层
#   B v0.25.2  雾层墙像素=协调值，墙层 4 格自身值（含 W/N 溢出）
#   C v0.25.3  雾层墙像素=边界自身值，墙层 4 格自身值
#   D 候选     雾层墙像素=协调值，墙层只写 (2x+1,2y+1) 一格（恰好覆盖整瓦片，零溢出）
import math
import struct
import zlib

TILE = 40
W, H = 16, 10
SW, SH = W * TILE, H * TILE
L1, L2 = 300.0, 1000.0
DIMA = 166
PX, PY = 5.5 * TILE, 4.0 * TILE

grid = [[0] * W for _ in range(H)]
for x in range(W):
    grid[0][x] = grid[H - 1][x] = 1
for y in range(H):
    grid[y][0] = grid[y][W - 1] = 1
for y in range(2, 7):
    grid[y][9] = 1

def is_wall(x, y):
    return 0 <= x < W and 0 <= y < H and grid[y][x] == 1

def in_bounds(x, y):
    return 0 <= x < W and 0 <= y < H

def los(tx, ty):
    cx, cy = (tx + 0.5) * TILE, (ty + 0.5) * TILE
    steps = int(math.hypot(cx - PX, cy - PY) / 20) + 1
    for i in range(1, steps):
        px = PX + (cx - PX) * i / steps
        py = PY + (cy - PY) * i / steps
        t2 = (int(px / TILE), int(py / TILE))
        if t2 != (tx, ty) and is_wall(*t2):
            return False
    return True

def visi_at(tx, ty):
    cx, cy = (tx + 0.5) * TILE, (ty + 0.5) * TILE
    d = math.hypot(cx - PX, cy - PY)
    if d > L2 or not los(tx, ty):
        return 0.0
    if d <= L1:
        return 1.0
    return (L2 - d) / (L2 - L1)

visi = [[visi_at(x, y) for x in range(W)] for y in range(H)]
explored = [[visi[y][x] > 0.05 for x in range(W)] for y in range(H)]

aArr = [[0] * W for _ in range(H)]
for y in range(H):
    for x in range(W):
        gameA = round((1 - visi[y][x]) * 255)
        if visi[y][x] >= 0.6:
            a = gameA
        else:
            # 记忆区：地板渐暗 166；墙 visi 常亮保持亮（游戏语义：墙 visi 不衰减）
            if explored[y][x]:
                a = DIMA if grid[y][x] == 0 else gameA
            else:
                a = 255
        aArr[y][x] = max(0, min(255, a))

def build_fog(mode):
    """mode: 'own' 全自身(v0.25.0) / 'coord' 全协调(v0.25.2) /
    'own_boundary' 边界自身其余协调(v0.25.3)"""
    fog = [[255] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if grid[y][x] == 1:
                if mode == 'own' or (mode == 'own_boundary' and (
                        x == 0 or y == 0 or x == W - 1 or y == H - 1)):
                    fog[y][x] = aArr[y][x]
                    continue
                s, c = 0, 0
                for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                    nx, ny = x + dx, y + dy
                    if in_bounds(nx, ny) and not is_wall(nx, ny):
                        s += aArr[ny][nx]
                        c += 1
                fog[y][x] = round(s / c) if c else aArr[y][x]
            else:
                fog[y][x] = aArr[y][x]
    return fog

def bilinear(src, sw, sh, sx, sy):
    sx = min(max(sx, 0.0), sw - 1.0)
    sy = min(max(sy, 0.0), sh - 1.0)
    x0, y0 = int(sx), int(sy)
    x1, y1 = min(x0 + 1, sw - 1), min(y0 + 1, sh - 1)
    fx, fy = sx - x0, sy - y0
    return src[y0][x0] * (1 - fx) * (1 - fy) + src[y0][x1] * fx * (1 - fy) \
        + src[y1][x0] * (1 - fx) * fy + src[y1][x1] * fx * fy

def render_fog(fog):
    out = [[0] * SW for _ in range(SH)]
    for dy in range(SH):
        sy = (dy + 0.5) / TILE - 0.5
        for dx in range(SW):
            out[dy][dx] = bilinear(fog, W, H, (dx + 0.5) / TILE - 0.5, sy)
    return out

def render_wall_layer(cells_only_one=False):
    """墙层 2px/瓦片 scale20 位移(-20,-20)。
    cells_only_one=False：每墙写 4 格（v0.25.2/3，含 W/N 溢出）；
    True：只写 (2x+1,2y+1) 一格（恰好=整瓦片，零溢出）。"""
    cw, ch = 2 * W, 2 * H
    cells = [[0] * cw for _ in range(ch)]
    for y in range(H):
        for x in range(W):
            if grid[y][x] == 1:
                v = aArr[y][x]
                if cells_only_one:
                    cells[2 * y + 1][2 * x + 1] = v
                else:
                    for cy in (2 * y, 2 * y + 1):
                        for cx in (2 * x, 2 * x + 1):
                            cells[cy][cx] = v
    out = [[0] * SW for _ in range(SH)]
    for dy in range(SH):
        sy = (dy + 30) / 20.0 - 0.5
        for dx in range(SW):
            out[dy][dx] = bilinear(cells, cw, ch, (dx + 30) / 20.0 - 0.5, sy)
    return out

scene = [[20] * SW for _ in range(SH)]
for y in range(H):
    for x in range(W):
        v = 60 if grid[y][x] == 1 else 130
        for py in range(y * TILE, (y + 1) * TILE):
            for px in range(x * TILE, (x + 1) * TILE):
                scene[py][px] = v

def write_png(path, img):
    """img[y][x] = 亮度 0-255，灰度 PNG。"""
    raw = b""
    for row in img:
        raw += b"\x00" + bytes(int(max(0, min(255, v))) for v in row)
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    ihdr = struct.pack(">IIBBBBB", SW, SH, 8, 0, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) \
        + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    open(path, "wb").write(png)
    print("wrote", path)

variants = (
    ("A_v0250_fog_own_nolayer", "own", False),
    ("B_v0252_fog_coord_layer4", "coord", False),
    ("C_v0253_fog_ownbnd_layer4", "own_boundary", False),
    ("D_cand_fog_coord_layer1", "coord", True),
)
for name, mode, one in variants:
    fog = build_fog(mode)
    fog_s = render_fog(fog)
    wall_s = render_wall_layer(one)
    comp = [[0] * SW for _ in range(SH)]
    for dy in range(SH):
        for dx in range(SW):
            wa = wall_s[dy][dx] / 255.0
            fa = fog_s[dy][dx] / 255.0
            comp[dy][dx] = scene[dy][dx] * (1 - (wa + fa * (1 - wa)))
    write_png(name + ".png", comp)
