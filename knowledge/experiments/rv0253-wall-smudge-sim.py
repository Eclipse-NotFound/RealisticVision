# -*- coding: utf-8 -*-
# classic 墙渲染离线像素模拟：复刻 v0.25.2 / v0.25.3 合成管线
# 雾层 1px/瓦片(scale40 双线性, tile 对齐) + 墙层 2px/瓦片(scale20 双线性, 位移 -20,-20)
# 目的：定位"墙内阴影脏"的来源，验证候选修复
import math

TILE = 40
W, H = 16, 10                      # 瓦片数
SW, SH = W * TILE, H * TILE        # 屏幕尺寸
L1, L2 = 300.0, 1000.0
DIMA = 166                          # 记忆暗色 alpha
PX, PY = 5.5 * TILE, 4.0 * TILE     # 玩家位置（像素中心）

# 0=地板 1=墙；边界全墙 + 一段内墙
grid = [[0] * W for _ in range(H)]
for x in range(W):
    grid[0][x] = grid[H - 1][x] = 1
for y in range(H):
    grid[y][0] = grid[y][W - 1] = 1
for y in range(2, 7):
    grid[y][9] = 1                  # 一段竖直内墙

def is_wall(x, y):
    return 0 <= x < W and 0 <= y < H and grid[y][x] == 1

def in_bounds(x, y):
    return 0 <= x < W and 0 <= y < H

# 玩家光照 visi：径向衰减 + 射线阴影（墙阻挡 → 相邻墙瓦片亮暗突变 = 真实"脏"来源）
def los(tx, ty):
    """从玩家到瓦片中心的射线，途中（不含终点瓦片）遇墙 → 0"""
    cx, cy = (tx + 0.5) * TILE, (ty + 0.5) * TILE
    steps = int(math.hypot(cx - PX, cy - PY) / 20) + 1
    for i in range(1, steps):
        px = PX + (cx - PX) * i / steps
        py = PY + (cy - PY) * i / steps
        tx2, ty2 = int(px / TILE), int(py / TILE)
        if (tx2, ty2) != (tx, ty) and is_wall(tx2, ty2):
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
explored = [[visi[y][x] > 0.05 for x in range(W)] for y in range(H)]  # 简化：曾照亮=探索

# 公式值 aArr：gameA=(1-visi)*255；不可见且已探索 → 记忆暗色
aArr = [[0] * W for _ in range(H)]
for y in range(H):
    for x in range(W):
        gameA = round((1 - visi[y][x]) * 255)
        visible = visi[y][x] >= 0.6
        if visible:
            a = gameA
        else:
            a = DIMA if explored[y][x] else 255
        aArr[y][x] = max(0, min(255, a))

def is_wall(x, y):
    return 0 <= x < W and 0 <= y < H and grid[y][x] == 1

def in_bounds(x, y):
    return 0 <= x < W and 0 <= y < H

