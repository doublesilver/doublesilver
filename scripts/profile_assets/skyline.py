"""skyline (1280×560) — 일별 커밋을 '주(열)×요일(행)' 아이소메트릭 3D 막대 도시로 그린다.

막대는 주 단위 물결로 솟아오르고(등장 후 최종 높이로 멈춤), 빛줄기가 도시 실루엣을 훑는다.
사실 값(기간·합계·저장소 수·월별 합계·최고일)은 전부 data["commits"] 에서 읽는다.
"""

from __future__ import annotations

import datetime as _dt
import math

from . import design as D

W, H = 1280, 560
P = "skyline"

# 아이소메트릭 축(SVG 단위) — 주 축 u 는 오른쪽 아래, 요일 축 v 는 왼쪽 아래.
# 진짜 등각(30°)보다 납작하게 잡아 18주 × 7일 도시가 1280×560 안에 들어가게 했다.
UX, UY = 44.0, 10.5
VX, VY = -17.0, 12.5
BAR_FILL = 0.74            # 칸 안에서 막대가 차지하는 비율(나머지는 골목)
H_MAX = 222.0              # 최고일 막대 높이
H_MIN = 5.0                # 커밋이 1건이라도 있으면 최소 높이
MARGIN_X = 64

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

# 강도 색 램프(낮음 → 높음). 다크는 abyss→ocean→cyan→aqua→mint, 라이트는 같은 순서를 밝은 바탕용으로.
RAMP = {
    "dark": [(0.0, "#1A5A86"), (0.22, "#0077B6"), (0.5, "#00B4D8"), (0.76, "#90E0EF"), (1.0, "#2DD4BF")],
    "light": [(0.0, "#BFE4F3"), (0.22, "#48B7DD"), (0.5, "#0096C7"), (0.76, "#0077B6"), (1.0, "#14B8A6")],
}


def _ramp(theme, t):
    stops = RAMP[theme]
    t = D.clamp(t, 0.0, 1.0)
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if t <= b:
            return D.mix(ca, cb, (t - a) / (b - a) if b > a else 0)
    return stops[-1][1]


def _parse(iso):
    try:
        return _dt.date.fromisoformat(str(iso)[:10])
    except ValueError:
        return None


def _poly(pts):
    return "M" + "L".join(f"{D.n(x, 1)} {D.n(y, 1)}" for x, y in pts) + "Z"


class _Grid:
    """주(i)·요일(j) 칸 → 화면 좌표."""

    def __init__(self, ox, oy):
        self.ox, self.oy = ox, oy

    def p(self, i, j, h=0.0):
        return (self.ox + i * UX + j * VX, self.oy + i * UY + j * VY - h)


