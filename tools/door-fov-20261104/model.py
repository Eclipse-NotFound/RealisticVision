#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RealisticVision door/window FOV boundary + wall-hug leak -- offline numeric model

按当前已部署生产源（v0.34.8-clip-pad）的公式重算 current 模式雾场 alpha，
量化两条用户反馈：

  A. 可透光门/窗的视野边界 vs 墙造成的视野边界，在数值结构上差在哪
  B. 眼点落入 opac>=1 瓦片时（castRay 起点格不参与遮挡）能泄漏多大范围

边界声明：这是**模型**，复刻 RV 的算术路径，不是游戏截图，也不是原生渲染管线
的等价物。它只回答"同一套公式在两种几何上会产生什么数值"。

run:  python model.py          # 打印指标
      python model.py --png    # 另存 field-*.png
"""

import math
import os
import sys

# ------------------------------------------------------------------ 运行配置
# 取自 <APPDATA>/pfe/Local Store/RealisticVision_config.txt（游戏实际读的副本，
# 优先于 release/config.txt —— 见 RealisticVisionMod.as:569-570）
CFG = dict(
    dim=0.6,            # cfgDim       记忆/亮部亮度下限
    doordim=0.85,       # cfgDoorDim   透光门后亮度下限
    litmin=0.6,         # cfgLitMin    FOV_VISIBLE 阈值
    fog_sub=4,          # fogSub       vision_quality_preset=0 -> 4 子格/瓦片
    soft_current=25.0,  # cfgSoftCurrent
)

TILE = 40.0
FOG_PAD = 4
MASK_LIT_A = 140
FOV_NONE, FOV_DIM, FOV_VISIBLE = 0, 1, 2

G = CFG["fog_sub"]
CS = TILE / G
BLUR_R = CFG["soft_current"] * G / 40.0          # AS3 applyVisionScale:702 / :738
BLUR_SIGMA = BLUR_R * math.sqrt(3 / 12.0)        # 源码注释 452-454 的等价式（q=3）

LDIST1 = 300.0
LDIST2 = 1000.0


def dist_falloff(d2):
    """AS3 distFalloff（:3267-3279）。"""
    d = math.sqrt(d2)
    if d <= LDIST1:
        return 1.0
    if d >= LDIST2:
        return 0.0
    return (LDIST2 - d) / (LDIST2 - LDIST1)


class Scene(object):
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.opac = [[0.0] * h for _ in range(w)]

    def rect(self, x0, y0, x1, y1, opac):
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                self.opac[x][y] = opac

    def tile_opac(self, x, y):
        if x < 0 or y < 0 or x >= self.w or y >= self.h:
            return 1.0
        return self.opac[x][y]


def cast_ray(scene, eye, tgt_xy, tgt_cell, origin_guard="as3", fix_double=False):
    """DDA：复刻 castRay（:1899-2052）。

    origin_guard:
      "as3"   -- 与生产代码一致：**起点格不参与遮挡累减**
      "fixed" -- 反事实：起点格也计入遮挡（量化泄漏面积）
    fix_double:
      True    -- 反事实：目标格 opac 只累减一次。生产代码在 while 循环里步入
                 目标格时已累减一次，2028-2037 行循环退出后又累减一次，
                 落在透光门/窗/水格上的射线因此被扣两遍。
    """
    ex, ey = eye
    tx, ty = tgt_cell
    dx, dy = tgt_xy[0] - ex, tgt_xy[1] - ey
    c0x, c0y = int(math.floor(ex / TILE)), int(math.floor(ey / TILE))

    if dx > 0:
        stepx, tmaxx, tdeltax = 1, ((c0x + 1) * TILE - ex) / dx, TILE / dx
    elif dx < 0:
        stepx, tmaxx, tdeltax = -1, (c0x * TILE - ex) / dx, -TILE / dx
    else:
        stepx, tmaxx, tdeltax = 0, float("inf"), 0.0
    if dy > 0:
        stepy, tmaxy, tdeltay = 1, ((c0y + 1) * TILE - ey) / dy, TILE / dy
    elif dy < 0:
        stepy, tmaxy, tdeltay = -1, (c0y * TILE - ey) / dy, -TILE / dy
    else:
        stepy, tmaxy, tdeltay = 0, float("inf"), 0.0

    if origin_guard == "fixed":
        # v0.34.9 语义（与出货 AS3 一致）：起点格**实心**时整条射线判为被挡。
        # 0<opac<1 的半透起点格（水/薄雾区）不扣——那是 v0.34.8 与原生一致的既有语义。
        lit = 1.0
        if scene.tile_opac(c0x, c0y) >= 1:
            return -1.0
    else:
        lit = 1.0

    leaked = False
    c1x, c1y = c0x, c0y
    guard = 0
    while c1x != tx or c1y != ty:
        guard += 1
        if guard > 400:
            break
        if tmaxx < tmaxy:
            tmaxx += tdeltax
            c1x += stepx
        else:
            tmaxy += tdeltay
            c1y += stepy
        op = scene.tile_opac(c1x, c1y)
        if op >= 1:
            return -1.0
        if op > 0:
            leaked = True
        lit -= op

    op = scene.tile_opac(tx, ty)
    if op >= 1:
        return -1.0
    if op > 0:
        leaked = True
    already = guard > 0 and c1x == tx and c1y == ty
    if not (fix_double and already):
        lit -= op
    lit = max(0.0, min(1.0, lit))
    if leaked and lit < 1e-4:
        return 0.05
    return lit


def sanitize_eye(scene, feet, sc, eye):
    """v0.34.9 C-Eye-1 的模型版：把眼点夹回"当前姿态碰撞盒内的自由格"。

    feet=(gg.X, gg.Y)；sc=(gg.scX, gg.scY)（坐姿时 scY=35）。
    与 AS3 的 sanitizeEye 同序：①本身合法就直接用；②沿"眼点->盒中心偏上"回退 6 步；
    ③夹进盒内（内缩 1px）；④退回盒中心偏上。
    """
    fx, fy = feet
    sx, sy = sc

    def free(x, y):
        # 与出货 AS3 的 eyeCellFree 一致：只把"实心格"判为不合法
        return scene.tile_opac(int(x // TILE), int(y // TILE)) < 1

    if free(eye[0], eye[1]):
        return eye
    mx, my = fx, fy - sy * 0.5
    for k in range(1, 7):
        t = k / 7.0
        px = eye[0] + (mx - eye[0]) * t
        py = eye[1] + (my - eye[1]) * t
        if free(px, py):
            return (px, py)
    bx = max(fx - sx * 0.5 + 1, min(fx + sx * 0.5 - 1, eye[0]))
    by = max(fy - sy + 1, min(fy - 1, eye[1]))
    if free(bx, by):
        return (bx, by)
    return (mx, my)


def compute_fov(scene, eye, fix_double=False, no_promote_translucent=False):
    """复刻 computeFov（:1788-1897），含墙可见性传播（:1859-1894）。"""
    w, h = scene.w, scene.h
    fov = [[FOV_NONE] * h for _ in range(w)]
    br = [[0.0] * h for _ in range(w)]
    ex, ey = eye
    r = LDIST2
    r2 = r * r
    fx0 = max(0, int(math.floor((ex - r) / TILE - 0.5)))
    fy0 = max(0, int(math.floor((ey - r) / TILE - 0.5)))
    fx1 = min(w, int(math.ceil((ex + r) / TILE + 0.5)))
    fy1 = min(h, int(math.ceil((ey + r) / TILE + 0.5)))
    for tx in range(fx0, fx1):
        for ty in range(fy0, fy1):
            cx, cy = (tx + 0.5) * TILE, (ty + 0.5) * TILE
            ddx, ddy = cx - ex, cy - ey
            if ddx * ddx + ddy * ddy > r2:
                continue
            lit = cast_ray(scene, eye, (cx, cy), (tx, ty), fix_double=fix_double)
            br[tx][ty] = 0.0 if lit < 0 else min(1.0, lit * dist_falloff(ddx * ddx + ddy * ddy))
            if lit >= CFG["litmin"]:
                fov[tx][ty] = FOV_VISIBLE
            elif lit > 1e-4:
                fov[tx][ty] = FOV_DIM
    for tx in range(max(0, fx0 - 1), min(w, fx1 + 1)):
        for ty in range(max(0, fy0 - 1), min(h, fy1 + 1)):
            if fov[tx][ty] == FOV_VISIBLE or scene.opac[tx][ty] <= 0:
                continue
            if no_promote_translucent and scene.opac[tx][ty] < 1:
                continue
            for ddx, ddy in ((-1, -1), (0, -1), (1, -1), (-1, 0),
                             (1, 0), (-1, 1), (0, 1), (1, 1)):
                nx, ny = tx + ddx, ty + ddy
                if 0 <= nx < w and 0 <= ny < h:
                    if fov[nx][ny] == FOV_VISIBLE and scene.opac[nx][ny] <= 0:
                        fov[tx][ty] = FOV_VISIBLE
                        wdx = (tx + 0.5) * TILE - ex
                        wdy = (ty + 0.5) * TILE - ey
                        br[tx][ty] = dist_falloff(wdx * wdx + wdy * wdy)
                        break
    return fov, br


def native_visi(scene, eye):
    """原生 Location.lighting()（Location.as:3108-3255）的稳态值：
    逐瓦片角点 1 样本/瓦片（lightBmp 每格 1 像素），逐格累减 opac，
    再按 lDist1->lDist2 线性衰减。"""
    w, h = scene.w, scene.h
    visi = [[0.0] * h for _ in range(w)]
    p1, p2 = eye
    for x in range(1, w):
        for y in range(1, h):
            dx = x * TILE - p1
            dy = y * TILE - p2
            d2 = dx * dx + dy * dy
            if d2 >= LDIST2 * LDIST2:
                continue
            d = math.sqrt(d2)
            lit = 1.0 if d <= LDIST1 else (LDIST2 - d) / (LDIST2 - LDIST1)
            if abs(dx) == abs(dy):
                dy += 1
            if abs(dx) >= abs(dy):
                sx = TILE if dx > 0 else -TILE
                sy = dy / dx * sx
                steps = int(dx / sx)
            else:
                sy = TILE if dy > 0 else -TILE
                sx = dx / dy * sy
                steps = int(dy / sy)
            for k in range(1, steps + 1):
                op = scene.tile_opac(int((p1 + k * sx) // TILE),
                                     int((p2 + k * sy) // TILE))
                if op > 0:
                    lit -= op
                    if lit <= 0:
                        lit = 0.0
                        break
            visi[x][y] = max(0.0, min(1.0, lit))
    return visi


def fill_fog(scene, eye, fov, guard="as3", trace=None, fix_double=False,
             radius_guard=False, aperture_surface=False, lit_fastpath=False,
             door_grade=0.0, door_wall_merge=False):
    """复刻 fillFogCache(:2267-2388) + recalcTile(:2398-2464) +
    fillLitTile(:2469-2514) + fillWallTile(:2709-2762)。

    radius_guard=False 复刻 v0.34.8（recalcTile 无半径守卫，半径外子格仍会写 seenSub）；
    True 复刻 v0.34.9 的 C-Ray-2。
    trace 可选键：tile/lit/mem/recalc 分支计数，seen/seenFar"曾见"子格数与其中位于
    视野半径外的数量（C-Ray-2 的量化口径）。
    """
    w, h = scene.w, scene.h
    img = [[0] * (w * G) for _ in range(h * G)]
    dim_f = CFG["dim"]
    dim_a = int(round((1 - dim_f) * 255))
    door_f = CFG["doordim"]
    visi = native_visi(scene, eye)
    seen = set()
    d2max = LDIST2 * LDIST2

    def put(tx, ty, sx, sy, a):
        img[ty * G + sy][tx * G + sx] = max(0, min(255, int(round(a))))

    def ray(subx, suby):
        return cast_ray(scene, eye, (subx, suby),
                        (int(subx // TILE), int(suby // TILE)), guard,
                        fix_double=fix_double)

    def recalc(tx, ty, floor_f, door_grade=0.0):
        bx, by = tx * TILE, ty * TILE
        for sy in range(G):
            for sx in range(G):
                subx = bx + (sx + 0.5) * CS
                suby = by + (sy + 0.5) * CS
                sdx, sdy = subx - eye[0], suby - eye[1]
                if radius_guard and sdx * sdx + sdy * sdy > d2max:
                    lit = -1.0
                else:
                    lit = ray(subx, suby)
                if lit < 0:
                    lit = 0.0
                lit = min(1.0, lit)
                if lit > 1e-4:
                    seen.add((tx * G + sx, ty * G + sy))
                    ddx, ddy = subx - eye[0], suby - eye[1]
                    fo = dist_falloff(ddx * ddx + ddy * ddy)
                    b = lit * fo
                    floor_eff = floor_f
                    if door_grade > 0:
                        floor_eff = floor_f - (floor_f - CFG["dim"]) * min(1.0, (1 - fo) * door_grade)
                    if b < floor_eff:
                        b = floor_eff
                    put(tx, ty, sx, sy, (1 - b) * 255)
                elif (tx * G + sx, ty * G + sy) in seen:
                    put(tx, ty, sx, sy, dim_a)
                else:
                    put(tx, ty, sx, sy, 255)

    def fill_lit(tx, ty, litF=1.0):
        bx, by = tx * TILE, ty * TILE
        for sy in range(G):
            for sx in range(G):
                seen.add((tx * G + sx, ty * G + sy))
        farx = max(abs(bx + 0.5 * CS - eye[0]), abs(bx + (G - 0.5) * CS - eye[0]))
        fary = max(abs(by + 0.5 * CS - eye[1]), abs(by + (G - 0.5) * CS - eye[1]))
        if farx * farx + fary * fary <= LDIST1 * LDIST1:
            flat = max(litF, dim_f)
            for sy in range(G):
                for sx in range(G):
                    put(tx, ty, sx, sy, (1 - flat) * 255)
            return
        for sy in range(G):
            for sx in range(G):
                subx = bx + (sx + 0.5) * CS
                suby = by + (sy + 0.5) * CS
                ddx, ddy = subx - eye[0], suby - eye[1]
                f = dist_falloff(ddx * ddx + ddy * ddy) * litF
                if f < dim_f:
                    f = dim_f
                put(tx, ty, sx, sy, (1 - f) * 255)

    def wall_alpha(x, y):
        if x >= w or y >= h:
            return 255.0
        gv = 0.0 if (x == 0 or y == 0) else visi[x][y]
        game_a = math.floor((1 - gv) * 255)
        cur = 0.0                 # 当前可见 -> memCur=0
        return 255 - (255 - game_a) * (1 - cur + cur * dim_f)

    def fill_wall(tx, ty):
        a00, a10 = wall_alpha(tx, ty), wall_alpha(tx + 1, ty)
        a01, a11 = wall_alpha(tx, ty + 1), wall_alpha(tx + 1, ty + 1)
        for sy in range(G):
            fy = (sy + 0.5) / G
            left = a00 + fy * (a01 - a00)
            right = a10 + fy * (a11 - a10)
            for sx in range(G):
                fx = (sx + 0.5) / G
                put(tx, ty, sx, sy, left + fx * (right - left))

    def surface_alpha(x, y):
        """v0.35.0 C-Ap-2：透光叶面 = 与墙同族的角值（同一个原生 visi 场）。"""
        if x >= w or y >= h or x <= 0 or y <= 0:
            return 255.0
        gv = visi[x][y]
        return 255 - gv * 255

    def fill_aperture(tx, ty):
        a00, a10 = surface_alpha(tx, ty), surface_alpha(tx + 1, ty)
        a01, a11 = surface_alpha(tx, ty + 1), surface_alpha(tx + 1, ty + 1)
        for sy in range(G):
            fy = (sy + 0.5) / G
            left = a00 + fy * (a01 - a00)
            right = a10 + fy * (a11 - a10)
            for sx in range(G):
                fx = (sx + 0.5) / G
                put(tx, ty, sx, sy, left + fx * (right - left))

    def door_cone(tx, ty):
        for dx, dy in ((-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
            nx, ny = tx + dx, ty + dy
            if 0 <= nx < w and 0 <= ny < h and fov[nx][ny] == FOV_DIM:
                return True
        return False

    def door_alpha(tx, ty):
        ddx = (tx + 0.5) * TILE - eye[0]
        ddy = (ty + 0.5) * TILE - eye[1]
        fo = dist_falloff(ddx * ddx + ddy * ddy)
        fl = door_f
        if door_grade > 0:
            fl = door_f - (door_f - dim_f) * min(1.0, (1 - fo) * door_grade)
        return (1 - fl) * 255

    for tx in range(w):
        for ty in range(h):
            if scene.opac[tx][ty] >= 1:
                if door_wall_merge and door_cone(tx, ty):
                    a = door_alpha(tx, ty)
                    for sy in range(G):
                        for sx in range(G):
                            put(tx, ty, sx, sy, a)
                    continue
                fill_wall(tx, ty)
                continue
            if scene.opac[tx][ty] > 0 and aperture_surface:
                fill_aperture(tx, ty)
                continue
            f = fov[tx][ty]
            if f == FOV_DIM:
                if trace is not None:
                    trace["tile"] += 1
                recalc(tx, ty, door_f, door_grade)
                continue
            c_lit, flags = 0, 0
            lit_max = 0.0
            bx, by = tx * TILE, ty * TILE
            for sx in (0, 1):
                for sy in (0, 1):
                    subx = bx + (0.5 if sx == 0 else G - 0.5) * CS
                    suby = by + (0.5 if sy == 0 else G - 0.5) * CS
                    ddx, ddy = subx - eye[0], suby - eye[1]
                    inside = ddx * ddx + ddy * ddy <= LDIST2 * LDIST2
                    lit = ray(subx, suby) if inside else -1.0
                    if lit > 1e-4:
                        c_lit += 1
                        flags |= 1 << (sx * 2 + sy)
                        lit_max = max(lit_max, lit)
                        seen.add((tx * G + (0 if sx == 0 else G - 1),
                                  ty * G + (0 if sy == 0 else G - 1)))
                    elif inside:
                        flags |= 16 << (sx * 2 + sy)
            if trace is not None:
                if f == FOV_VISIBLE and c_lit == 4:
                    trace["lit"] += 1
                elif c_lit == 0 and (f != FOV_VISIBLE or (flags & 240) == 0):
                    trace["mem"] += 1
                else:
                    trace["recalc"] += 1
            if f == FOV_VISIBLE and c_lit == 4:
                fill_lit(tx, ty, lit_max if lit_fastpath else 1.0)
            elif c_lit == 0 and (f != FOV_VISIBLE or (flags & 240) == 0):
                for sy in range(G):
                    for sx in range(G):
                        is_seen = (tx * G + sx, ty * G + sy) in seen
                        put(tx, ty, sx, sy, dim_a if is_seen else 255)
            else:
                recalc(tx, ty, dim_f)
    if trace is not None:
        far = 0
        for (sx_i, sy_i) in seen:
            wx = (sx_i + 0.5) * CS
            wy = (sy_i + 0.5) * CS
            if (wx - eye[0]) ** 2 + (wy - eye[1]) ** 2 > d2max:
                far += 1
        trace["seen"] = len(seen)
        trace["seenFar"] = far
    return img


def blur(img, sigma):
    """源码注释 452-454：BlurFilter(bx,q) 约等于盒模糊 q 次，sigma = bx*sqrt(q/12)。
    这里用等价高斯。"""
    if sigma <= 0:
        return img
    rad = max(1, int(math.ceil(sigma * 3)))
    kernel = [math.exp(-(i * i) / (2 * sigma * sigma)) for i in range(-rad, rad + 1)]
    s = sum(kernel)
    kernel = [k / s for k in kernel]
    h, w = len(img), len(img[0])

    def conv(src, horizontal):
        out = [[0.0] * w for _ in range(h)]
        for y in range(h):
            for x in range(w):
                acc = 0.0
                for i, k in enumerate(kernel):
                    o = i - rad
                    sx = min(w - 1, max(0, x + o)) if horizontal else x
                    sy = y if horizontal else min(h - 1, max(0, y + o))
                    acc += src[sy][sx] * k
                out[y][x] = acc
        return out

    tmp = conv([[float(v) for v in r] for r in img], True)
    out = conv(tmp, False)
    return [[int(round(v)) for v in r] for r in out]


# --------------------------------------------------------------------- 场景
def build_room(kind):
    """40x20：下方大厅(row10..17) + 上方内室(row1..7)，中间横墙 row8。
    kind:
      'wide8'  开口宽 8 瓦片（x=17..24）-- 开口边即"墙造成的边界"参照
      'gap'    开口宽 2 瓦片（x=20..21）纯开口
      'door'   同宽 2 瓦片，木门 opac 0.8
      'window' 同宽 2 瓦片，窗  opac 0.2
    眼点固定 (820,700)（row17），正对开口；内室与大厅各放一根柱子做对照。"""
    s = Scene(40, 20)
    s.rect(0, 0, 39, 0, 1.0)
    s.rect(0, 19, 39, 19, 1.0)
    s.rect(0, 0, 0, 19, 1.0)
    s.rect(39, 0, 39, 19, 1.0)
    s.rect(1, 8, 38, 8, 1.0)
    if kind == "wide8":
        s.rect(17, 8, 24, 8, 0.0)
    else:
        s.rect(20, 8, 21, 8, 0.0)
        if kind == "door":
            s.rect(20, 8, 21, 8, 0.8)
        elif kind == "window":
            s.rect(20, 8, 21, 8, 0.2)
    s.rect(30, 3, 30, 6, 1.0)
    s.rect(6, 12, 7, 13, 1.0)
    eye = (820.0, 700.0)
    return s, eye


def row(img, ysub, x0, x1):
    return [img[ysub][x] for x in range(x0, x1 + 1)]


def col(img, xsub, y0, y1):
    return [img[y][xsub] for y in range(y0, y1 + 1)]


def steps(v):
    return [abs(v[i + 1] - v[i]) for i in range(len(v) - 1)]


def describe(name, v):
    if not v:
        return
    st = steps(v)
    print("    %-26s n=%3d range[%3d..%3d] distinct=%2d maxstep=%3d mean|d|=%5.1f"
          % (name, len(v), min(v), max(v), len(set(v)), max(st) if st else 0,
             (sum(st) / len(st)) if st else 0))


def inner_raw_stats(scene, raw):
    dim_a = int(round((1 - CFG["dim"]) * 255))
    vals = [raw[ty * G + sy][tx * G + sx]
            for ty in range(1, 8) for tx in range(1, 39)
            if scene.opac[tx][ty] < 1
            for sy in range(G) for sx in range(G)]
    lit = [v for v in vals if v != dim_a and v != 255]
    from collections import Counter
    if not lit:
        return "no lit pixels"
    top = Counter(lit).most_common(1)[0]
    return ("lit n=%d range[%d..%d] distinct=%d single-value-share=%.0f%%(value %d)"
            % (len(lit), min(lit), max(lit), len(set(lit)),
               100.0 * top[1] / len(lit), top[0]))


def main():
    print("=" * 96)
    print("offline model door-fov-20261104    config =", CFG)
    print("fogSub=%d  CS=%.1f px  BLUR_R=%.2f grid (sigma=%.2f = %.1f world px)"
          % (G, CS, BLUR_R, BLUR_SIGMA, BLUR_SIGMA * CS))
    print("=" * 96)

    results = {}
    for kind in ("wide8", "gap", "door", "window"):
        scene, eye = build_room(kind)
        fov, br = compute_fov(scene, eye)
        trace = {"tile": 0, "lit": 0, "mem": 0, "recalc": 0}
        raw = fill_fog(scene, eye, fov, trace=trace)
        img = blur(raw, BLUR_SIGMA)
        counts = {n: sum(1 for x in range(scene.w) for y in range(scene.h) if fov[x][y] == c)
                  for n, c in (("VISIBLE", FOV_VISIBLE), ("DIM", FOV_DIM), ("NONE", FOV_NONE))}
        print("\n--- scene = %s ---   fov[tiles] %s" % (kind, counts))
        print("    fillFogCache: FOV_DIM whole-tile=%d  fillLitTile=%d  "
              "fillMemory=%d  recalc=%d" % (trace["tile"], trace["lit"],
                                           trace["mem"], trace["recalc"]))
        print("    raw(inner room) %s" % inner_raw_stats(scene, raw))
        inner = [img[ty * G + sy][tx * G + sx]
                 for ty in range(1, 8) for tx in range(1, 39)
                 if scene.opac[tx][ty] < 1
                 for sy in range(G) for sx in range(G)]
        describe("inner alpha(lit, blurred)", [v for v in inner if v < 200])
        aps = [(20, 8), (21, 8)] if kind != "wide8" else [(17, 8), (20, 8), (24, 8)]
        ap = [raw[8 * G + sy][tx * G + sx] for tx, _ in aps
              for sy in range(G) for sx in range(G)]
        wl, wr = (16 if kind == "wide8" else 19), (25 if kind == "wide8" else 22)
        wallL = [raw[8 * G + sy][wl * G + sx] for sy in range(G) for sx in range(G)]
        wallR = [raw[8 * G + sy][wr * G + sx] for sy in range(G) for sx in range(G)]
        print("    raw aperture tiles %s alpha=%s" % (aps, sorted(set(ap))))
        print("    raw left wall(%d,8)=%d..%d  right wall(%d,8)=%d..%d"
              % (wl, min(wallL), max(wallL), wr, min(wallR), max(wallR)))
        describe("edge profile y=4 (x=12..29)", row(img, 4 * G + G // 2, 12 * G, 29 * G))
        describe("vertical x=20.5 (y=1..12)", col(img, 20 * G + G // 2, 1 * G, 12 * G))
        # 光轴上的空间剖面（内室 row1..7，x=20.5）—— 平顶 vs 渐变的最直接证据
        axis_raw = col(raw, 20 * G + G // 2, 1 * G, 7 * G)
        axis_img = col(img, 20 * G + G // 2, 1 * G, 7 * G)
        print("    beam axis x=20.5 raw   = %s" % (axis_raw,))
        print("    beam axis x=20.5 blur  = %s" % (axis_img,))
        describe("pillar shadow y=13 (x=3..16)", row(img, 13 * G + G // 2, 3 * G, 16 * G))
        seams = []
        for ty in range(scene.h):
            for tx in range(scene.w - 1):
                a = img[ty * G + G // 2][tx * G + G - 1]
                b = img[ty * G + G // 2][(tx + 1) * G]
                seams.append((abs(b - a), tx, ty, a, b))
        seams.sort(reverse=True)
        print("    tile-boundary seams max3: " +
              "; ".join("%d@(%d,%d)%d->%d" % s for s in seams[:3]))
        results[kind] = dict(fov=fov, raw=raw, img=img, trace=trace, seams=seams)

    # ------------------------------------------- counterfactual
    print("\n" + "=" * 96)
    print("counterfactual: (1) target opacity charged once  (2) translucent tiles not")
    print("                promoted to FOV_VISIBLE by the wall-visibility pass")
    print("=" * 96)
    for kind in ("door", "window"):
        scene, eye = build_room(kind)
        fov, _ = compute_fov(scene, eye, fix_double=True, no_promote_translucent=True)
        raw = fill_fog(scene, eye, fov, fix_double=True)
        print("  %-7s raw(inner) %s" % (kind, inner_raw_stats(scene, raw)))
        print("          fov DIM tiles=%d  aperture raw alpha=%s"
              % (sum(1 for x in range(scene.w) for y in range(scene.h)
                     if fov[x][y] == FOV_DIM),
                 sorted(set(raw[8 * G + sy][20 * G + sx]
                            for sy in range(G) for sx in range(G)))))

    # ------------------------------------------------------ problem B
    print("\n" + "=" * 96)
    print("problem B: origin-cell exemption -- when the eye's own cell is opaque, that cell")
    print("           is never charged, so the whole wall around the eye stops blocking")
    print("=" * 96)
    s = Scene(40, 20)
    s.rect(0, 0, 39, 0, 1.0)
    s.rect(0, 19, 39, 19, 1.0)
    s.rect(0, 0, 0, 19, 1.0)
    s.rect(39, 0, 39, 19, 1.0)
    s.rect(1, 6, 38, 6, 1.0)           # 横墙 row6 -> 世界 y 240..280
    print("player unit = littlepip, phis sX=50 sY=70 (AllData.as:20-24) -> box 50x70 standing,")
    print("                                  sitX=stayX=50, sitY=stayY/2=35 (Unit.as:1037-1044)")
    print("RV eye offsets (checks-06, 6 poses), relative to feet:")
    print("   eyeX-gg.X in [-22.1,+22.1]   eyeY-gg.Y in [-52.8,-62.4]  (old=(X, Y-0.75*scY), scY=70)")
    print("=> standing: eye is 7.6..17.2px BELOW the box top  -> always inside the box -> free cell")
    print("=> sitting : box top = Y-35, so the same head height is 17.8..27.4px ABOVE the box top")
    print("            and the shorter box lets the player get 35px closer to the wall.\n")
    cases = [
        ("standing  box top = wall bottom (Y=350)", 350.0, 70.0),
        ("sitting   box top = wall bottom (Y=315)", 315.0, 35.0),
    ]
    for label, feet_y, box_h in cases:
        feet_x = 20 * TILE + 20.0
        eye = (feet_x + 22.1, feet_y - 62.4)      # 最不利：朝向 + 抬头
        cell = (int(eye[0] // TILE), int(eye[1] // TILE))
        op = s.tile_opac(cell[0], cell[1])
        fov_as3, _ = compute_fov(s, eye)
        lit_tiles = [(x, y) for x in range(s.w) for y in range(s.h)
                     if s.opac[x][y] < 1 and fov_as3[x][y] != FOV_NONE]
        behind = [t for t in lit_tiles if t[1] < 6]          # 墙上方（墙后）的瓦片
        img_as3 = blur(fill_fog(s, eye, fov_as3), BLUR_SIGMA)
        img_fix = blur(fill_fog(s, eye, fov_as3, guard="fixed"), BLUR_SIGMA)
        ndiff = sum(1 for y in range(len(img_as3)) for x in range(len(img_as3[0]))
                    if abs(img_as3[y][x] - img_fix[y][x]) >= 40)
        print("  %-40s box=[%.0f..%.0f]x[%.0f..%.0f]"
              % (label, feet_x - 25, feet_x + 25, feet_y - box_h, feet_y))
        print("      eye=(%.1f,%.1f) cell=%s opac=%.1f  %s"
              % (eye[0], eye[1], cell, op,
                 "  <-- EYE INSIDE THE WALL" if op >= 1 else ""))
        print("      lit non-wall tiles=%d ; tiles BEYOND the wall (row<6)=%d ; "
              "pixels with alpha delta>=40 vs counterfactual=%.1f%%"
              % (len(lit_tiles), len(behind),
                 100.0 * ndiff / (len(img_as3) * len(img_as3[0]))))
        results["leak_" + ("stand" if box_h > 40 else "sit")] = dict(img=img_as3)

    print("\n  note: same exemption also skips semi-transparent origin cells (water/tileop):")
    print("        a 0.5 water tile under the eye contributes 0 instead of 0.5, so every")
    print("        distance value in that room is 0.5 brighter than it should be (lit 1.0 vs 0.5).")

    if "--png" in sys.argv:
        try:
            from PIL import Image
        except Exception as e:
            print("PNG skipped:", e)
            return
        for name, d in results.items():
            img = d["img"]
            hh, ww = len(img), len(img[0])
            im = Image.new("L", (ww, hh))
            im.putdata([255 - img[y][x] for y in range(hh) for x in range(ww)])
            im = im.resize((ww * 8, hh * 8), Image.NEAREST)
            p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "field-%s.png" % name)
            im.save(p)
            print("wrote", p)


if __name__ == "__main__":
    main()
