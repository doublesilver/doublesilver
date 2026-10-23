"""stats (1280×360) — KPI 6개를 3×2 글래스 타일로. 숫자는 오도미터처럼 굴러 멈추고,
타일마다 네온 링·윗선 진행 막대·빛 스침이 순차로 켜진다."""

from __future__ import annotations

import re

from . import design as D

W, H = 1280, 360
P = "stats"

PAD_X = 56               # 바깥 여백 — domains·terminal 그리드와 같은 값
GAP_X = 16
GAP_Y = 14
GRID_TOP = 66
GRID_BOTTOM = H - 24
MAX_TILES = 6
IN_X = 26                 # 타일 안쪽 글자 시작
RING_R = 23
RING_CY = 44              # 링 중심(타일 로컬), x 는 타일 오른쪽 끝 - 48

APPEAR0 = 120             # 첫 타일 등장(ms)
APPEAR_STEP = 90
ODO_DUR = 1.45            # 오도미터 롤링 길이(s) — 2.5초 안에 모두 멈추게
BASE = 62                 # 숫자 기준선(타일 로컬)
SUB_SPILL = 12            # 보조 문구가 안쪽 여백으로 넘쳐도 되는 폭(페이드로 사라짐)


def _grid(count):
    """개수에 맞는 격자: 1~3개 한 줄, 4개 2×2, 5~6개 3열(마지막 줄 가운데 정렬)."""
    cols = count if count <= 3 else (2 if count == 4 else 3)
    cols = max(cols, 1)
    rows = (count + cols - 1) // cols if count else 1
    tw = (W - PAD_X * 2 - GAP_X * (cols - 1)) / cols
    th = (GRID_BOTTOM - GRID_TOP - GAP_Y * (rows - 1)) / rows
    return {"cols": cols, "rows": rows, "tw": tw, "th": th, "rcx": tw - 48, "count": count}


def _num(v):
    """'12,439' -> 12439.0, 숫자가 없으면 None."""
    m = re.search(r"-?\d[\d,]*(?:\.\d+)?", str(v))
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def _fraction(stat, stats):
    """링에 그릴 비율. 'active' 는 같은 묶음의 'days' 대비 비율, 나머지는 한 바퀴(1.0)."""
    if stat.get("key") == "active":
        days = next((s for s in stats if s.get("key") == "days"), None)
        a, d = _num(stat.get("value")), _num(days.get("value")) if days else None
        if a is not None and d:
            return D.clamp(a / d, 0.02, 1.0)
    return 1.0


# ---------------------------------------------------------------------------
# 아이콘(개념 기호 — 사실 아님). 원점 중심, 약 ±9 단위.
# ---------------------------------------------------------------------------

def _icon(key, col):
    s = f'stroke="{col}" stroke-width="1.8" fill="none" stroke-linecap="round" stroke-linejoin="round"'
    if key == "days":
        return (f'<g {s}><rect x="-8.5" y="-7" width="17" height="15" rx="3"/><path d="M-8.5 -2.2H8.5M-4 -9.5V-5M4 -9.5V-5"/></g>'
                f'<circle cx="-3.4" cy="2.6" r="1.3" fill="{col}"/><circle cx="1" cy="2.6" r="1.3" fill="{col}"/>')
    if key == "repos":
        return (f'<g {s}><circle cx="-5" cy="-6.5" r="2.4"/><circle cx="-5" cy="7" r="2.4"/><circle cx="6" cy="-3" r="2.4"/>'
                f'<path d="M-5 -4.1V4.6M6 -0.6C6 3 -1 2.5 -4.2 5.2"/></g>')
    if key == "commits":
        return f'<g {s}><path d="M-10 0H-4.2M4.2 0H10"/><circle r="4.2"/></g>'
    if key == "active":
        return f'<g {s}><path d="M-10 1H-5.5L-2.8 -6.5L1.8 7.5L4.6 -1H10"/></g>'
    if key == "domains":
        return (f'<g {s}><rect x="-8.5" y="-8.5" width="7.4" height="7.4" rx="2"/><rect x="1.1" y="-8.5" width="7.4" height="7.4" rx="2"/>'
                f'<rect x="-8.5" y="1.1" width="7.4" height="7.4" rx="2"/></g><rect x="1.1" y="1.1" width="7.4" height="7.4" rx="2" fill="{col}"/>')
    if key == "reports":
        return f'<g {s}><path d="M-6.5 -9H3L7.5 -4.5V9H-6.5Z"/><path d="M2.5 -9V-4H7.5M-3 0H4M-3 4H2"/></g>'
    return f'<path d="{D.sparkle_path(0, 0, 9, 0.22)}" fill="{col}"/>'