def _layout(series):
    """series → [(i, j, day)] 와 주 수. 첫 날의 요일을 j 로 맞춰 GitHub 잔디처럼 배치."""
    cells = []
    first = None
    for k, day in enumerate(series):
        d = _parse(day.get("date"))
        if d is None:
            continue
        if first is None:
            first = d - _dt.timedelta(days=d.weekday())  # 첫 주 월요일
        delta = (d - first).days
        cells.append((delta // 7, delta % 7, d, int(day.get("total") or 0)))
    weeks = (max(c[0] for c in cells) + 1) if cells else 1
    return cells, weeks


def _text_block(T, data, cm, company):
    """제목·부제·아이브로우."""
    p = P
    dark = T["dark"]
    out, dfs, css = [], [], []
    x = MARGIN_X
    max_w = 700

    # 아이브로우 — 기간 길이·활동일(data)
    days, active = cm.get("days"), cm.get("active_days")
    eyebrow_bits = []
    if days:
        eyebrow_bits.append(f"{D.fmt_int(days)} DAYS")
    if active:
        eyebrow_bits.append(f"{D.fmt_int(active)} ACTIVE")
    eyebrow = " · ".join(eyebrow_bits)
    if eyebrow:
        out.append(D.eyebrow(p, x, 34, eyebrow, T["theme"], "teal", "dot", max_w=max_w)[0])

    # 제목 — 그라디언트 글자 + 빛 스침
    suffix = "Commit Skyline"
    title = f"{company} {suffix}".strip()
    ts = D.fit_size(title, max_w, 46, 30, "latin", 800, -0.8)
    if D.text_width(title, ts, "latin", 800, -0.8) > max_w and company:
        room = max_w - D.text_width(" " + suffix, ts, "latin", 800, -0.8)
        title = f"{D.truncate(company, room, ts, 'latin', 800)} {suffix}"
    tw = D.text_width(title, ts, "latin", 800, -0.8)
    ty = 112
    dfs.append(D.linear_gradient(f"{p}-title-g", T["grad_text"], 0, 0, 1, 0))
    dfs.append(f'<clipPath id="{p}-title-clip">' + D.text(x, ty, title, ts, None, 800, "latin", ls=-0.8) + "</clipPath>")
    dfs.append(D.linear_gradient(f"{p}-shine", [(0, T["shine"], 0), (0.5, T["shine"], T["shine_opacity"]), (1, T["shine"], 0)], 0, 0, 1, 0))
    css.append(D.shimmer_css(p, "k-shine", x - 200, x + tw + 80, 0.3))
    glow = ""
    if dark:
        dfs.append(D.blur_filter(f"{p}-title-blur", 12))
        glow = (f'<g opacity="0.45" class="{p}-glow" filter="url(#{p}-title-blur)">'
                + D.text(x, ty, title, ts, T["accent"], 800, "latin", ls=-0.8) + "</g>")
    out.append(f'<g class="{p}-fu" style="{D.delay(160)}">{glow}'
               + D.text(x, ty, title, ts, f"url(#{p}-title-g)", 800, "latin", ls=-0.8)
               + f'<g clip-path="url(#{p}-title-clip)"><g style="{D.anim(p, "k-shine", 8, 1900, D.EASE_IN_OUT)}">'
                 f'<rect x="0" y="{D.n(ty - ts)}" width="120" height="{D.n(ts * 1.3)}" fill="url(#{p}-shine)" transform="skewX(-18)"/></g></g>'
               + "</g>")

    # 부제 — 기간 · 합계 · 저장소 수(data 로 조립)
    since, until = cm.get("since"), cm.get("until")
    parts = []
    if since or until:
        parts.append(f"{D.fmt_date(since) if since else ''} → {D.fmt_date(until) if until else ''}".strip())
    if cm.get("total") is not None:
        parts.append(f"{D.fmt_int(cm['total'])} commits")
    if cm.get("repos") is not None:
        parts.append(f"{D.fmt_int(cm['repos'])} repositories")
    sub = "  ·  ".join(parts)
    if sub:
        ss = D.fit_size(sub, max_w, 21, 17, "latin", 500)
        sub = D.truncate(sub, max_w, ss, "latin", 500)
        # 숫자만 밝게: tspan 으로 이어 붙여 실제 글자 폭을 따라간다
        spans = []
        for k, part in enumerate(sub.split("  ·  ")):
            if k:
                spans.append(f'<tspan fill="{T["border_hi"]}">  ·  </tspan>')
            head, _, tail = part.partition(" ")
            if tail and head[:1].isdigit():
                spans.append(f'<tspan fill="{T["text"]}" font-weight="700">{D.esc(head)}</tspan><tspan> {D.esc(tail)}</tspan>')
            else:
                spans.append(f'<tspan>{D.esc(part)}</tspan>')
        out.append(f'<g class="{p}-fu" style="{D.delay(320)}">'
                   f'<text x="{x}" y="{ty + 38}" font-size="{D.n(ss)}" font-weight="500" fill="{T["text2"]}" '
                   f'font-family="{D.esc(D.FONT_LATIN)}">{"".join(spans)}</text></g>')
    return "".join(dfs), "".join(out), "".join(css)


def _background(T, theme, avoid=None):
    p = P
    dark = T["dark"]
    dfs, out = [], []
    blobs = [
        (1060, 120, 380, "#7C3AED", 0.7 if dark else 0.45, 0),
        (220, 520, 420, "#00B4D8", 0.7, -6000),
        (760, 560, 420, "#14B8A6", 0.65, -10000),
        (520, 40, 300, "#0077B6", 0.6, -3000),
    ]
    for i, (cx, cy, r, c, k, dl) in enumerate(blobs):
        gid = f"{p}-blob{i}"
        dfs.append(D.radial_gradient(gid, [(0, c, T["blob_opacity"] * k), (0.55, c, T["blob_opacity"] * k * 0.3), (1, c, 0)]))
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})" class="{p}-floats" style="animation-delay:{dl}ms;animation-duration:18s"/>')
    dfs.append(D.dot_grid_pattern(f"{p}-dots", theme, gap=24, r=1.0))
    dfs.append(D.radial_gradient(f"{p}-dotsfade-g", [(0, "#fff", 0.9), (0.55, "#fff", 0.3), (1, "#fff", 0)],
                                 cx=900, cy=160, r=620, units="userSpaceOnUse"))
    dfs.append(f'<mask id="{p}-dotsfade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
               f'<rect width="{W}" height="{H}" fill="url(#{p}-dotsfade-g)"/></mask>')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#{p}-dots)" mask="url(#{p}-dotsfade)"/>')
    stars = D.constellation(p, theme, (780, 30, 470, 150), count=12, seed=11, link_dist=140, r_range=(0.9, 2.0))
    if avoid:
        # 반투명 카드 뒤로 별자리 선이 비치지 않게 카드 자리(+여백)를 마스크로 도려낸다
        ax, ay, aw, ah = avoid
        m = 14
        dfs.append(f'<mask id="{p}-starmask" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
                   f'<rect width="{W}" height="{H}" fill="#fff"/>'
                   f'<rect x="{D.n(ax - m, 1)}" y="{D.n(ay - m, 1)}" width="{D.n(aw + 2 * m, 1)}" height="{D.n(ah + 2 * m, 1)}" rx="{18 + m}" fill="#000"/></mask>')
        stars = f'<g mask="url(#{p}-starmask)">{stars}</g>'
    out.append(stars)
    return "".join(dfs), "".join(out)


