#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v0.34.9-fov-correct 的离线行为断言（不启动游戏）。

用 tools/door-fov-20261104/model.py 的算术模型，把"改动前（v0.34.8）的语义"与
"改动后的语义"逐条对照。每条断言对应方案里的一条缺陷编号；失败即非 0 退出。

run:  python checks.py
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
FOV_NONE, FOV_DIM, FOV_VISIBLE = M.FOV_NONE, M.FOV_DIM, M.FOV_VISIBLE
RESULTS = []


def check(ok, name, detail=''):
    RESULTS.append((bool(ok), name))
    print(('PASS  ' if ok else 'FAIL  ') + name + ('   ' + detail if detail else ''))


def empty_trace():
    return {'tile': 0, 'lit': 0, 'mem': 0, 'recalc': 0}


def wall_scene():
    """40x20，横墙 row6 全宽。"""
    s = M.Scene(40, 20)
    s.rect(0, 0, 39, 0, 1.0)
    s.rect(0, 19, 39, 19, 1.0)
    s.rect(0, 0, 0, 19, 1.0)
    s.rect(39, 0, 39, 19, 1.0)
    s.rect(1, 6, 38, 6, 1.0)
    return s


def lit_beyond(scene, fov, row=6):
    return sum(1 for x in range(scene.w) for y in range(scene.h)
               if scene.opac[x][y] < 1 and fov[x][y] != FOV_NONE and y < row)


def tile_values(raw, tx, ty, sub=4):
    return sorted({raw[ty * sub + sy][tx * sub + sx] for sy in range(sub) for sx in range(sub)})