# ---------------------------------------------------------------------------
# 배경
# ---------------------------------------------------------------------------

def _background(T, theme):
    p = P
    dark = T["dark"]
    blobs = [
        (160, 30, 340, "#00B4D8", 0.75, 0),
        (720, 420, 380, "#14B8A6", 0.55, -6000),
        (1180, 60, 320, "#7C3AED", 0.75 if dark else 0.5, -10000),
    ]
    dfs, out = [], []
    for i, (cx, cy, r, c, k, dl) in enumerate(blobs):
        gid = f"{p}-blob{i}"
        dfs.append(D.radial_gradient(gid, [(0, c, T["blob_opacity"] * k), (0.55, c, T["blob_opacity"] * k * 0.3), (1, c, 0)]))
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})" class="{p}-floats" style="animation-delay:{dl}ms;animation-duration:18s"/>')
    dfs.append(D.dot_grid_pattern(f"{p}-dots", theme, gap=24, r=1.0))
    dfs.append(D.radial_gradient(f"{p}-dotsfade-g", [(0, "#fff", 0.9), (0.7, "#fff", 0.25), (1, "#fff", 0)],
                                 cx=W / 2, cy=H / 2, r=760, units="userSpaceOnUse"))
    dfs.append(f'<mask id="{p}-dotsfade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
               f'<rect width="{W}" height="{H}" fill="url(#{p}-dotsfade-g)"/></mask>')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#{p}-dots)" mask="url(#{p}-dotsfade)"/>')
    out.append(f'<g class="{p}-fi" style="animation-duration:2s">'
               + D.constellation(p, theme, (16, 12, W - 32, H - 24), count=26, seed=23, link_dist=150, dim=0.5,
                                 dim_box=(0, 0, W, H)) + "</g>")
    return "".join(dfs), "".join(out)


# ---------------------------------------------------------------------------
# 머리줄
# ---------------------------------------------------------------------------