def _floor(T, G, weeks):
    """도시 바닥판 — 글래스 평면 + 칸 격자 + 테두리를 따라 흐르는 빛."""
    p = P
    dark = T["dark"]
    pad = 0.55
    a, b = G.p(-pad, -pad), G.p(weeks + pad, -pad)
    c, d = G.p(weeks + pad, 7 + pad), G.p(-pad, 7 + pad)
    dfs = [
        D.linear_gradient(f"{p}-floor-g", [(0, "#90E0EF" if dark else "#FFFFFF", 0.07 if dark else 0.9),
                                            (1, "#00B4D8" if dark else "#E3F1FA", 0.02 if dark else 0.9)], 0, 0, 1, 1),
        D.linear_gradient(f"{p}-floor-edge", [(0, T["grad"][0], 0.9), (0.5, T["grad"][1], 0.9), (1, T["grad"][2], 0.9)], 0, 0, 1, 0),
        D.radial_gradient(f"{p}-floor-glow", [(0, "#00B4D8", 0.30 if dark else 0.14), (0.6, "#0077B6", 0.08 if dark else 0.04), (1, "#0077B6", 0)]),
    ]
    out = []
    # 바닥 아래 은은한 빛 웅덩이
    cx, cy = G.p(weeks * 0.62, 3.5)
    out.append(f'<ellipse cx="{D.n(cx)}" cy="{D.n(cy + 30)}" rx="520" ry="150" fill="url(#{p}-floor-glow)" class="{p}-breathe" style="animation-duration:8s"/>')
    # 바닥판 측면 두께(앞 두 변)
    th = 10
    side_l = _poly([d, c, (c[0], c[1] + th), (d[0], d[1] + th)])
    side_r = _poly([b, c, (c[0], c[1] + th), (b[0], b[1] + th)])
    out.append(f'<path d="{side_l}" fill="{D.rgba("#0077B6", 0.22) if dark else "#D6EAF6"}"/>'
               f'<path d="{side_r}" fill="{D.rgba("#0077B6", 0.32) if dark else "#C4E0F1"}"/>')
    out.append(f'<path d="{_poly([a, b, c, d])}" fill="url(#{p}-floor-g)" stroke="{T["border_hi"]}" stroke-width="1"/>')
    # 칸 격자(주·요일 경계)
    lines = []
    for i in range(weeks + 1):
        (x1, y1), (x2, y2) = G.p(i, 0), G.p(i, 7)
        lines.append(f"M{D.n(x1, 1)} {D.n(y1, 1)}L{D.n(x2, 1)} {D.n(y2, 1)}")
    for j in range(8):
        (x1, y1), (x2, y2) = G.p(0, j), G.p(weeks, j)
        lines.append(f"M{D.n(x1, 1)} {D.n(y1, 1)}L{D.n(x2, 1)} {D.n(y2, 1)}")
    out.append(f'<path d="{"".join(lines)}" stroke="{T["line"]}" stroke-width="0.8" opacity="{0.16 if dark else 0.22}"/>')
    # 테두리를 도는 빛(대시 오프셋 루프) — 축소 모드에선 멈춘 짧은 선으로 남는다
    out.append(f'<path d="{_poly([a, b, c, d])}" pathLength="1000" stroke="url(#{p}-floor-edge)" stroke-width="2" '
               f'stroke-linecap="round" stroke-dasharray="140 860" filter="url(#{p}-glow-s)" '
               f'style="{D.anim(p, "k-edge", 10, 0, "linear")}"/>')
    css = D.keyframes(p, "k-edge", "from{stroke-dashoffset:0}to{stroke-dashoffset:-1000}")
    return "".join(dfs), "".join(out), css


def _bar_faces(G, i, j, h):
    g = (1 - BAR_FILL) / 2
    i0, i1, j0, j1 = i + g, i + 1 - g, j + g, j + 1 - g
    t00, t10, t11, t01 = G.p(i0, j0, h), G.p(i1, j0, h), G.p(i1, j1, h), G.p(i0, j1, h)
    b10, b11, b01 = G.p(i1, j0), G.p(i1, j1), G.p(i0, j1)
    top = [t00, t10, t11, t01]
    left = [t01, t11, b11, b01]     # j+1 쪽 면(왼쪽 아래를 향함)
    right = [t10, t11, b11, b10]    # i+1 쪽 면(오른쪽 아래를 향함)
    return top, left, right, b11


