#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v0.35.0-aperture-grade 的离线行为断言（不启动游戏）。

对应 RV-DESIGN-20261104 §7.2 的四条改动：
  C-Ap-4 lit_fastpath     -- fillLitTile 带上射线亮度（窗/栅格不再被涂成 alpha 0）
  C-Ap-2 aperture_surface -- 透光叶面改用与墙同族的四角双线性（交界连续）
  C-Ap-3 doorgrade        -- 门景从常量平顶改为"近端 doordim、远端 dim"的渐变
  C-Ap-5 door_wall_merge  -- 门景锥内的墙与地板同源（默认关，单独断言）

run:  python checks_b2.py
"""

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = HERE.parents[1]
MODEL_PATH = MOD / 'tools/door-fov-20261104/model.py'

spec = importlib.util.spec_from_file_location('rv_model', MODEL_PATH)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

TILE = M.TILE
G = M.CFG['fog_sub']
FOV_NONE, FOV_DIM, FOV_VISIBLE = M.FOV_NONE, M.FOV_DIM, M.FOV_VISIBLE
DIM_A = int(round((1 - M.CFG['dim']) * 255))
DOOR_A = int(round((1 - M.CFG['doordim']) * 255))
RESULTS = []


def check(ok, name, detail=''):
    RESULTS.append((bool(ok), name))
    print(('PASS  ' if ok else 'FAIL  ') + name + ('   ' + detail if detail else ''))


def tile(raw, tx, ty, sub=None):
    sub = sub or G
    return sorted({raw[ty * sub + sy][tx * sub + sx] for sy in range(sub) for sx in range(sub)})


def seam(raw, tx_left, tx_right, ty, sub=None):
    sub = sub or G
    return abs(raw[ty * sub + sub // 2][tx_right * sub]
               - raw[ty * sub + sub // 2][tx_left * sub + sub - 1])


def scene_window_close():
    """窗离眼只有 ~120px：窗后瓦片落在 lDist1(300px) 内，正好命中 fillLitTile 快路径。"""
    s = M.Scene(24, 14)
    s.rect(0, 0, 23, 0, 1.0)
    s.rect(0, 13, 23, 13, 1.0)
    s.rect(0, 0, 0, 13, 1.0)
    s.rect(23, 0, 23, 13, 1.0)
    s.rect(1, 6, 23, 6, 1.0)
    s.rect(10, 6, 11, 6, 0.2)
    eye = (10 * TILE + 20.0, 9 * TILE + 20.0)
    return s, eye


def scene_door_with_pillar():
    """门后光锥里放一根柱子，用来验证 door_wall_merge。"""
    s = M.Scene(24, 14)
    s.rect(0, 0, 23, 0, 1.0)
    s.rect(0, 13, 23, 13, 1.0)
    s.rect(0, 0, 0, 13, 1.0)
    s.rect(23, 0, 23, 13, 1.0)
    s.rect(1, 6, 23, 6, 1.0)
    s.rect(10, 6, 11, 6, 0.8)
    s.rect(11, 3, 11, 5, 1.0)
    eye = (10 * TILE + 20.0, 9 * TILE + 20.0)
    return s, eye


def prep(scene, eye):
    fov, _ = M.compute_fov(scene, eye, no_promote_translucent=True)
    return fov


def main():
    # ------------------------------------------------ C-Ap-4 快路径带 lit
    scene, eye = scene_window_close()
    fov = prep(scene, eye)
    raw_off = M.fill_fog(scene, eye, fov, fix_double=True)
    raw_on = M.fill_fog(scene, eye, fov, fix_double=True, lit_fastpath=True)
    off_vals = [v for v in tile(raw_off, 10, 5) if v < 200]
    on_vals = [v for v in tile(raw_on, 10, 5) if v < 200]
    check(0 in off_vals and min(on_vals) == round((1 - 0.8) * 255),
          'C-Ap-4 窗后 300px 内：v0.34.9 涂 alpha 0 -> 恢复 (1-lit)*255 = 51',
          'off=%s on=%s' % (tile(raw_off, 10, 5)[:4], tile(raw_on, 10, 5)[:4]))

    scene_w, eye_w = M.build_room('wide8')
    fov_w = prep(scene_w, eye_w)
    off_w = M.fill_fog(scene_w, eye_w, fov_w)
    on_w = M.fill_fog(scene_w, eye_w, fov_w, lit_fastpath=True)
    check(tile(off_w, 20, 4) == tile(on_w, 20, 4),
          'C-Ap-4 开放区域（lit=1）逐位不变',
          'off=%s on=%s' % (tile(off_w, 20, 4)[:3], tile(on_w, 20, 4)[:3]))

    # ------------------------------------------ C-Ap-2 叶面口径与交界连续
    scene_d, eye_d = M.build_room('door')
    fov_d = prep(scene_d, eye_d)
    raw_before = M.fill_fog(scene_d, eye_d, fov_d, fix_double=True)
    raw_after = M.fill_fog(scene_d, eye_d, fov_d, fix_double=True, aperture_surface=True)
    seam_before = seam(raw_before, 19, 20, 8)
    seam_after = seam(raw_after, 19, 20, 8)
    check(seam_after <= 2 and seam_after < seam_before,
          'C-Ap-2 门板与相邻墙在瓦片边界上连续（raw 落差 -> ~0）',
          'seam %d -> %d' % (seam_before, seam_after))
    check(max(tile(raw_after, 20, 8)) > 30 and len(tile(raw_after, 20, 8)) > 1,
          'C-Ap-2 门板不再是无雾亮洞：出现与墙同族的角点梯度（= 原生门板观感）',
          'aperture %s -> %s' % (tile(raw_before, 20, 8)[:3], tile(raw_after, 20, 8)[:6]))

    # ------------------------------------------------ C-Ap-3 门景渐变
    flat = M.fill_fog(scene_d, eye_d, fov_d, fix_double=True, aperture_surface=True,
                      door_grade=0.0)
    grad = M.fill_fog(scene_d, eye_d, fov_d, fix_double=True, aperture_surface=True,
                      door_grade=1.0)
    axis_flat = [flat[y][20 * G + G // 2] for y in range(G, 7 * G)
                 if flat[y][20 * G + G // 2] != 255]
    axis_grad = [grad[y][20 * G + G // 2] for y in range(G, 7 * G)
                 if grad[y][20 * G + G // 2] != 255]
    check(len(set(axis_flat)) <= 2 and len(set(axis_grad)) >= 8,
          'C-Ap-3 门后光轴：常量平顶 -> 距离渐变',
          'distinct %d -> %d ; 远端/近端 %d>>%d -> %d>>%d'
          % (len(set(axis_flat)), len(set(axis_grad)),
             axis_flat[0], axis_flat[-1], axis_grad[0], axis_grad[-1]))
    check(axis_grad[0] > axis_grad[-1],
          'C-Ap-3 门后亮度随距离变暗（远 > 近，alpha 越大越暗）',
          'far %d > near %d' % (axis_grad[0], axis_grad[-1]))

    ddx, ddy = (20.5 * TILE - eye_d[0]), (1.5 * TILE - eye_d[1])
    fo = M.dist_falloff(ddx * ddx + ddy * ddy)
    floor_eff = M.CFG['doordim'] - (M.CFG['doordim'] - M.CFG['dim']) * min(1.0, (1 - fo))
    expect = round((1 - floor_eff) * 255)
    check(abs(axis_grad[0] - expect) <= 2,
          'C-Ap-3 远端与解析式一致（floorEff 从 doordim 渐变到 dim）',
          'model=%d expect=%d (fo=%.3f floorEff=%.3f)' % (axis_grad[0], expect, fo, floor_eff))

    # ------------------------------------ C-Ap-5 door_wall_merge（默认关）
    scene_p, eye_p = scene_door_with_pillar()
    fov_p = prep(scene_p, eye_p)
    off = M.fill_fog(scene_p, eye_p, fov_p, fix_double=True, aperture_surface=True,
                     door_grade=1.0, door_wall_merge=False)
    on = M.fill_fog(scene_p, eye_p, fov_p, fix_double=True, aperture_surface=True,
                    door_grade=1.0, door_wall_merge=True)
    v_off = max(tile(off, 11, 4))
    v_on = max(tile(on, 11, 4))
    check(v_off > v_on and v_on <= DIM_A,
          'C-Ap-5 门景锥内的墙：原生 visi 亮度 -> 地板同源',
          'pillar off=%d on=%d dimA=%d' % (v_off, v_on, DIM_A))
    check(tile(off, 2, 9) == tile(on, 2, 9),
          'C-Ap-5 门景锥外的墙不受影响（开关只影响锥内墙）',
          'outside wall off=%s on=%s' % (tile(off, 2, 9)[:3], tile(on, 2, 9)[:3]))

    bad = [n for ok, n in RESULTS if not ok]
    print('\n%d 项断言，%d 失败' % (len(RESULTS), len(bad)))
    if bad:
        print('FAILED: ' + '; '.join(bad))
        return 1
    print('ALL BATCH-2 OFFLINE CHECKS PASSED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