def build_fog(wall_pixel_mode):
    """wall_pixel_mode: 'coord' 全协调(v0.25.2/v0.25.4) / 'own_boundary' 边界=自身(v0.25.3)"""
    fog = [[255] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if grid[y][x] == 1:
                if wall_pixel_mode == 'own_boundary' and (
                        x == 0 or y == 0 or x == W - 1 or y == H - 1):
                    fog[y][x] = aArr[y][x]
                    continue
                if wall_pixel_mode == 'own_boundary':  # v0.25.3：内部墙=协调
                    s, c = 0, 0
                    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                        nx, ny = x + dx, y + dy
                        if in_bounds(nx, ny) and not is_wall(nx, ny):
                            s += aArr[ny][nx]
                            c += 1
                    fog[y][x] = round(s / c) if c else aArr[y][x]
                    continue
                # coord：全协调。例外：右/下边界墙——其暴露象限的覆盖格越界
                # （墙层位图到边），只能靠雾层自己出自身值（v0.25.4 同此）
                if wall_pixel_mode == 'coord' and (x == W - 1 or y == H - 1):
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

def bilinear_sample(src, sw, sh, sx, sy):
    """双线性采样，边缘钳制。src[y][x] 为 alpha 值。"""
    if sx < 0:
        sx = 0.0
    if sy < 0:
        sy = 0.0
    if sx > sw - 1:
        sx = sw - 1.0
    if sy > sh - 1:
        sy = sh - 1.0
    x0, y0 = int(sx), int(sy)
    x1, y1 = min(x0 + 1, sw - 1), min(y0 + 1, sh - 1)
    fx, fy = sx - x0, sy - y0
    a = src[y0][x0] * (1 - fx) * (1 - fy) + src[y0][x1] * fx * (1 - fy) \
        + src[y1][x0] * (1 - fx) * fy + src[y1][x1] * fx * fy
    return a

def render_fog(fog):
    """雾层：1px/瓦片 scale40 tile 对齐 → 屏幕 alpha。"""
    out = [[0] * SW for _ in range(SH)]
    for dy in range(SH):
        sy = (dy + 0.5) / TILE - 0.5
        for dx in range(SW):
            sx = (dx + 0.5) / TILE - 0.5
            out[dy][dx] = bilinear_sample(fog, W, H, sx, sy)
    return out

def render_wall_layer(fill_boundary=False):
    """墙层：2px/瓦片 scale20，位移 (-20,-20)。
    每墙 4 格写自身值；fill_boundary=True 时（v0.25.4）左/上边界墙的
    暴露象限格（E/S 非墙时）补写自身值（覆盖雾层协调值，消亮带）。"""
    cw, ch = 2 * W, 2 * H
    cells = [[0] * cw for _ in range(ch)]   # 0=透明
    for y in range(H):
        for x in range(W):
            if grid[y][x] == 1:
                v = aArr[y][x]
                for cy in (2 * y, 2 * y + 1):
                    for cx in (2 * x, 2 * x + 1):
                        cells[cy][cx] = v
                if fill_boundary and (x == 0 or y == 0):
                    # 左列墙：NE 象限格 (2x+2, 2y)——E 非墙时补
                    if x == 0 and not is_wall(x + 1, y) and 2 * x + 2 < cw:
                        cells[2 * y][2 * x + 2] = v
                    # 顶行墙：SW 象限格 (2x, 2y+2)——S 非墙时补
                    if y == 0 and not is_wall(x, y + 1) and 2 * y + 2 < ch:
                        cells[2 * y + 2][2 * x] = v
                    # 左上角墙：SE 象限格 (2x+1, 2y+1)——SE 非墙时补
                    if x == 0 and y == 0 and not is_wall(x + 1, y + 1):
                        cells[2 * y + 1][2 * x + 1] = v
    out = [[0] * SW for _ in range(SH)]
    for dy in range(SH):
        sy = (dy + 20 + 10) / 20.0 - 0.5    # dest → layer 坐标（位移-20，scale20）
        for dx in range(SW):
            sx = (dx + 20 + 10) / 20.0 - 0.5
            out[dy][dx] = bilinear_sample(cells, cw, ch, sx, sy)
    return out

def composite(scene, fog_s, wall_s):
    """黑遮罩 over：a = w + f*(1-w)；场景亮度 × (1-a)。"""
    out = [[0] * SW for _ in range(SH)]
    for dy in range(SH):
        for dx in range(SW):
            wa = wall_s[dy][dx] / 255.0
            fa = fog_s[dy][dx] / 255.0
            a = wa + fa * (1 - wa)
            out[dy][dx] = scene[dy][dx] * (1 - a)
    return out

def build_scene():
    s = [[20] * SW for _ in range(SH)]
    for y in range(H):
        for x in range(W):
            v = 55 if grid[y][x] == 1 else 120
            for py in range(y * TILE, (y + 1) * TILE):
                for px in range(x * TILE, (x + 1) * TILE):
                    s[py][px] = v
    return s

def profile_row(img, dy):
    return [round(img[dy][dx]) for dx in range(0, SW, 20)]

def ascii_map(img, step=20):
    chars = " .:-=+*#%@"
    lines = []
    for dy in range(0, SH, step * 2):
        line = ""
        for dx in range(0, SW, step):
            v = img[dy][dx]
            line += chars[min(9, int(v / 26))]
        lines.append(line)
    return "\n".join(lines)

scene = build_scene()

cases = (
    ("v0.25.2(全协调)", "coord", False),
    ("v0.25.3(边界=自身)", "own_boundary", False),
    ("v0.25.4(协调+边界补格)", "coord_fix", True),
)
for name, mode, fill in cases:
    fog = build_fog(mode)
    fog_s = render_fog(fog)
    wall_s = render_wall_layer(fill)
    comp = composite(scene, fog_s, wall_s)
    print("=" * 30, name, "=" * 30)
    # 底部墙排（ty=H-1）中心行的屏幕剖面 y = (H-1)*40+20（墙下半=雾层露出区）
    y_probe = (H - 1) * TILE + 20
    print("底行墙 y=%d 剖面(每20px):" % y_probe, profile_row(comp, y_probe))
    # 左列墙（tx=0）x=20（墙右半=雾层露出区）纵向剖面
    prof = [round(comp[dy][20]) for dy in range(0, SH, 20)]
    print("左列墙 x=20 剖面(每20px):", prof)
    # 地板侧稀释测量：底行墙上方的地板行（ty=H-2）中段
    y_probe2 = (H - 2) * TILE + 20
    print("底行上方地板 y=%d 剖面:" % y_probe2, profile_row(comp, y_probe2))
    print("ASCII 合成图（亮=场景可见）:")
    print(ascii_map(comp))
    print()