def _city(T, theme, G, cells, weeks, max_total):
    p = P
    dark = T["dark"]
    dfs = [
        # 옆면 위→아래 어두워지는 공용 음영
        D.linear_gradient(f"{p}-shade", [(0, "#000", 0), (1, "#000", 0.38 if dark else 0.16)], 0, 0, 0, 1),
        D.linear_gradient(f"{p}-sheen", [(0, "#FFFFFF", 0.35 if dark else 0.55), (1, "#FFFFFF", 0)], 0, 0, 0, 1),
    ]
    tiles, bars, sil = [], [], []
    win_col = "#E8FBFF" if dark else "#FFFFFF"
    order = sorted(cells, key=lambda c: (c[0] + c[1], c[0]))
    tall = []
    for (i, j, d, total) in order:
        if total <= 0:
            g = 0.1
            pts = [G.p(i + g, j + g), G.p(i + 1 - g, j + g), G.p(i + 1 - g, j + 1 - g), G.p(i + g, j + 1 - g)]
            tiles.append(_poly(pts))
            continue
        t = math.sqrt(total / max_total) if max_total else 0
        h = max(H_MIN, H_MAX * t)
        col = _ramp(theme, t)
        top, left, right, base = _bar_faces(G, i, j, h)
        sil.append(_poly([top[0], top[1], right[3], right[2], left[3], top[3]]))
        top_c = D.mix(col, "#FFFFFF", 0.10 if dark else 0.06)
        left_c = D.mix(col, "#000000", 0.30 if dark else 0.14)
        right_c = D.mix(col, "#000000", 0.50 if dark else 0.28)
        edge = D.mix(col, "#FFFFFF", 0.55 if dark else 0.45)
        delay = 240 + i * 54 + j * 20
        parts = [
            f'<path d="{_poly(left)}" fill="{left_c}"/>',
            f'<path d="{_poly(right)}" fill="{right_c}"/>',
        ]
        if h > 18:
            parts.append(f'<path d="{_poly(left)}" fill="url(#{p}-shade)"/><path d="{_poly(right)}" fill="url(#{p}-shade)"/>')
        # 높은 막대의 오른쪽 면에 창문 불빛(대시 선 한 줄 = 창문 한 층)
        if h > 64:
            rows = []
            g = (1 - BAR_FILL) / 2
            for k in range(int((h - 22) // 15)):
                yy = h - 16 - k * 15
                for frac in (0.22, 0.58):
                    x1, y1 = G.p(i + g + BAR_FILL * frac, j + 1 - g, yy)
                    x2, y2 = G.p(i + g + BAR_FILL * (frac + 0.22), j + 1 - g, yy)
                    # 오른쪽 면이 아니라 앞-왼쪽 면(j+1)에 깐다 — 더 넓게 보이는 면
                    rows.append(f"M{D.n(x1, 1)} {D.n(y1, 1)}L{D.n(x2, 1)} {D.n(y2, 1)}")
            if rows:
                parts.append(f'<g opacity="{0.55 if dark else 0.7}"><path d="{"".join(rows)}" stroke="{win_col}" stroke-width="2.2" '
                             f'stroke-linecap="round" class="{p}-tw" style="animation-delay:-{(i * 937 + j * 389) % 3600}ms;animation-duration:{5 + (i + j) % 4}s"/></g>')
        stroke = f' stroke="{edge}" stroke-width="0.9" stroke-linejoin="round"' if dark or t > 0.3 else ""
        parts.append(f'<path d="{_poly(top)}" fill="{top_c}"{stroke}/>')
        if h > 18:
            parts.append(f'<path d="{_poly(top)}" fill="url(#{p}-sheen)"/>')
        if t > 0.8:
            tall.append((i, j, h, col))
        bx, by = base
        bars.append(f'<g style="transform-origin:{D.n(bx, 1)}px {D.n(by, 1)}px;'
                    f'animation:{p}-k-rise 1.1s {D.EASE_OUT} {delay}ms both">' + "".join(parts) + "</g>")
    tile_fill = D.rgba("#90E0EF", 0.10) if dark else "#DCEBF5"
    tile_stroke = D.rgba("#90E0EF", 0.16) if dark else "#C9E0EE"
    city = (f'<g><path d="{"".join(tiles)}" fill="{tile_fill}" stroke="{tile_stroke}" stroke-width="0.8"/>'
            + "".join(bars) + "</g>")
    css = D.keyframes(p, "k-rise", "from{transform:scaleY(0.02);opacity:0}30%{opacity:1}")
    return "".join(dfs), city, css, tall, "".join(sil)


def _beam(T, silhouette):
    """도시 실루엣을 훑는 빛줄기 — 바닥·배경엔 아주 옅게, 막대 위에선 밝게."""
    p = P
    dark = T["dark"]
    dfs = [
        # 막대 실루엣(최종 높이) — <use>+필터 마스크는 Chrome 에서 비어 버려 도형을 직접 넣는다
        f'<mask id="{p}-citymask" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
        f'<path d="{silhouette}" fill="#fff"/></mask>',
        D.linear_gradient(f"{p}-beam-g", [(0, "#FFFFFF", 0), (0.5, "#FFFFFF", 1), (1, "#FFFFFF", 0)], 0, 0, 1, 0),
        D.linear_gradient(f"{p}-ray-g", [(0, "#90E0EF" if dark else "#00B4D8", 0), (0.5, "#90E0EF" if dark else "#00B4D8", 1),
                                          (1, "#90E0EF" if dark else "#00B4D8", 0)], 0, 0, 1, 0),
    ]
    css = D.shimmer_css(p, "k-beam", -360, W + 260, 0.42)
    style = D.anim(p, "k-beam", 9, 2600, D.EASE_IN_OUT)
    out = (
        # 배경을 지나는 옅은 광선
        f'<g opacity="{0.13 if dark else 0.12}"><g transform="skewX(-24)"><rect x="0" y="0" width="220" height="{H}" fill="url(#{p}-ray-g)" style="{style}"/></g></g>'
        # 막대 위의 밝은 빛
        f'<g mask="url(#{p}-citymask)" opacity="{0.5 if dark else 0.6}"><g transform="skewX(-24)">'
        f'<rect x="0" y="0" width="150" height="{H}" fill="url(#{p}-beam-g)" style="{style}"/></g></g>'
    )
    return "".join(dfs), out, css


def _labels(T, G, cells, weeks, cm):
    """월 라벨(앞 모서리를 따라) · 요일 라벨(왼쪽 모서리)."""
    p = P
    dark = T["dark"]
    out = []
    ang = math.degrees(math.atan2(UY, UX))
    monthly = cm.get("monthly") or {}
    by_month = {}
    for (i, j, d, total) in cells:
        key = f"{d.year:04d}-{d.month:02d}"
        by_month.setdefault(key, []).append(i)
    step = math.hypot(UX, UY)          # 주 1칸이 앞 모서리를 따라 차지하는 길이
    prev_end = -1e9
    for k, (key, cols) in enumerate(sorted(by_month.items())):
        mid = (min(cols) + max(cols) + 1) / 2
        try:
            mname = MONTHS[int(key[5:7]) - 1]
        except (ValueError, IndexError):
            mname = key
        val = monthly.get(key)
        val_txt = D.fmt_int(val) if val is not None else ""
        lw_full = D.text_width(mname, 17, "mono", 700, 1) + (8 + D.text_width(val_txt, 17, "mono", 500) if val_txt else 0)
        lw_name = D.text_width(mname, 17, "mono", 700, 1)
        gap = 14
        if val_txt and mid * step - lw_full / 2 < prev_end + gap:
            val_txt = ""              # 자리가 없으면 월 합계는 생략하고 월 이름만
        lw = lw_full if val_txt else lw_name
        c_px = max(mid * step, prev_end + gap + lw / 2)
        prev_end = c_px + lw / 2
        mid = c_px / step
        x, y = G.p(mid, 7.55)
        tick_a, tick_b = G.p(min(cols), 7.0), G.p(min(cols), 7.35)
        if k:
            out.append(f'<path d="M{D.n(tick_a[0], 1)} {D.n(tick_a[1], 1)}L{D.n(tick_b[0], 1)} {D.n(tick_b[1], 1)}" '
                       f'stroke="{T["border_hi"]}" stroke-width="1.2"/>')
        val_s = f'<tspan dx="8" fill="{T["text2"]}" font-weight="500">{D.esc(val_txt)}</tspan>' if val_txt else ""
        out.append(f'<g transform="translate({D.n(x, 1)},{D.n(y + 14, 1)}) rotate({D.n(ang, 2)})">'
                   f'<g class="{p}-fi" style="{D.delay(900 + k * 120)}">'
                   f'<text x="0" y="0" text-anchor="middle" font-family="{D.esc(D.FONT_MONO)}" font-size="17" font-weight="700" '
                   f'fill="{T["accent"]}" letter-spacing="1">{D.esc(mname)}{val_s}</text></g></g>')
    for j in (0, 2, 4, 6):
        x, y = G.p(-0.35, j + 0.5)
        out.append(f'<g class="{p}-fi" style="{D.delay(700 + j * 60)}">'
                   + D.text(x - 4, y + 5, WEEKDAYS[j], 16, T["muted"], 600, "mono", "end", ls=1) + "</g>")
    return "".join(out)


def _peak(T, G, cells, cm, max_total, labels=None):
    """최고일 콜아웃 — 막대 꼭대기 비컨 + 연결선 + 글래스 카드(롤링 숫자)."""
    labels = labels or {}
    p = P
    dark = T["dark"]
    md = cm.get("max_day") or {}
    pd = _parse(md.get("date"))
    hit = next(((i, j, d, t) for (i, j, d, t) in cells if d == pd), None)
    if not hit:
        return "", "", "", None
    i, j, d, total = hit
    value = md.get("total", total)
    t = math.sqrt(total / max_total) if max_total else 1
    h = max(H_MIN, H_MAX * t)
    bx, by = G.p(i + 0.5, j + 0.5, h)
    out, dfs = [], []
    # 카드 — 오른쪽 위 빈 하늘
    label = "PEAK DAY"
    date_s = D.fmt_date(md.get("date", ""))
    val_s = D.fmt_int(value)
    unit = "commits"
    unit_w = D.text_width(unit, 19, "latin", 500)
    date_w = D.text_width(date_s, 18, "mono", 600)
    label_w = 42 + D.text_width(label, 16, "mono", 700, 2) + 22
    nat_w = D.text_width(val_s, 46, "latin", 800)
    # 도메인 캡션(상위 2개)이 들어갈 폭도 카드 폭 후보에 넣는다 — 상한 360 을 넘으면 캡션이 1개로 줄어든다
    mix_by = md.get("by") or {}
    top2 = sorted(mix_by.items(), key=lambda kv: -kv[1])[:2]
    mix_tot = sum(mix_by.values()) or 1
    cap_need = sum(14 + D.text_width(f"{labels.get(k, k)} {round(100 * v / mix_tot)}%", 16, "mono", 500) for k, v in top2) + 18 * max(len(top2) - 1, 0)
    cw = min(360, max(240, label_w, 48 + date_w, 48 + nat_w + 12 + unit_w, 48 + cap_need))
    ch = 180
    cy = 30
    CW_MIN, LEFT_LIMIT, RIGHT_LIMIT = 200, 780, W - MARGIN_X

    def clear(x0, w0):
        return not (x0 - 10 <= bx <= x0 + w0 + 10)

    # 최고일 막대(빛기둥)를 가리지 않는 자리: 오른쪽 끝 → 기둥 오른쪽 → 기둥 왼쪽 순으로 찾는다
    cands = [(RIGHT_LIMIT - cw, cw)]
    w_r = min(cw, RIGHT_LIMIT - (bx + 36))
    if w_r >= CW_MIN:
        cands.append((bx + 36, w_r))
    w_l = min(cw, bx - 44 - LEFT_LIMIT)
    if w_l >= CW_MIN:
        cands.append((bx - 44 - w_l, w_l))
    cx, cw = next(((x0, w0) for x0, w0 in cands if clear(x0, w0)), cands[0])
    under = not clear(cx, cw)          # 자리가 없으면 빛기둥이 카드 밑변에 닿게
    num_size = D.fit_size(val_s, cw - 48 - 12 - unit_w, 46, 28, "latin", 800)
    num_w = D.text_width(val_s, num_size, "latin", 800)
    top_y = (cy + ch + 4) if under else by - 70
    pil_h = max(by - top_y, 0)

    # 비컨: 꼭대기에서 퍼지는 고리 + 위로 솟는 빛기둥
    dfs.append(D.linear_gradient(f"{p}-pillar", [(0, T["accent2"], 0.15 if under else 0), (1, T["accent2"], 0.8 if dark else 0.6)], 0, 0, 0, 1))
    out.append(f'<g class="{p}-fi" style="{D.delay(1500)}">'
               + (f'<rect x="{D.n(bx - 1.5, 1)}" y="{D.n(top_y, 1)}" width="3" height="{D.n(pil_h, 1)}" fill="url(#{p}-pillar)"/>' if pil_h > 4 else "")
               + f'<g transform="translate({D.n(bx, 1)},{D.n(by, 1)}) scale(1,0.42)">'
               f'<circle r="18" fill="none" stroke="{T["accent2"]}" stroke-width="2.4" style="{D.anim(p, "k-ring", 2.8, 0, "ease-out")}"/>'
               f'<circle r="18" fill="none" stroke="{T["accent2"]}" stroke-width="2.4" style="{D.anim(p, "k-ring", 2.8, 1400, "ease-out")}"/>'
               f'</g><circle cx="{D.n(bx, 1)}" cy="{D.n(by, 1)}" r="4.5" fill="{T["accent2"]}" filter="url(#{p}-glow-s)" class="{p}-glow"/></g>')
    css = D.keyframes(p, "k-ring", "0%{transform:scale(.3);opacity:.95}100%{transform:scale(2.4);opacity:0}")

    # 연결선: 빛기둥 꼭대기 → (수직) → 카드 옆구리
    if under:
        out.append(f'<circle cx="{D.n(bx, 1)}" cy="{D.n(top_y - 4, 1)}" r="3" fill="{T["accent2"]}" class="{p}-fi" style="{D.delay(1900)}"/>')
    else:
        ly = D.clamp(top_y, cy + 30, cy + ch - 30)
        edge_x = cx if bx < cx else cx + cw
        out.append(f'<path d="M{D.n(bx, 1)} {D.n(top_y, 1)}L{D.n(bx, 1)} {D.n(ly, 1)}L{D.n(edge_x, 1)} {D.n(ly, 1)}" pathLength="1" '
                   f'stroke="{T["accent2"]}" stroke-width="1.4" stroke-dasharray="1" opacity="0.85" class="{p}-draw" style="{D.delay(1250)};animation-duration:.9s"/>'
                   f'<circle cx="{D.n(edge_x, 1)}" cy="{D.n(ly, 1)}" r="3" fill="{T["accent2"]}" class="{p}-fi" style="{D.delay(1900)}"/>')
    out.append(f'<g class="{p}-fu" style="{D.delay(700)}">'
               # 카드 밑으로 솟은 막대가 비쳐 캡션을 가리지 않게 유리 아래에 짙은 바탕을 한 겹 깐다
               + f'<rect x="{D.n(cx, 1)}" y="{cy}" width="{D.n(cw, 1)}" height="{ch}" rx="18" '
               f'fill="{"#0B1220" if dark else "#FFFFFF"}" opacity="{0.62 if dark else 0.55}"/>'
               + D.glass(cx, cy, cw, ch, T["theme"], p, r=18))
    out.append(f'<circle cx="{D.n(cx + 28)}" cy="{cy + 30}" r="4" fill="{T["accent2"]}" class="{p}-glow"/>'
               + D.text(cx + 42, cy + 36, label, 16, T["accent2"], 700, "mono", ls=2))
    # 숫자 기준선을 조금 올려, 굴러가는 중 아랫줄 숫자 조각이 날짜 줄에 붙지 않게 한다
    num_y = cy + 88
    out.append(D.odometer(p, cx + 24, num_y, val_s, num_size, T["text"], "latin", 800, delay_ms=650, clip_id=f"{p}-odo-peak"))
    out.append(D.text(cx + 24 + num_w + 12, num_y, unit, 19, T["text2"], 500, "latin"))
    out.append(D.text(cx + 24, cy + 124, date_s, 18, T["text2"], 600, "mono"))
    # 그날 도메인 구성 비율 막대(가장 큰 순)
    mix_by = md.get("by") or {}
    if mix_by and value:
        segs = sorted(mix_by.items(), key=lambda kv: -kv[1])
        sx, sw = cx + 24, cw - 48
        yb = cy + 138
        cols = [T["accent"], T["accent2"], T["accent3"], D.PALETTE["aqua"] if dark else "#48B7DD", T["muted"]]
        acc = 0.0
        tot = sum(v for _, v in segs) or 1
        segs_svg = []
        for k, (name, v) in enumerate(segs):
            wseg = sw * v / tot
            segs_svg.append(f'<rect x="{D.n(sx + acc, 1)}" y="{yb}" width="{D.n(max(wseg - 2, 1), 1)}" height="6" rx="3" fill="{cols[min(k, len(cols) - 1)]}"/>')
            acc += wseg
        # 띠의 뜻을 읽을 수 있게 상위 항목 이름·비율 캡션(들어가는 만큼만, 최대 2개)
        items = []
        for k, (name, v) in enumerate(segs[:2]):
            items.append((cols[min(k, len(cols) - 1)], f"{labels.get(name, name)} {round(100 * v / tot)}%"))
        dot_w, gap = 14, 18
        def cap_w(its):
            return sum(dot_w + D.text_width(s, 16, "mono", 500) for _, s in its) + gap * (len(its) - 1)
        while len(items) > 1 and cap_w(items) > sw:
            items.pop()
        if len(items) == 1:
            # 한 항목도 안 들어가면 이름을 줄임표로 자른다(캡션 글자는 16 미만으로 줄이지 않는다)
            col, s1 = items[0]
            name, pct = s1.rsplit(" ", 1)
            while len(name) > 3 and dot_w + D.text_width(f"{name}… {pct}", 16, "mono", 500) > sw:
                name = name[:-1]
            items = [(col, s1 if name == s1.rsplit(" ", 1)[0] else f"{name}… {pct}")]
        size = 16
        xx, yc = sx, cy + 164
        for col, s in items:
            segs_svg.append(f'<circle cx="{D.n(xx + 4, 1)}" cy="{D.n(yc - size * 0.34, 1)}" r="4" fill="{col}"/>')
            segs_svg.append(D.text(xx + dot_w, yc, s, size, T["text2"], 500, "mono"))
            xx += dot_w + D.text_width(s, size, "mono", 500) + gap
        out.append(f'<g class="{p}-fi" style="{D.delay(1400)}">' + "".join(segs_svg) + "</g>")
    out.append("</g>")
    return "".join(dfs), "".join(out), css, (cx, cy, cw, ch)


def _legend(T, theme, x, y):
    """범례: 적음 → 많음 — 키가 커지는 작은 아이소 큐브 5개."""
    p = P
    dark = T["dark"]
    out = [f'<g class="{p}-fu" style="{D.delay(1100)}">']
    out.append(D.text(x, y, "적음", 17, T["text2"], 600, "ko"))
    cx = x + 52
    s = 0.48
    for k, t in enumerate([0.08, 0.3, 0.52, 0.76, 1.0]):
        col = _ramp(theme, t)
        h = 6 + 30 * t
        ox, oy = cx + k * 34, y + 4
        top = [(ox, oy - h), (ox + UX * s * 0.6, oy - h + UY * s * 0.6), (ox + UX * s * 0.6 + VX * s * 0.9, oy - h + UY * s * 0.6 + VY * s * 0.9),
               (ox + VX * s * 0.9, oy - h + VY * s * 0.9)]
        t01, t11 = top[3], top[2]
        t10 = top[1]
        left = [t01, t11, (t11[0], t11[1] + h), (t01[0], t01[1] + h)]
        right = [t10, t11, (t11[0], t11[1] + h), (t10[0], t10[1] + h)]
        out.append(f'<g class="{p}-pop" style="{D.delay(1200 + k * 90)}">'
                   f'<path d="{_poly(left)}" fill="{D.mix(col, "#000000", 0.30 if dark else 0.14)}"/>'
                   f'<path d="{_poly(right)}" fill="{D.mix(col, "#000000", 0.50 if dark else 0.28)}"/>'
                   f'<path d="{_poly(top)}" fill="{D.mix(col, "#FFFFFF", 0.1)}"/></g>')
    out.append(D.text(cx + 5 * 34 + 6, y, "많음", 17, T["text2"], 600, "ko"))
    out.append(D.text(x, y + 30, "높이 = √ 일별 커밋", 16, T["muted"], 500, "ko"))
    out.append("</g>")
    return "".join(out)


def _sparks(T, G, tall):
    """높은 막대 꼭대기에서 피어오르는 빛 입자(축소 모드에선 숨김)."""
    p = P
    R = D.rng(23)
    out = []
    picks = sorted(tall, key=lambda c: -c[2])[:14]
    for k, (i, j, h, col) in enumerate(picks):
        x, y = G.p(i + 0.5, j + 0.5, h)
        x += R.uniform(-6, 6)
        dur = R.uniform(5.5, 9.0)
        out.append(f'<circle cx="{D.n(x, 1)}" cy="{D.n(y - 6, 1)}" r="{D.n(R.uniform(1.4, 2.4), 1)}" fill="{D.mix(col, "#FFFFFF", 0.4)}" '
                   f'filter="url(#{p}-glow-s)" style="{D.anim(p, "k-spark", round(dur, 1), -int(R.uniform(0, dur) * 1000), "ease-out")}"/>')
    css = D.keyframes(p, "k-spark", "0%{transform:translateY(0);opacity:0}15%{opacity:1}100%{transform:translateY(-90px);opacity:0}")
    return D.motion_only(p, "".join(out)), css


def render(theme, data) -> str:
    T = D.tokens(theme)
    p = P
    cm = data.get("commits") or {}
    series = cm.get("series") or []
    cells, weeks = _layout(series)
    max_total = (cm.get("max_day") or {}).get("total") or max((c[3] for c in cells), default=1) or 1

    company = data.get("company")
    if not company:
        role = str(data.get("role_en", ""))
        company = role.split("@", 1)[1].strip() if "@" in role else ""

    # 도시 원점: 주 수가 바뀌어도 가로 중앙 근처에 오도록
    span_x = weeks * UX + 7 * abs(VX)
    ox = max(180.0, min(300.0, (W - span_x) / 2 + 7 * abs(VX) - 12))
    G = _Grid(ox, 214.0)

    pk_defs, peak, pk_css, pk_rect = _peak(T, G, cells, cm, max_total, data.get("domain_short"))
    bg_defs, bg = _background(T, theme, pk_rect)
    fl_defs, floor, fl_css = _floor(T, G, weeks)
    city_defs, city, city_css, tall, sil = _city(T, theme, G, cells, weeks, max_total)
    beam_defs, beam, beam_css = _beam(T, sil)
    tx_defs, text_svg, tx_css = _text_block(T, data, cm, company)
    sparks, sp_css = _sparks(T, G, tall)
    labels = _labels(T, G, cells, weeks, cm)
    legend = _legend(T, theme, MARGIN_X, 482)

    defs = D.defs(
        D.card_clip(f"{p}-clip", W, H),
        D.glass_defs(theme, p),
        D.glow_filter(f"{p}-glow-s", 3, 1.0 if T["dark"] else 0.5),
        bg_defs, fl_defs, city_defs, beam_defs, tx_defs, pk_defs,
    )
    body = (D.card(W, H, theme, p) + defs
            + f'<g clip-path="url(#{p}-clip)">' + bg + floor + city + beam + sparks + "</g>"
            + labels + legend + peak + text_svg)
    total = cm.get("total")
    title = f"{company} Commit Skyline".strip()
    desc = (f"{cm.get('since', '')}부터 {cm.get('until', '')}까지 일별 커밋을 주×요일 3D 막대 도시로 표현. "
            f"총 {D.fmt_int(total) if total is not None else '-'}건, 저장소 {cm.get('repos', '-')}개, "
            f"최고일 {(cm.get('max_day') or {}).get('date', '-')} {(cm.get('max_day') or {}).get('total', '-')}건.")
    return D.svg_root(W, H, theme, title, desc, body, fl_css + city_css + beam_css + tx_css + pk_css + sp_css, p)