def _header(T, data):
    p = P
    dark = T["dark"]
    dfs, out, css = [], [], []
    y = 44
    title = data.get("stats_title") or "BY THE NUMBERS"
    ts = 16
    tw = D.text_width(title, ts, "mono", 600, letter_spacing=3)
    sp = f'<path d="{D.sparkle_path(PAD_X + 9, y - 6, 9, 0.24)}" fill="url(#{p}-ai)" class="{p}-glow"/>'
    dfs.append(D.linear_gradient(f"{p}-ai", T["grad_ai"], 0, 0, 1, 1))
    out.append(f'<g class="{p}-fd" style="{D.delay(40)}">' + sp
               + D.text(PAD_X + 28, y, title, ts, T["accent"], 600, "mono", ls=3) + "</g>")
    left = PAD_X + 28 + tw + 18

    asof = data.get("asof")
    right = W - PAD_X
    if asof:
        lab = f"AS OF {D.fmt_date(asof)}"
        aw = D.text_width(lab, ts, "mono", 500, letter_spacing=2)
        dot_x = right - aw - 16
        out.append(f'<g class="{p}-fd" style="{D.delay(120)}">'
                   f'<circle cx="{D.n(dot_x)}" cy="{y - 5.5}" r="7" fill="{T["accent2"]}" opacity="0.3" class="{p}-pulse"/>'
                   f'<circle cx="{D.n(dot_x)}" cy="{y - 5.5}" r="3.6" fill="{T["accent2"]}"/>'
                   + D.text(right, y, lab, ts, T["text2"], 500, "mono", "end", ls=2) + "</g>")
        right = dot_x - 22

    # 두 라벨 사이를 잇는 흐르는 그라디언트 실선
    if right - left > 60:
        per = 420
        dfs.append(D.flow_gradient(f"{p}-hair", [T["grad"][0], T["grad"][1], T["violet"], T["grad"][2]], per))
        # 실선 구간만 보이도록 양 끝이 사라지는 마스크
        mid = f"{p}-hm"
        dfs.append(D.linear_gradient(f"{mid}-g", [(0, "#fff", 0), (0.15, "#fff", 1), (0.85, "#fff", 1), (1, "#fff", 0)],
                                     left, 0, right, 0, units="userSpaceOnUse"))
        dfs.append(f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
                   f'<rect x="{D.n(left)}" y="{y - 8}" width="{D.n(right - left)}" height="4" fill="url(#{mid}-g)"/></mask>')
        css.append(D.flow_css(p, per))
        out.append(f'<g class="{p}-fi" style="{D.delay(200)}" opacity="{0.9 if dark else 0.8}">'
                   + D.flow_rect(p, left, y - 7, right - left, 1.6, f"{p}-hair", per, dur=7, mask_id=mid) + "</g>")
    return "".join(dfs), "".join(out), "".join(css)


# ---------------------------------------------------------------------------
# 타일
# ---------------------------------------------------------------------------

def _tile_defs(T, theme, g):
    th = g["th"]
    p = P
    dark = T["dark"]
    dfs = [D.glass_defs(theme, p),
           f'<clipPath id="{p}-tclip"><rect x="0" y="0" width="{D.n(g["tw"])}" height="{D.n(th)}" rx="18"/></clipPath>',
           D.glow_filter(f"{p}-gl", 4, 0.95 if dark else 0.45),
           D.glow_filter(f"{p}-gl-s", 2.4, 1.0 if dark else 0.5),
           D.blur_filter(f"{p}-numblur", 12),
           D.linear_gradient(f"{p}-shine", [(0, T["shine"], 0), (0.5, T["shine"], 0.13 if dark else 0.55), (1, T["shine"], 0)], 0, 0, 1, 0)]
    # 색 변주 3종: 링·윗선·숫자 그라디언트
    for v, col in enumerate(_variant_cols(T)):
        hi = "#E6FBFF" if dark else D.mix(col, "#000000", 0.25)
        dfs.append(D.linear_gradient(f"{p}-num{v}", [(0, hi), (0.55, col if not dark else D.mix(col, "#FFFFFF", 0.25)), (1, col)],
                                     IN_X, 0, IN_X + 230, 0, units="userSpaceOnUse"))
        dfs.append(D.linear_gradient(f"{p}-bar{v}", [(0, col, 0), (0.25, col, 1), (0.75, D.mix(col, "#FFFFFF", 0.3) if dark else col, 1), (1, col, 0)], 0, 0, 1, 0))
        dfs.append(D.linear_gradient(f"{p}-ring{v}", [(0, D.mix(col, "#FFFFFF", 0.35)), (1, col)], 0, 0, 1, 1))
        dfs.append(D.radial_gradient(f"{p}-halo{v}", [(0, col, 0.38 if dark else 0.16), (0.6, col, 0.08 if dark else 0.04), (1, col, 0)]))
        dfs.append(D.radial_gradient(f"{p}-corner{v}", [(0, col, 0.22 if dark else 0.10), (1, col, 0)]))
    full = g["tw"] - IN_X * 2
    fx0, fx1 = IN_X + full - 26, IN_X + full + SUB_SPILL
    dfs.append(D.linear_gradient(f"{p}-subfade-g", [(0, "#fff", 1), (1, "#fff", 0)], fx0, 0, fx1, 0, units="userSpaceOnUse"))
    dfs.append(f'<mask id="{p}-subfade" maskUnits="userSpaceOnUse" x="0" y="0" width="{D.n(g["tw"])}" height="{D.n(th)}">'
               f'<rect x="0" y="0" width="{D.n(fx0)}" height="{D.n(th)}" fill="#fff"/>'
               f'<rect x="{D.n(fx0)}" y="0" width="{D.n(fx1 - fx0)}" height="{D.n(th)}" fill="url(#{p}-subfade-g)"/></mask>')
    return "".join(dfs)


