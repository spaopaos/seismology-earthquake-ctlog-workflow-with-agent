#!/usr/bin/env python3
"""Regenerate docs/images/catalog-pipeline-dark.png (3200x1800 px, dark theme).

The previous figure's style was reverse-engineered pixel-by-pixel (palette,
geometry, type sizes, connector gradients) and is reproduced here, with two
new modules added in the same style:

  09 SKHASH    - PhaseNet+ polarity + S/P ratios -> A/B/C/D-graded focal
                 mechanisms; branches off the catalog chain after stage 08
                 (skills/seismic-focal-mechanism).
  10 InSARHub  - Sentinel-1 + HyP3 cloud GAMMA coseismic capture; a parallel
                 track fed from the catalog rail (M >= 4.5 event selection),
                 delivered as an independent output (skills/seismic-insar).

The header counter is updated 8 -> 10 STAGES (the only change to original
text, required by the new module count).

Style reference (measured from the original PNG):
  - canvas 3200x1800, background pure #000000
  - boxes: fill #1c1c1e, 2px border #3a3a3c, corner radius 30, 530x302 px
  - circular 68px badge per box, solid accent fill, white number
  - palette: iOS dark-mode system colors (see constants below)
  - box-to-box connectors: 8px gradient strip source-accent -> target-accent
    with a 20x20 solid arrowhead in the target color
  - catalog fan-out: gray (#48484a) rail with drops and small arrowheads
  - three stadium output pills; third pill filled blue->purple gradient

Typography: sans-serif (Segoe UI on Windows / DejaVu Sans elsewhere), sizes
auto-calibrated at runtime against the measured pixel widths of the original.

Usage: python catalog-pipeline-dark.py [out.png]     (CPU only, Agg backend)
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Polygon
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.font_manager import FontProperties
from PIL import ImageFont

# ----------------------------------------------------------------------------
# palette (iOS dark-mode system colors, measured from the original PNG)
# ----------------------------------------------------------------------------
BG = '#000000'
BOX_FILL = '#1c1c1e'
BOX_EDGE = '#3a3a3c'
TEXT_MAIN = '#f1f1f3'
TEXT_SUB = '#98989d'
GRAY_BADGE = '#8e8e93'
STRUCT_GRAY = '#48484a'
PILL1_EDGE = '#636366'
BLUE = '#0a84ff'
CYAN = '#64d2ff'
GREEN = '#30d158'
YELLOW = '#ffd60a'
ORANGE = '#ff9f0a'
PINK = '#ff375f'
PURPLE = '#bf5af2'
INDIGO = '#5e5ce6'   # NEW 09 SKHASH
TEAL = '#6ac4dc'     # NEW 10 InSARHub
WHITE = '#ffffff'

# ----------------------------------------------------------------------------
# geometry (pixels; y grows downward)
# ----------------------------------------------------------------------------
W, H = 3200, 1800
COLS = [159, 747, 1335, 1923, 2511]
BOX_W, BOX_H, BOX_R = 530, 302, 30
ROW1_Y, ROW2_Y = 599, 1059
BADGE_D = 68
TITLE_DX, TITLE_DY = 133, 88
SUB_DX = 41           # body lines align with the badge circle's left edge
SUB_DYS = [158, 205, 252]
CONN_Y1, CONN_Y2 = 749.5, 1208.5
CONN_T = 8
HEAD_L, HEAD_H = 20, 20
PILL_Y0, PILL_H, PILL_R = 1522, 147, 73.5
RAIL_Y = 1453.5
PX2PT = 0.72          # fontsize is in points; dpi=100 -> 1pt = 1.389px

# ----------------------------------------------------------------------------
# fonts
# ----------------------------------------------------------------------------
_WINDIR = os.environ.get('WINDIR', r'C:\Windows')
_MPLF = os.path.join(matplotlib.get_data_path(), 'fonts', 'ttf')

ROLES = {
    # role: (preferred windows file, fallback matplotlib file)
    'semibold': (os.path.join(_WINDIR, 'Fonts', 'seguisb.ttf'), os.path.join(_MPLF, 'DejaVuSans-Bold.ttf')),
    'bold': (os.path.join(_WINDIR, 'Fonts', 'segoeuib.ttf'), os.path.join(_MPLF, 'DejaVuSans-Bold.ttf')),
    'regular': (os.path.join(_WINDIR, 'Fonts', 'segoeui.ttf'), os.path.join(_MPLF, 'DejaVuSans.ttf')),
}


def resolve_fonts():
    """Pick the first existing TTF per role; return {role: path}."""
    out = {}
    for role, (pref, fb) in ROLES.items():
        out[role] = pref if os.path.exists(pref) else fb
    return out


FONTS = resolve_fonts()
_PIL_CACHE = {}
_SUP = 4  # supersample font metrics for sub-pixel accuracy


def pil_font(role, size_px):
    """Font object at size_px*_SUP px; callers divide metrics by _SUP."""
    key = (role, round(size_px * _SUP))
    if key not in _PIL_CACHE:
        _PIL_CACHE[key] = ImageFont.truetype(FONTS[role], round(size_px * _SUP))
    return _PIL_CACHE[key]


def ink_w(role, s, size_px):
    bb = pil_font(role, size_px).getbbox(s)
    return (bb[2] - bb[0]) / _SUP


def ink_x0(role, s, size_px):
    return pil_font(role, size_px).getbbox(s)[0] / _SUP


def adv_w(role, s, size_px):
    return pil_font(role, size_px).getlength(s) / _SUP


def cap_h(role, size_px):
    bb = pil_font(role, size_px).getbbox('H')
    return (bb[3] - bb[1]) / _SUP


def solve_size_for_width(role, s, target_w, lo=4.0, hi=400.0):
    for _ in range(60):
        mid = (lo + hi) / 2
        if ink_w(role, s, mid) < target_w:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def solve_size_for_cap(role, target_cap, lo=4.0, hi=400.0):
    for _ in range(60):
        mid = (lo + hi) / 2
        if cap_h(role, mid) < target_cap:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def fp(role, size_px):
    return FontProperties(fname=FONTS[role], size=size_px * PX2PT)


def text(ax, x, y, s, role, size_px, color, ha='left', zorder=6, size_pt=None):
    ax.text(x, y, s, fontproperties=fp(role, size_px) if size_pt is None
            else FontProperties(fname=FONTS[role], size=size_pt),
            color=color, ha=ha, va='baseline', zorder=zorder)


def tracked_text(ax, s, x, y, role, size_px, color, target_ink, zorder=6):
    """Per-character text with uniform tracking factor to hit target width."""
    f = pil_font(role, size_px)
    nat = (f.getbbox(s)[2] - f.getbbox(s)[0]) / _SUP
    k = target_ink / nat
    adv = [0.0]
    for ch in s[:-1]:
        adv.append(adv[-1] + f.getlength(ch) / _SUP)
    x0_off = f.getbbox(s)[0] / _SUP
    for ch, a in zip(s, adv):
        if ch != ' ':
            ax.text(x + (k * a - x0_off), y, ch, fontproperties=fp(role, size_px),
                    color=color, ha='left', va='baseline', zorder=zorder)


def letterspaced_text(ax, s, x, y, role, size_px, color, target_ink,
                      right_align=False, zorder=6):
    """All-caps label with uniform letterspacing to hit target width."""
    f = pil_font(role, size_px)
    nat = f.getlength(s) / _SUP
    ls = (target_ink - nat) / len(s)
    if right_align:
        x = x - target_ink
    for ch in s:
        ax.text(x, y, ch, fontproperties=fp(role, size_px), color=color,
                ha='left', va='baseline', zorder=zorder)
        x += f.getlength(ch) / _SUP + ls


# ----------------------------------------------------------------------------
# shapes / connectors
# ----------------------------------------------------------------------------
def hex2rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def grad_strip_h(ax, xa, xb, y, thick, ca, cb, zorder=4):
    n = 256
    cmap = LinearSegmentedColormap.from_list(
        'g', np.linspace(hex2rgb(ca), hex2rgb(cb), n) / 255.0)
    grad = np.linspace(0, 1, n)[:, None].repeat(2, axis=1)
    ax.imshow(grad, cmap=cmap, extent=(xa, xb, y + thick / 2, y - thick / 2),
              aspect='auto', interpolation='nearest', zorder=zorder)


def grad_strip_v(ax, ya, yb, x, thick, ca, cb, zorder=4):
    n = 256
    cmap = LinearSegmentedColormap.from_list(
        'g', np.linspace(hex2rgb(ca), hex2rgb(cb), n) / 255.0)
    grad = np.linspace(0, 1, n)[:, None].repeat(2, axis=1)
    ax.imshow(grad, cmap=cmap, extent=(x - thick / 2, x + thick / 2, yb, ya),
              aspect='auto', interpolation='nearest', zorder=zorder)


def head_right(ax, x, y, color, L=HEAD_L, hh=HEAD_H / 2, zorder=5):
    ax.add_patch(Polygon([[x, y], [x - L, y - hh], [x - L, y + hh]], closed=True,
                         facecolor=color, edgecolor=color, lw=1, zorder=zorder))


def head_left(ax, x, y, color, L=HEAD_L, hh=HEAD_H / 2, zorder=5):
    ax.add_patch(Polygon([[x, y], [x + L, y - hh], [x + L, y + hh]], closed=True,
                         facecolor=color, edgecolor=color, lw=1, zorder=zorder))


def head_down(ax, x, y, color, L=HEAD_H, hw=HEAD_H / 2, zorder=5):
    ax.add_patch(Polygon([[x, y], [x - hw, y - L], [x + hw, y - L]], closed=True,
                         facecolor=color, edgecolor=color, lw=1, zorder=zorder))


def head_up(ax, x, y, color, L=HEAD_H, hw=HEAD_H / 2, zorder=5):
    ax.add_patch(Polygon([[x, y], [x - hw, y + L], [x + hw, y + L]], closed=True,
                         facecolor=color, edgecolor=color, lw=1, zorder=zorder))


def connector_h(ax, x_src, x_tgt, y, c_src, c_tgt, leftward=False):
    if leftward:
        grad_strip_h(ax, x_tgt, x_src, y, CONN_T, c_tgt, c_src)
        head_left(ax, x_tgt - 0.5, y, c_tgt)
    else:
        grad_strip_h(ax, x_src, x_tgt, y, CONN_T, c_src, c_tgt)
        head_right(ax, x_tgt + 0.5, y, c_tgt)


def gray_line(ax, x0, y0, x1, y1):
    ax.plot([x0, x1], [y0, y1], color=STRUCT_GRAY, lw=2.8,
            solid_capstyle='butt', zorder=3)


# ----------------------------------------------------------------------------
# calibrated type sizes (solved at runtime against the original's ink widths)
# ----------------------------------------------------------------------------
SIZES = {}


def calibrate():
    S = SIZES
    S['headline'] = solve_size_for_cap('semibold', 78.0)
    S['title'] = solve_size_for_cap('bold', 26.0)
    S['sub'] = solve_size_for_width('regular', 'Adaptive ingestion · fixed config', 290.0)
    S['subtitle'] = solve_size_for_width(
        'regular',
        'PhaseNet+ · GaMMA · HYPOINVERSE · HypoDD · PALM — detection, '
        'association, and relocation in one pipeline', 1638.0)
    S['hdrlabel'] = solve_size_for_cap('regular', 19.0)
    S['pillmain'] = solve_size_for_width('bold', 'Catalog · CC ≥ 0.4', 288.0)
    S['pillsec'] = solve_size_for_width('regular', 'maximum recall', 161.0)
    S['footer'] = solve_size_for_width(
        'regular',
        'CC = waveform cross-correlation · CT = catalog time · '
        'thresholds user-selectable', 837.0)
    S['badge'] = solve_size_for_cap('bold', 21.0)
    return S


# ----------------------------------------------------------------------------
# element painters
# ----------------------------------------------------------------------------
def draw_box(ax, x, y, badge_color, number, title, subs, title_ink):
    ax.add_patch(FancyBboxPatch((x + BOX_R, y + BOX_R + 0.5), BOX_W - 2 * BOX_R,
                                BOX_H - 2 * BOX_R - 1.0,
                                boxstyle='round,pad=%d,rounding_size=%d' % (BOX_R, BOX_R),
                                facecolor=BOX_FILL, edgecolor=BOX_EDGE, lw=2.0,
                                zorder=2))
    cx, cy = x + 41 + BADGE_D / 2, y + 41 + BADGE_D / 2
    ax.add_patch(Circle((cx, cy), BADGE_D / 2, facecolor=badge_color,
                        edgecolor='none', zorder=3))
    # number centered on the badge (ink-bbox centering; metrics are supersampled)
    f = pil_font('bold', SIZES['badge'])
    bx0, by0, bx1, by1 = [v / _SUP for v in f.getbbox(number)]
    # dark digits on light fills (cyan/yellow in the original), white otherwise
    r, g, b = hex2rgb(badge_color)
    digit_color = BOX_FILL if (0.299 * r + 0.587 * g + 0.114 * b) >= 160 else WHITE
    ax.text(cx - (bx0 + bx1) / 2, cy + (by1 - by0) / 2, number,
            fontproperties=fp('bold', SIZES['badge']), color=digit_color,
            ha='left', va='baseline', zorder=4)
    tracked_text(ax, title, x + TITLE_DX, y + TITLE_DY, 'bold', SIZES['title'],
                 TEXT_MAIN, title_ink)
    for i, s_ in enumerate(subs):
        text(ax, x + SUB_DX, y + SUB_DYS[i], s_, 'regular', SIZES['sub'], TEXT_SUB)


def build(out_path):
    calibrate()

    fig = plt.figure(figsize=(32, 18), dpi=100)
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis('off')

    # ---- header ---------------------------------------------------------
    letterspaced_text(ax, 'SEISMIC CATALOG WORKFLOW', 173, 153.5, 'regular',
                      SIZES['hdrlabel'], TEXT_SUB, 642)
    letterspaced_text(ax, '10 STAGES · 3 CATALOG TIERS', 3026, 153.5, 'regular',
                      SIZES['hdrlabel'], TEXT_SUB, 622, right_align=True)
    tracked_text(ax, 'Waveforms in. Catalog out.', 160, 288.5, 'semibold',
                 SIZES['headline'], TEXT_MAIN, 1268)
    text(ax, 160, 375,
         'PhaseNet+ · GaMMA · HYPOINVERSE · HypoDD · PALM — detection, '
         'association, and relocation in one pipeline',
         'regular', SIZES['subtitle'] * 1.012, TEXT_SUB)

    # ---- module boxes ----------------------------------------------------
    TITLE_INKS = {  # measured ink widths of the original titles
        'Raw Waveforms': 266, 'Preprocess': 184, 'PhaseNet+': 173, 'GaMMA': 133,
        'HYPOINVERSE': 252, 'HypoDD · R1': 202, 'PALM MESS': 205,
        'HypoDD · R2': 204, 'SKHASH': 150, 'InSARHub': 150,
    }
    boxes = [
        (0, ROW1_Y, GRAY_BADGE, '01', 'Raw Waveforms',
         ['Continuous waveform data', 'any layout · any format']),
        (1, ROW1_Y, BLUE, '02', 'Preprocess',
         ['Adaptive ingestion · fixed config', '100 Hz · m/s · 1–40 Hz',
          'Z/N/E per UTC day']),
        (2, ROW1_Y, CYAN, '03', 'PhaseNet+',
         ['P/S phase arrivals', '+ first-motion polarity']),
        (3, ROW1_Y, GREEN, '04', 'GaMMA',
         ['DBSCAN association', 'eps — user-confirmed']),
        (4, ROW1_Y, YELLOW, '05', 'HYPOINVERSE',
         ['Absolute location', 'version 1.40']),
        (4, ROW2_Y, ORANGE, '06', 'HypoDD · R1',
         ['Catalog-time (CT) relocation', 'DAMP trials']),
        (3, ROW2_Y, PINK, '07', 'PALM MESS',
         ['Matched-filter detection', 'new event detections']),
        (2, ROW2_Y, PURPLE, '08', 'HypoDD · R2',
         ['Joint CC + CT relocation', 'CT from independent',
          'PhaseNet+ arrivals']),
        # ---- NEW modules ---------------------------------------------------
        (1, ROW2_Y, INDIGO, '09', 'SKHASH',
         ['Focal mechanisms · grid search', 'PhaseNet+ polarity + S/P ratios',
          'A/B/C/D-graded catalog']),
        (0, ROW2_Y, TEAL, '10', 'InSARHub',
         ['Coseismic deformation capture', 'Sentinel-1 SLC · HyP3 cloud GAMMA',
          'LOS maps · M ≥ 4.5 events']),
    ]
    for col, ytop, bc, num, title, subs in boxes:
        draw_box(ax, COLS[col], ytop, bc, num, title, subs, TITLE_INKS[title])

    # ---- box-to-box gradient connectors ----------------------------------
    connector_h(ax, COLS[0] + BOX_W + 0.5, COLS[1] - 1, CONN_Y1, GRAY_BADGE, BLUE)
    connector_h(ax, COLS[1] + BOX_W + 0.5, COLS[2] - 1, CONN_Y1, BLUE, CYAN)
    connector_h(ax, COLS[2] + BOX_W + 0.5, COLS[3] - 1, CONN_Y1, CYAN, GREEN)
    connector_h(ax, COLS[3] + BOX_W + 0.5, COLS[4] - 1, CONN_Y1, GREEN, YELLOW)
    vx = COLS[4] + BOX_W / 2                       # 05 -> 06 snake drop
    grad_strip_v(ax, ROW1_Y + BOX_H + 0.5, ROW2_Y - HEAD_H - 1, vx, CONN_T,
                 YELLOW, ORANGE)
    head_down(ax, vx, ROW2_Y - 1.5, ORANGE)
    connector_h(ax, COLS[4] - 0.5, COLS[3] + BOX_W + 1, CONN_Y2, ORANGE, PINK,
                leftward=True)
    connector_h(ax, COLS[3] - 0.5, COLS[2] + BOX_W + 1, CONN_Y2, PINK, PURPLE,
                leftward=True)
    # NEW: 08 -> 09 (SKHASH branch off the catalog chain)
    connector_h(ax, COLS[2] - 0.5, COLS[1] + BOX_W + 1, CONN_Y2, PURPLE, INDIGO,
                leftward=True)

    # ---- catalog fan-out rail -> three tier pills -------------------------
    drop_x = COLS[2] + BOX_W / 2
    gray_line(ax, drop_x, ROW2_Y + BOX_H + 1, drop_x, RAIL_Y)
    gray_line(ax, 423.5, RAIL_Y, 2760, RAIL_Y)
    for pc in [639.5, 1599.5, 2759.5]:             # 2759.5 kept from original
        gray_line(ax, pc, RAIL_Y, pc, RAIL_Y + 50)
        head_down(ax, pc, PILL_Y0 - 4, STRUCT_GRAY, L=14, hw=7)
    # NEW: rail branch feeding InSAR event selection (M >= 4.5)
    gray_line(ax, 423.5, RAIL_Y, 423.5, ROW2_Y + BOX_H + 15)
    head_up(ax, 423.5, ROW2_Y + BOX_H + 1.5, STRUCT_GRAY, L=14, hw=7)

    # ---- output pills ------------------------------------------------------
    pills = [
        (198, 883, 'Catalog · CC ≥ 0.4', 'maximum recall', TEXT_MAIN, TEXT_SUB, PILL1_EDGE),
        (1158, 883, 'Catalog · CC ≥ 0.6', 'balanced', TEXT_MAIN, TEXT_SUB, BLUE),
        (2120, 880, 'Catalog · CC ≥ 0.8', 'highest confidence', WHITE, WHITE, None),
    ]
    for x0, w_, main, sec, c_main, c_sec, edge in pills:
        cx = x0 + w_ / 2
        patch = FancyBboxPatch((x0 + PILL_R, PILL_Y0 + PILL_R),
                               w_ - 2 * PILL_R, PILL_H - 2 * PILL_R,
                               boxstyle='round,pad=%.1f,rounding_size=%.1f' % (PILL_R, PILL_R),
                               facecolor=BOX_FILL if edge else 'none',
                               edgecolor=edge or 'none',
                               lw=2.4 if edge else 0, zorder=2)
        ax.add_patch(patch)
        if edge is None:                            # blue -> purple gradient fill
            n = 512
            cmap = LinearSegmentedColormap.from_list(
                'p3', np.linspace(hex2rgb(BLUE), hex2rgb(PURPLE), n) / 255.0)
            grad = np.linspace(0, 1, n)[None, :].repeat(8, axis=0)
            im = ax.imshow(grad, cmap=cmap, extent=(x0, x0 + w_, PILL_Y0 + PILL_H, PILL_Y0),
                           aspect='auto', interpolation='nearest', zorder=2)
            im.set_clip_path(patch)
        text(ax, cx, 1589, main, 'bold', SIZES['pillmain'], c_main, ha='center')
        text(ax, cx, 1629, sec, 'regular', SIZES['pillsec'], c_sec, ha='center')

    # ---- footer ------------------------------------------------------------
    text(ax, 158, 1744,
         'CC = waveform cross-correlation · CT = catalog time · '
         'thresholds user-selectable',
         'regular', SIZES['footer'], TEXT_SUB)

    fig.savefig(out_path, dpi=100, facecolor=BG)
    plt.close(fig)
    print('fonts used:', {r: os.path.basename(p) for r, p in FONTS.items()})
    print('calibrated sizes (px):', {k: round(v, 1) for k, v in SIZES.items()})
    print('written', out_path)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'catalog-pipeline-dark.png')
    build(out)