def main():
    s = wall_scene()
    eye_free = (20 * TILE + 22.1, 350.0 - 62.4)
    eye_wall = (20 * TILE + 22.1, 315.0 - 62.4)

    fov_free, _ = M.compute_fov(s, eye_free)
    fov_wall, _ = M.compute_fov(s, eye_wall)
    check(s.tile_opac(int(eye_free[0] // TILE), int(eye_free[1] // TILE)) == 0
          and lit_beyond(s, fov_free) == 0,
          'F-1a 站立（眼点在自由格）墙后 0 格被点亮',
          'beyond=%d' % lit_beyond(s, fov_free))
    check(s.tile_opac(int(eye_wall[0] // TILE), int(eye_wall[1] // TILE)) >= 1
          and lit_beyond(s, fov_wall) > 0,
          'F-1b 坐姿（眼点落进墙瓦片）复现"墙后视野"',
          'beyond=%d  (v0.34.8 语义)' % lit_beyond(s, fov_wall))

    feet, sc_stand, sc_sit = (20 * TILE + 20.0, 315.0), (50.0, 70.0), (50.0, 35.0)
    for label, sc in (('站立', sc_stand), ('坐姿', sc_sit)):
        clamped = M.sanitize_eye(s, feet, sc, eye_wall)
        cell = (int(clamped[0] // TILE), int(clamped[1] // TILE))
        fov_c, _ = M.compute_fov(s, clamped)
        check(s.tile_opac(cell[0], cell[1]) <= 0 and lit_beyond(s, fov_c) == 0,
              'C-Eye-1 %s：钳制后眼点在自由格、墙后 0 格' % label,
              'cell=%s opac=%.1f beyond=%d' % (cell, s.tile_opac(cell[0], cell[1]),
                                               lit_beyond(s, fov_c)))

    s2 = M.Scene(40, 20)
    s2.rect(0, 0, 39, 0, 1.0)
    s2.rect(0, 19, 39, 19, 1.0)
    s2.rect(0, 0, 0, 19, 1.0)
    s2.rect(39, 0, 39, 19, 1.0)
    s2.rect(1, 12, 38, 12, 1.0)
    eye2 = (20 * TILE + 20.0, 15 * TILE + 20.0)
    target = (20 * TILE + 20.0, 12 * TILE + 20.0)
    cell2 = (20, 12)

    s2.rect(20, 12, 21, 12, 0.8)
    rv_door = M.cast_ray(s2, eye2, target, cell2)
    fix_door = M.cast_ray(s2, eye2, target, cell2, fix_double=True)
    check(abs(rv_door - 0.05) < 1e-9 and abs(fix_door - 0.2) < 1e-9,
          'F-6/C-Ray-1 木门目标格：v0.34.8=0.05 -> 只扣一次=0.2',
          'rv=%.4f fixed=%.4f' % (rv_door, fix_door))

    s2.rect(20, 12, 21, 12, 0.2)
    rv_win = M.cast_ray(s2, eye2, target, cell2)
    fix_win = M.cast_ray(s2, eye2, target, cell2, fix_double=True)
    check(abs(rv_win - 0.6) < 1e-9 and abs(fix_win - 0.8) < 1e-9,
          'F-6/C-Ray-1 窗目标格：0.6（恰贴 litmin）-> 0.8',
          'rv=%.4f fixed=%.4f' % (rv_win, fix_win))

    scene_d, eye_d = M.build_room('door')
    raw_d_rv = M.fill_fog(scene_d, eye_d, M.compute_fov(scene_d, eye_d)[0])
    fov_d_fix, _ = M.compute_fov(scene_d, eye_d, no_promote_translucent=True)
    raw_d_fix = M.fill_fog(scene_d, eye_d, fov_d_fix, fix_double=True)
    check(max(tile_values(raw_d_rv, 20, 8)) <= 30 and tile_values(raw_d_fix, 20, 8) == [38],
          'F-3/C-Ap-1 木门叶面：v0.34.8 几乎无雾 -> 恢复门景口径 38',
          'rv=%s fixed=%s' % (tile_values(raw_d_rv, 20, 8)[:4], tile_values(raw_d_fix, 20, 8)))

    scene_w, eye_w = M.build_room('window')
    raw_w_rv = M.fill_fog(scene_w, eye_w, M.compute_fov(scene_w, eye_w)[0])
    fov_w_fix, _ = M.compute_fov(scene_w, eye_w, no_promote_translucent=True)
    raw_w_fix = M.fill_fog(scene_w, eye_w, fov_w_fix, fix_double=True)
    check(fov_w_fix[20][8] == FOV_VISIBLE
          and tile_values(raw_w_fix, 20, 8) == tile_values(raw_w_rv, 20, 8),
          'F-3 窗（lit 0.8 >= litmin）：批次 1 后仍走 FOV_VISIBLE，叶面留给批次 2 的 C-Ap-4',
          'rv=%s fixed=%s fov=%d' % (tile_values(raw_w_rv, 20, 8)[:4],
                                     tile_values(raw_w_fix, 20, 8)[:4], fov_w_fix[20][8]))

    big = M.Scene(60, 12)
    big.rect(0, 0, 59, 0, 1.0)
    big.rect(0, 11, 59, 11, 1.0)
    big.rect(0, 0, 0, 11, 1.0)
    big.rect(59, 0, 59, 11, 1.0)
    eye_big = (2 * TILE, 2 * TILE)
    fov_big, _ = M.compute_fov(big, eye_big)
    tr_off, tr_on = empty_trace(), empty_trace()
    M.fill_fog(big, eye_big, fov_big, trace=tr_off, radius_guard=False)
    M.fill_fog(big, eye_big, fov_big, trace=tr_on, radius_guard=True)
    check(tr_off['seenFar'] > 0 and tr_on['seenFar'] == 0,
          'C-Ray-2 半径外的子格不再被标"曾见"（探索溢出修正）',
          'seenFar off=%d on=%d（seen %d -> %d）'
          % (tr_off['seenFar'], tr_on['seenFar'], tr_off['seen'], tr_on['seen']))

    bad = [n for ok, n in RESULTS if not ok]
    print('\n%d 项断言，%d 失败' % (len(RESULTS), len(bad)))
    if bad:
        print('FAILED: ' + '; '.join(bad))
        return 1
    print('ALL OFFLINE CHECKS PASSED')
    return 0


if __name__ == '__main__':
    sys.exit(main())