def _variant_cols(T):
    # 시안 · 틸 · 바이올렛(AI) 순환
    return [T["accent"], T["accent2"], T["accent3"]]


def _tile(T, i, stat, stats, g):
    th = g["th"]
    p = P
    dark = T["dark"]
    v = i % 3
    col = _variant_cols(T)[v]
    row, c = divmod(i, g["cols"])
    in_row = min(g["cols"], g["count"] - row * g["cols"])
    off = (g["cols"] - in_row) * (g["tw"] + GAP_X) / 2   # 덜 찬 마지막 줄은 가운데로
    tx = PAD_X + off + c * (g["tw"] + GAP_X)
    ty = GRID_TOP + row * (th + GAP_Y)
    t0 = APPEAR0 + i * APPEAR_STEP
    out = []
    css = []

    out.append(f'<g transform="translate({D.n(tx)},{D.n(ty)})"><g class="{p}-fu" style="{D.delay(t0)}">')
    out.append(D.glass(0, 0, g["tw"], th, T["theme"], p, r=18))

    # 장식(타일 모양으로 자름): 모서리 빛 · 빛 스침
    deco = [f'<circle cx="{D.n(g["rcx"])}" cy="{RING_CY}" r="120" fill="url(#{p}-corner{v})" class="{p}-breathe" style="animation-delay:-{i * 900}ms"/>']
    deco.append(D.motion_only(p, f'<g style="{D.anim(p, "k-shine", 9, 1800 + i * 160, D.EASE_IN_OUT)}">'
                              f'<rect x="-150" y="-20" width="110" height="{D.n(th + 40)}" fill="url(#{p}-shine)" transform="skewX(-20)"/></g>'))
    out.append(f'<g clip-path="url(#{p}-tclip)">' + "".join(deco) + "</g>")

    # 윗선 진행 막대(그려지며 켜짐) + 테두리를 한 바퀴 도는 빛줄기
    bar_x, bar_w = 22, g["tw"] - 44
    out.append(f'<g filter="url(#{p}-gl-s)"><rect x="{bar_x}" y="0" width="{D.n(bar_w)}" height="2.2" rx="1.1" fill="url(#{p}-bar{v})" '
               f'class="{p}-bar" style="{D.anim(p, "k-bar", 1.1, t0 + 250, D.EASE_OUT, "1")}"/></g>')
    tr_col = D.mix(col, "#FFFFFF", 0.35) if dark else col
    out.append(D.motion_only(p, f'<g filter="url(#{p}-gl-s)"><rect x="0.75" y="0.75" width="{D.n(g["tw"] - 1.5)}" height="{D.n(th - 1.5)}" rx="18" '
                             f'pathLength="1" stroke="{tr_col}" stroke-width="1.8" stroke-linecap="round" stroke-dasharray="0.05 0.95" '
                             f'style="{D.anim(p, "k-trace", 11, t0 + 2000 + i * 650, "linear")}"/></g>'))

    # 네온 링(진행 호) + 궤도 점 + 아이콘
    frac = _fraction(stat, stats)
    gap = 2 - frac
    ring = [f'<g transform="translate({D.n(g["rcx"])},{RING_CY})">',
            f'<circle r="{RING_R + 20}" fill="url(#{p}-halo{v})" class="{p}-glow" style="animation-delay:-{i * 700}ms"/>',
            f'<g class="{p}-spinr" style="animation-duration:{24 + i * 3}s"><circle r="{RING_R + 7}" stroke="{D.rgba(col, 0.42 if dark else 0.5)}" '
            f'stroke-width="1" stroke-dasharray="1.5 6" stroke-linecap="round"/></g>',
            f'<circle r="{RING_R}" stroke="{D.rgba(col, 0.16 if dark else 0.14)}" stroke-width="3.2"/>',
            f'<g transform="rotate(-90)" filter="url(#{p}-gl)"><circle r="{RING_R}" pathLength="1" stroke="url(#{p}-ring{v})" stroke-width="3.2" '
            f'stroke-linecap="round" stroke-dasharray="{D.n(frac, 4)} {D.n(gap, 4)}" '
            f'style="{D.anim(p, "k-arc" + str(int(round(frac * 1000))), 1.5, t0 + 300, D.EASE_OUT, "1")}"/></g>',
            f'<g class="{p}-spin" style="animation-duration:{7 + i}s;animation-delay:-{i * 1100}ms">'
            f'<circle cx="{RING_R}" cy="0" r="2.6" fill="{D.mix(col, "#FFFFFF", 0.4) if dark else col}" filter="url(#{p}-gl-s)"/></g>']
    css.append(D.keyframes(p, "k-arc" + str(int(round(frac * 1000))), f"from{{stroke-dashoffset:{D.n(frac, 4)}}}"))
    if frac < 0.995:
        pct = f"{int(round(frac * 100))}%"
        ring.append(f'<g class="{p}-pop" style="{D.delay(t0 + 700)}">'
                    + D.text(0, 5.8, pct, 16, col if not dark else D.mix(col, "#FFFFFF", 0.3), 700, "latin", "middle") + "</g>")
    else:
        ring.append(f'<g class="{p}-pop" style="{D.delay(t0 + 600)}">{_icon(stat.get("key"), col if not dark else D.mix(col, "#FFFFFF", 0.25))}</g>')
    ring.append("</g>")
    out.append("".join(ring))

    # 숫자 — 오도미터
    value = str(stat.get("value", ""))
    vmax = g["rcx"] - RING_R - 18 - IN_X
    vs = D.fit_size(value, vmax, 46, 26, "latin", 800)
    base = BASE
    if value:
        if dark:
            out.append(f'<g class="{p}-fi" style="{D.delay(t0 + 1300)};animation-duration:1.4s"><g opacity="0.5"><g class="{p}-glow" style="animation-delay:-{i * 600}ms" filter="url(#{p}-numblur)">'
                       + D.text(IN_X, base, value, vs, col, 800, "latin") + "</g></g></g>")
        odo = D.odometer(p, IN_X, base, value, vs, f"url(#{p}-num{v})", "latin", 800, delay_ms=t0 + 200, step_ms=60,
                         clip_id=f"{p}-odo{i}")
        odo = odo.replace("animation-delay:", f"animation-duration:{ODO_DUR}s;animation-delay:")
        # 굴러가는 창을 숫자 글자 높이에 맞춰 좁힌다. design.odometer 의 clipPath 는 줄 간격보다 넉넉해
        # 지나가는 자릿수 조각이 숫자 위아래에 떠 보이므로, 바깥에서 한 번 더 잘라 창을 숫자 자리로 한정한다.
        # 그라디언트 mask 로 위아래를 흐리는 방식은 Chrome 에서 transform 애니메이션(합성 레이어) 자식과 만나면
        # 흐림 모양이 어긋나(윗변이 칼로 자른 듯 남음) 실측으로 버렸다 — clipPath 는 정확히 먹는다.
        # 숫자 윗선 ≈ 기준선-0.73em(Inter·Arial), 둥근 숫자 아래 넘침 ≈ 0.015em 이라 여유를 조금 둔다.
        top, bot = base - vs * 0.77, base + vs * 0.04
        wid = f"{p}-ow{i}"
        rects = [f'<rect x="0" y="{D.n(top)}" width="{D.n(g["tw"])}" height="{D.n(bot - top)}"/>']
        # 고정 글자(, . + % k)는 굴러가지 않으니 쉼표 꼬리가 잘리지 않게 그 자리만 아래로 더 연다
        cx = IN_X
        for ch in value:
            cw = D.char_em(ch, "latin") * vs * 1.06
            if not ch.isdigit():
                rects.append(f'<rect x="{D.n(cx - 2)}" y="{D.n(top)}" width="{D.n(cw + 4)}" height="{D.n(vs * 1.05)}"/>')
            cx += cw
        win = f'<clipPath id="{wid}">' + "".join(rects) + "</clipPath>"
        out.append(D.defs(win) + f'<g clip-path="url(#{wid})">{odo}</g>')

    # 라벨 · 보조
    full = g["tw"] - IN_X * 2
    label = str(stat.get("label", ""))
    if label:
        fam = D.family_of(label)
        ls_ = D.fit_size(label, full, 21, 18, fam, 700)
        out.append(f'<g class="{p}-fu" style="{D.delay(t0 + 380)}">'
                   + D.text(IN_X, base + 31, D.truncate(label, full, ls_, fam, 700), ls_, T["text"], 700, fam) + "</g>")
    sub = str(stat.get("sub", ""))
    if sub:
        fam = D.family_of(sub)
        ss = D.fit_size(sub, full, 17, 16, fam, 500)
        # 추정(넉넉함)으로는 넘쳐도 실제 글꼴은 대개 들어간다 → 1.25배까지는 그대로 두고 마스크가 끝을 흐린다
        sub_t = D.truncate(sub, full * 1.25, ss, fam, 500)
        out.append(f'<g class="{p}-fu" style="{D.delay(t0 + 480)}"><g mask="url(#{p}-subfade)">'
                   + D.text(IN_X, base + 55, sub_t, ss, T["text2"], 500, fam) + "</g></g>")

    out.append("</g></g>")
    return "".join(out), "".join(css)


def render(theme, data) -> str:
    T = D.tokens(theme)
    p = P
    stats = list(data.get("stats") or [])[:MAX_TILES]
    g = _grid(len(stats))

    bg_defs, bg = _background(T, theme)
    hd_defs, hd, hd_css = _header(T, data)
    tiles, t_css = [], []
    seen = set()
    for i, s in enumerate(stats):
        svg, c = _tile(T, i, s, stats, g)
        tiles.append(svg)
        if c not in seen:
            seen.add(c)
            t_css.append(c)

    css = (hd_css + "".join(t_css)
           + D.keyframes(p, "k-bar", "from{transform:scaleX(0);opacity:0}")
           + D.keyframes(p, "k-trace", "0%{stroke-dashoffset:0;opacity:0}3%{opacity:1}24%{opacity:1}27%{stroke-dashoffset:-1;opacity:0}100%{stroke-dashoffset:-1;opacity:0}")
           + D.shimmer_css(p, "k-shine", 0, g["tw"] + 260, 0.3)
           # 막대는 왼쪽 끝에서 펼쳐진다
           + f".{p}-bar{{transform-box:fill-box;transform-origin:0 50%}}\n")

    body = (D.card(W, H, theme, p)
            + D.defs(D.card_clip(f"{p}-clip", W, H), bg_defs, hd_defs, _tile_defs(T, theme, g))
            + f'<g clip-path="url(#{p}-clip)">' + bg + "</g>"
            + hd
            + "".join(tiles))

    title = " · ".join(f"{s.get('value', '')} {s.get('label', '')}".strip() for s in stats)
    desc = " / ".join(f"{s.get('label', '')}: {s.get('value', '')} ({s.get('sub', '')})" for s in stats)
    return D.svg_root(W, H, theme, "Stats — " + title if title else "Stats", desc, body, css, p)
