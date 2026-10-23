"""domains (1280×768) — 담당 도메인 벤토 그리드.

첫 타일은 2칸(누적 커밋 곡선 + 롤링 숫자), 나머지 7개는 1칸.
타일마다 직접 그린 라인 아이콘(글로우 맥동), 테두리를 도는 그라디언트 빛,
대표 성과(metric) 글래스 필, 전체 대비 커밋 비율 막대.
헤더에는 총 커밋과 도메인별 비율 띠(타일 색과 같은 색)를 둔다.
"""

from __future__ import annotations

import math

from . import design as D

W, H = 1280, 768  # 높이: metric 필 줄(676→752), 머리 칩·44 제목(752→768)
P = "domains"

M = 56            # 바깥 여백
GAP = 18          # 타일 간격
COLS, ROWS = 3, 3
TITLE_Y = 108     # 제목 기준선(위 32 칩 아래)
GRID_TOP = 144
TILE_H = (H - GRID_TOP - 30 - GAP * (ROWS - 1)) / ROWS
TILE_W = (W - 2 * M - GAP * (COLS - 1)) / COLS
TR = 18           # 타일 모서리 반경
PILL_H = 30       # metric 필 높이
PILL_BOTTOM = 16  # 타일 아래 테두리에서 필까지

# 아이콘 키 → 색(개념 매핑, 사실 아님). (dark, light)
ICON_COLORS = {
    "store": ("#00B4D8", "#0077B6"),
    "devices": ("#2DD4BF", "#0D9488"),
    "chat": ("#48CAE4", "#0284C7"),
    "dumbbell": ("#14B8A6", "#0F766E"),
    "scissors": ("#90E0EF", "#0891B2"),
    "network": ("#38BDF8", "#005F92"),
    "shield": ("#5EEAD4", "#0E7490"),
    "brain": ("#A78BFA", "#7C3AED"),
}
FALLBACK_COLORS = [("#00B4D8", "#0077B6"), ("#2DD4BF", "#0D9488"), ("#48CAE4", "#0284C7"), ("#A78BFA", "#7C3AED")]


# ---------------------------------------------------------------------------
# 아이콘(24×24 격자, 전부 path — draw 애니메이션에 pathLength 를 쓰려고)
# ---------------------------------------------------------------------------


def _circ(cx, cy, r):
    return f"M{D.n(cx - r)} {D.n(cy)}a{D.n(r)} {D.n(r)} 0 1 0 {D.n(2 * r)} 0a{D.n(r)} {D.n(r)} 0 1 0 {D.n(-2 * r)} 0"


def _rrect(x, y, w, h, r):
    return (f"M{D.n(x + r)} {D.n(y)}H{D.n(x + w - r)}a{D.n(r)} {D.n(r)} 0 0 1 {D.n(r)} {D.n(r)}"
            f"V{D.n(y + h - r)}a{D.n(r)} {D.n(r)} 0 0 1 {D.n(-r)} {D.n(r)}H{D.n(x + r)}"
            f"a{D.n(r)} {D.n(r)} 0 0 1 {D.n(-r)} {D.n(-r)}V{D.n(y + r)}a{D.n(r)} {D.n(r)} 0 0 1 {D.n(r)} {D.n(-r)}Z")


ICONS = {
    "store": [
        "M3.2 9.2 4.8 4h14.4l1.6 5.2",
        "M3.2 9.2a2.95 2.95 0 0 0 5.9 0a2.95 2.95 0 0 0 5.8 0a2.95 2.95 0 0 0 5.9 0",
        "M4.8 12.2V20h14.4v-7.8",
        "M10 20v-4.6h4V20",
    ],
    "devices": [
        _rrect(2, 4, 14, 10, 1.6),
        "M5.5 18h7M9 14v4",
        _rrect(17, 8.5, 5, 11.5, 1.2),
        "M19.5 17.2h.01",
    ],
    "chat": [
        "M4 4.5h10a2 2 0 0 1 2 2V12a2 2 0 0 1-2 2H8.5L5 17v-3H4a2 2 0 0 1-2-2V6.5a2 2 0 0 1 2-2z",
        "M6 9.25h.01M9 9.25h.01M12 9.25h.01",
        "M18.5 8.5H20a2 2 0 0 1 2 2V16a2 2 0 0 1-2 2h-1v2.6L15.8 18H12",
    ],
    "dumbbell": [
        _rrect(2.6, 8.2, 2.6, 7.6, 1),
        _rrect(5.2, 6, 3, 12, 1.1),
        _rrect(15.8, 6, 3, 12, 1.1),
        _rrect(18.8, 8.2, 2.6, 7.6, 1),
        "M8.2 12h7.6",
    ],
    "scissors": [
        _circ(6, 6, 2.8),
        _circ(6, 18, 2.8),
        "M20 4 8.1 15.9",
        "M14.5 14.5 20 20",
        "M8.1 8.1 12 12",
    ],
    "network": [
        _circ(12, 12, 2.4),
        _circ(12, 3.6, 1.8),
        _circ(4.2, 18.6, 1.8),
        _circ(19.8, 18.6, 1.8),
        "M12 5.4v4.2M10 13.3l-4.3 4.2M14 13.3l4.3 4.2",
        "M6.1 18.6h11.8",
    ],
    "shield": [
        "M12 2.6 19.6 5.6v5.8c0 4.7-3.2 8.5-7.6 10-4.4-1.5-7.6-5.3-7.6-10V5.6z",
        "M8.6 12.2l2.4 2.4 4.4-4.6",
    ],
    "brain": [
        "M12 4.6a3 3 0 0 0-5.4 1.4A3 3 0 0 0 4.1 9.8a3.1 3.1 0 0 0 .6 4.8A3 3 0 0 0 7.4 19a3 3 0 0 0 4.6.6z",
        "M12 4.6a3 3 0 0 1 5.4 1.4 3 3 0 0 1 2.5 3.8 3.1 3.1 0 0 1-.6 4.8A3 3 0 0 1 16.6 19a3 3 0 0 1-4.6.6z",
        "M12 4.6v15",
        "M7.8 9.6c1.3 0 2.2.9 2.2 2.2M16.2 9.6c-1.3 0-2.2.9-2.2 2.2",
        "M7.6 15.1c1.1 0 2-.5 2.4-1.3M16.4 15.1c-1.1 0-2-.5-2.4-1.3",
    ],
}


def _icon_paths(key):
    if key in ICONS:
        return ICONS[key]
    return [D.sparkle_path(12, 12, 9, 0.22)]


# ---------------------------------------------------------------------------
# 데이터
# ---------------------------------------------------------------------------


def _total(data, domains):
    c = data.get("commits") or {}
    t = c.get("total")
    if isinstance(t, (int, float)) and t > 0:
        return t
    s = sum(d.get("commits") or 0 for d in domains if isinstance(d.get("commits"), (int, float)))
    return s or 1


def _num(v):
    if isinstance(v, (int, float)):
        return v
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return 0


def _cumulative(data, key, k=7):
    """주 단위 누적 커밋 [0, …, 합계].

    주 경계는 마지막 날(asof)에서 거꾸로 7일씩 자른다. 그래서 짧은 조각은 맨 앞에만 생긴다.
    주별 합계를 그리면 진행 중인 마지막 날(당일 부분 집계)이 끝점을 끌어내려
    '최근 급감'처럼 읽혀서, 끝점이 타일 숫자와 같아지는 누적 곡선을 쓴다."""
    series = (data.get("commits") or {}).get("series") or []
    if not series:
        return []
    vals = [_num((s.get("by") or {}).get(key) or 0) for s in series]
    bounds = list(range(len(vals), 0, -k))[::-1]
    pts, run, prev = [0], 0, 0
    for b in bounds:
        run += sum(vals[prev:b])
        pts.append(run)
        prev = b
    return pts


def _smooth(points):
    """Catmull-Rom → 3차 베지어."""
    if len(points) < 2:
        return ""
    d = f"M{D.n(points[0][0])} {D.n(points[0][1])}"
    for i in range(len(points) - 1):
        p0 = points[i - 1] if i > 0 else points[i]
        p1, p2 = points[i], points[i + 1]
        p3 = points[i + 2] if i + 2 < len(points) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{D.n(c1[0])} {D.n(c1[1])} {D.n(c2[0])} {D.n(c2[1])} {D.n(p2[0])} {D.n(p2[1])}"
    return d


def _color(icon, i, dark):
    c = ICON_COLORS.get(icon) or FALLBACK_COLORS[i % len(FALLBACK_COLORS)]
    return c[0] if dark else c[1]


_SEPS = (" · ", " — ")


def _segments(s):
    """' · ' / ' — ' 로 구를 나눈다. [(앞 구분자, 구)] — 첫 구의 구분자는 ''."""
    out, sep, rest = [], "", str(s).strip()
    while rest:
        cut = min(((rest.find(x), x) for x in _SEPS if rest.find(x) >= 0), default=None)
        if cut is None:
            out.append((sep, rest))
            break
        i, x = cut
        if rest[:i].strip():
            out.append((sep, rest[:i].strip()))
        sep, rest = x, rest[i + len(x):].strip()
    return out


def _seg_wrap(s, size, max_w, family, weight=400):
    """구 단위 그리디 줄바꿈. 구가 한 줄보다 길 때만 공백 단위(D.wrap)로 내려간다.
    줄 끝 구분자는 버리고 다음 줄은 구로 시작한다. [(줄, 그 줄 뒤에서 버린 구분자)] 를 돌려준다."""
    lines, cur = [], ""
    for sep, seg in _segments(s):
        cand = cur + sep + seg if cur else seg
        if D.text_width(cand, size, family, weight) <= max_w:
            cur = cand
            continue
        if cur:
            lines.append([cur, sep])
        if D.text_width(seg, size, family, weight) <= max_w:
            cur = seg
            continue
        parts = D.wrap(seg, size, max_w, family, weight)
        lines.extend([pt, " "] for pt in parts[:-1])
        cur = parts[-1]
    if cur:
        lines.append([cur, ""])
    return lines or [["", ""]]


def _fit_subtitle(s, max_w, size, min_size, max_lines, family, weight=400):
    """max_lines 안에 들 때까지 축소, 그래도 넘치면 마지막 줄에 나머지를 이어 붙여 말줄임."""
    cur = size
    while True:
        lines = _seg_wrap(s, cur, max_w, family, weight)
        if len(lines) <= max_lines or cur <= min_size:
            break
        cur -= 0.5
    if len(lines) > max_lines:
        rest = "".join(t + sep for t, sep in lines[max_lines - 1:]).strip()
        lines = lines[:max_lines - 1] + [[D.truncate(rest, max_w, cur, family, weight), ""]]
    return cur, [t for t, _ in lines]


def _metric_pill(T, uid, x, y, max_w, metric, color, icol, delay_ms, dfs_acc, idx):
    """대표 성과 글래스 필. (svg, 폭). 자리가 너무 좁거나 metric 이 비면 ('', 0)."""
    p = P
    dark = T["dark"]
    metric = str(metric or "").strip()
    pad_l, star, gap, pad_r = 12, 14, 8, 14
    t_max = max_w - pad_l - star - gap - pad_r
    if not metric or t_max < 48:
        return "", 0
    fam = D.family_of(metric)
    size = D.fit_size(metric, t_max, 18, 16, fam, 600)
    txt = D.truncate(metric, t_max, size, fam, 600)
    est = D.text_width(txt, size, fam, 600)
    w = pad_l + star + gap + est + pad_r
    h = PILL_H
    cy = y + h / 2
    sx = x + pad_l + star / 2
    dfs_acc.append(f'<clipPath id="{uid}-pclip"><rect x="{D.n(x)}" y="{D.n(y)}" width="{D.n(w)}" height="{h}" rx="10"/></clipPath>')
    o = [f'<g class="{p}-fu" style="{D.delay(delay_ms)}">',
         f'<rect x="{D.n(x)}" y="{D.n(y)}" width="{D.n(w)}" height="{h}" rx="10" fill="{D.rgba(color, 0.15 if dark else 0.12)}" '
         f'stroke="{D.rgba(color, 0.5 if dark else 0.42)}" stroke-width="1"/>',
         f'<path d="M{D.n(x + 10)} {D.n(y + 1)}H{D.n(x + w - 10)}" stroke="{T["highlight"]}" stroke-width="1"/>',
         f'<g filter="url(#{p}-glow-s)"><path d="{D.sparkle_path(sx, cy, 7, 0.24)}" fill="{icol}" class="{p}-glow" '
         f'style="animation-delay:-{idx * 600}ms"/></g>',
         # 폭 추정이 넉넉해서(대체 폰트 대비) 왼쪽 정렬이면 오른쪽이 빈다 → 남는 칸 가운데에 둔다
         D.text(x + pad_l + star + gap + est / 2, cy + size * 0.36, txt, size, icol, 600, fam, "middle"),
         D.motion_only(p, f'<g clip-path="url(#{uid}-pclip)"><g transform="translate({D.n(x)},0)">'
                       f'<rect x="0" y="{D.n(y)}" width="60" height="{h}" fill="url(#{p}-shine)" opacity="{0.35 if dark else 0.6}" '
                       f'style="{D.anim(p, "k-bshine", 6, 3200 + idx * 520, D.EASE_IN_OUT)};--w:{D.n(w)}px"/></g></g>'),
         "</g>"]
    return "".join(o), w


def _odo_wrap(content, clip_id, x0, x1, y, size, delay_ms):
    """롤링 숫자를 라벨과 같은 시점에 페이드인하고, 캡하이트 근처에서 위아래를 부드럽게 지우는 마스크를 한 겹 더 씌워
    굴러가는 중의 이웃 숫자 조각이 깨진 글자처럼 보이지 않게 한다(최종 상태의 숫자 몸통은 불투명 1)."""
    p = P
    top, bot = y - size * 0.92, y + size * 0.26
    span = bot - top

    def at(v):
        return D.n((v - top) / span, 3)
    grad = (f'<linearGradient id="{clip_id}-capg" x1="0" y1="{D.n(top)}" x2="0" y2="{D.n(bot)}" gradientUnits="userSpaceOnUse">'
            f'<stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset="{at(y - size * 0.76)}" stop-color="#fff"/>'
            f'<stop offset="{at(y + size * 0.04)}" stop-color="#fff"/>'
            f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>')
    mask = (f'<mask id="{clip_id}-cap" maskUnits="userSpaceOnUse" x="{D.n(x0)}" y="{D.n(top)}" width="{D.n(x1 - x0)}" height="{D.n(span)}">'
            f'<rect x="{D.n(x0)}" y="{D.n(top)}" width="{D.n(x1 - x0)}" height="{D.n(span)}" fill="url(#{clip_id}-capg)"/></mask>')
    return (grad + mask
            + f'<g class="{p}-fi" style="{D.delay(delay_ms)}"><g mask="url(#{clip_id}-cap)">{content}</g></g>')


# ---------------------------------------------------------------------------
# 조각
# ---------------------------------------------------------------------------


def _background(T, theme):
    p = P
    dark = T["dark"]
    dfs, out = [], []
    blobs = [
        (1120, 70, 360, "#7C3AED", 0.7 if dark else 0.45, -2000),
        (140, 640, 420, "#00B4D8", 0.7, -7000),
        (700, 360, 460, "#14B8A6", 0.45, -11000),
        (1240, 620, 300, "#0077B6", 0.7, -4000),
    ]
    for i, (cx, cy, r, c, k, dl) in enumerate(blobs):
        gid = f"{p}-blob{i}"
        dfs.append(D.radial_gradient(gid, [(0, c, T["blob_opacity"] * k), (0.55, c, T["blob_opacity"] * k * 0.3), (1, c, 0)]))
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})" class="{p}-floats" style="animation-delay:{dl}ms;animation-duration:18s"/>')
    dfs.append(D.dot_grid_pattern(f"{p}-dots", theme, gap=24, r=1))
    dfs.append(D.fade_mask(f"{p}-dotsfade", W, H, "y", 0.3))
    out.append(f'<rect width="{W}" height="{H}" fill="url(#{p}-dots)" mask="url(#{p}-dotsfade)" opacity="0.8"/>')
    # 반짝이는 별(타일 사이 틈과 가장자리)
    R = D.rng(31)
    stars = []
    for k in range(26):
        x, y = R.uniform(20, W - 20), R.uniform(16, H - 16)
        r = R.uniform(0.8, 1.9)
        stars.append(f'<circle cx="{D.n(x)}" cy="{D.n(y)}" r="{D.n(r)}" class="{p}-tw" style="animation-delay:-{(k * 613) % 3600}ms"/>')
    out.append(f'<g fill="{T["particle"]}" opacity="{0.7 if dark else 0.45}">' + "".join(stars) + "</g>")
    return "".join(dfs), "".join(out)


def _header(T, data, domains, total, colors):
    p = P
    dark = T["dark"]
    dfs, out, css = [], [], []
    x0, x1 = M, W - M

    # 아이브로우: DOMAINS OWNED · 기간
    label = ""
    for s in data.get("stats") or []:
        if s.get("key") == "domains":
            label = str(s.get("label") or "")
    label = (label or "Domains").upper()
    since, asof = data.get("since"), data.get("asof")
    period = f"{D.fmt_date(since)} → {D.fmt_date(asof)}" if since and asof else ""
    eyebrow = label + (f"  ·  {period}" if period else "")
    out.append(D.eyebrow(p, x0, 30, eyebrow, T["theme"], "accent", "dot", max_w=720, delay_ms=80)[0])

    # 제목: "담당 도메인 N" — 다른 제목 섹션(skyline·orchestra)과 같은 그라디언트 글자 + 글로우 + 빛 스침
    count = str(len(domains))
    ts, ty = 44, TITLE_Y
    head_txt = "담당 도메인 " + count
    tw = D.text_width(head_txt, ts, "ko", 800)

    def title_text(fill):
        f = f' fill="{fill}"' if fill else ""
        return (f'<text x="{x0}" y="{ty}" font-size="{ts}" font-weight="800" letter-spacing="-0.5"{f} '
                f'font-family="{D.esc(D.FONT_KO)}">담당 도메인 <tspan font-family="{D.esc(D.FONT_LATIN)}">{D.esc(count)}</tspan></text>')

    dfs.append(D.linear_gradient(f"{p}-gt", T["grad_text"], x0, 0, x0 + tw, 0, units="userSpaceOnUse"))
    dfs.append(f'<clipPath id="{p}-title-clip">{title_text(None)}</clipPath>')
    dfs.append(D.linear_gradient(f"{p}-tshine", [(0, T["shine"], 0), (0.5, T["shine"], T["shine_opacity"]), (1, T["shine"], 0)]))
    css.append(D.shimmer_css(p, "k-tshine", x0 - 200, x0 + tw + 80, 0.3))
    glow = ""
    if dark:
        dfs.append(D.blur_filter(f"{p}-title-blur", 12))
        glow = f'<g opacity="0.45" class="{p}-glow" filter="url(#{p}-title-blur)">{title_text(T["accent"])}</g>'
    out.append(f'<g class="{p}-fu" style="{D.delay(160)}">{glow}{title_text(f"url(#{p}-gt)")}'
               f'<g clip-path="url(#{p}-title-clip)"><g style="{D.anim(p, "k-tshine", 8, 1900, D.EASE_IN_OUT)}">'
               f'<rect x="0" y="{D.n(ty - ts)}" width="120" height="{D.n(ts * 1.3)}" fill="url(#{p}-tshine)" transform="skewX(-18)"/></g></g></g>')

    # 오른쪽: 총 커밋 롤링 숫자
    val = D.fmt_int(total)
    dfs.append(D.linear_gradient(f"{p}-gnum", T["grad_text"], x1 - 220, 0, x1, 0, units="userSpaceOnUse"))
    out.append(f'<g class="{p}-fi" style="{D.delay(200)}">'
               + D.text(x1, 52, "TOTAL COMMITS", 16, T["muted"], 600, "mono", "end", ls=2) + "</g>")
    vsz = D.fit_size(val, 380, 44, 28, "latin", 800)
    vw = D.text_width(val, vsz, "latin", 800)
    out.append(_odo_wrap(D.odometer(p, x1, ty, val, vsz, f"url(#{p}-gnum)", "latin", 800, delay_ms=260, anchor="end",
                                    clip_id=f"{p}-odo-total"), f"{p}-odo-total", x1 - vw - 6, x1 + 6, ty, vsz, 200))

    # 도메인 비율 띠(타일 색과 같은 색) — 왼쪽부터 순차로 자란다
    by = TITLE_Y + 16
    bw = x1 - x0
    out.append(f'<rect x="{x0}" y="{by}" width="{bw}" height="5" rx="2.5" fill="{T["text2"]}" opacity="{0.12 if dark else 0.10}"/>')
    shares = [(i, max(_num(d.get("commits")), 0) / total) for i, d in enumerate(domains)]
    shares = [(i, s) for i, s in shares if s > 0]
    seg_gap = 3
    usable = bw - seg_gap * max(len(shares) - 1, 0)
    cx = x0
    for k, (i, s) in enumerate(shares):
        w = max(usable * min(s, 1), 4)
        if cx + w > x1:
            w = max(x1 - cx, 0)
        if w <= 0:
            break
        out.append(f'<rect x="{D.n(cx)}" y="{by}" width="{D.n(w)}" height="5" rx="2.5" fill="{colors[i]}" '
                   f'style="{D.anim(p, "k-grow", 0.9, 420 + k * 90, D.EASE_OUT, 1)};transform-box:fill-box;transform-origin:0 50%"/>')
        cx += w + seg_gap
    # 띠 위를 스치는 빛
    dfs.append(f'<clipPath id="{p}-hbar-clip"><rect x="{x0}" y="{by}" width="{bw}" height="5" rx="2.5"/></clipPath>')
    css.append(D.shimmer_css(p, "k-hshine", -140, bw + 140, 0.3))
    out.append(D.motion_only(p, f'<g clip-path="url(#{p}-hbar-clip)"><g transform="translate({x0},0)">'
               f'<rect x="0" y="{by - 2}" width="120" height="9" fill="url(#{p}-shine)" opacity="{0.6 if dark else 0.8}" '
               f'style="{D.anim(p, "k-hshine", 7, 2200, D.EASE_IN_OUT)}"/></g></g>'))
    return "".join(dfs), "".join(out), "".join(css)


def _tile_slots(n):
    """(col, row, span) — 첫 타일 2칸, 이후 왼→오, 위→아래."""
    slots = []
    occupied = set()
    for idx in range(n):
        for r in range(ROWS + 4):
            placed = False
            for c in range(COLS):
                span = 2 if idx == 0 else 1
                cells = [(c + k, r) for k in range(span)]
                if c + span <= COLS and not any(cl in occupied for cl in cells):
                    occupied.update(cells)
                    slots.append((c, r, span))
                    placed = True
                    break
            if placed:
                break
    return slots


def _tile(T, theme, data, dom, idx, slot, total, color, dfs_acc):
    p = P
    dark = T["dark"]
    col, row, span = slot
    tw = TILE_W * span + GAP * (span - 1)
    th = TILE_H
    tx = M + col * (TILE_W + GAP)
    ty = GRID_TOP + row * (TILE_H + GAP)
    big = span >= 2
    base_delay = 260 + idx * 115
    icon = str(dom.get("icon") or "")
    title = str(dom.get("title") or "")
    subtitle = str(dom.get("subtitle") or "")
    commits = _num(dom.get("commits"))
    ratio = min(max(commits / total, 0), 1) if total else 0
    uid = f"{p}-t{idx}"

    o = [f'<g transform="translate({D.n(tx)},{D.n(ty)})"><g class="{p}-fu" style="{D.delay(base_delay)}">']

    # 패널 — 글래스 + 타일 색으로 물든 안쪽 그라디언트
    o.append(D.glass(0, 0, tw, th, theme, p, r=TR))
    dfs_acc.append(D.radial_gradient(f"{uid}-tint", [(0, color, 0.20 if dark else 0.10), (1, color, 0)],
                                     cx=0.08, cy=0.1, r=0.75 if not big else 0.6))
    o.append(f'<rect x="0.75" y="0.75" width="{D.n(tw - 1.5)}" height="{D.n(th - 1.5)}" rx="{TR}" fill="url(#{uid}-tint)"/>')

    if big:
        dfs_acc.append(D.linear_gradient(f"{uid}-edge", [(0, color, 0.85 if dark else 0.7), (0.45, color, 0.12), (0.75, "#7C3AED", 0.15), (1, "#2DD4BF", 0.7 if dark else 0.55)], 0, 0, 1, 1))
        o.append(f'<rect x="0.75" y="0.75" width="{D.n(tw - 1.5)}" height="{D.n(th - 1.5)}" rx="{TR}" stroke="url(#{uid}-edge)" stroke-width="1.5" class="{p}-breathe" style="animation-duration:5s"/>')

    # 아이콘 배지
    bs = 60 if big else 52
    bx, by_ = 22, 22
    dfs_acc.append(D.linear_gradient(f"{uid}-badge", [(0, color, 0.26 if dark else 0.16), (1, color, 0.05 if dark else 0.04)], 0, 0, 1, 1))
    o.append(f'<g opacity="{0.55 if dark else 0.35}"><circle cx="{bx + bs / 2}" cy="{by_ + bs / 2}" r="{D.n(bs * 0.78)}" '
             f'fill="url(#{uid}-halo)" class="{p}-breathe" style="animation-delay:-{idx * 750}ms"/></g>')
    dfs_acc.append(D.radial_gradient(f"{uid}-halo", [(0, color, 0.55), (1, color, 0)]))
    o.append(f'<rect x="{bx}" y="{by_}" width="{bs}" height="{bs}" rx="{14 if big else 13}" fill="url(#{uid}-badge)" '
             f'stroke="{D.rgba(color, 0.55 if dark else 0.45)}" stroke-width="1.2"/>')
    o.append(f'<path d="M{bx + 12} {by_ + 1.4}H{bx + bs - 12}" stroke="{T["highlight"]}" stroke-width="1"/>')
    spk = D.mix(color, "#FFFFFF", 0.5) if dark else color
    o.append(f'<g opacity="{0.95 if dark else 0.8}"><path d="{D.sparkle_path(bx + bs - 1, by_ + 1, 6.5 if big else 5.5, 0.2)}" fill="{spk}" '
             f'class="{p}-tw" style="animation-delay:-{idx * 900}ms;animation-duration:4.2s"/></g>')

    s = (bs - 20) / 24
    ix, iy = bx + 10, by_ + 10
    paths = _icon_paths(icon)
    # 글로우 층(그리기가 끝난 뒤 떠오르고, 이후 맥동)
    glow_layer = "".join(f'<path d="{d}"/>' for d in paths)
    o.append(f'<g transform="translate({D.n(ix)},{D.n(iy)}) scale({D.n(s, 3)})" stroke="{color}" stroke-width="1.7" '
             f'stroke-linecap="round" stroke-linejoin="round" filter="url(#{p}-iglow)">'
             f'<g class="{p}-fi" style="{D.delay(base_delay + 1100)}"><g class="{p}-glow" style="animation-delay:-{idx * 500}ms">'
             f'{glow_layer}</g></g></g>')
    crisp = "".join(f'<path d="{d}" pathLength="1" class="{p}-draw" style="{D.delay(base_delay + 300 + k * 120)};animation-duration:1.2s"/>'
                    for k, d in enumerate(paths))
    icol = D.mix(color, "#FFFFFF", 0.25) if dark else color
    o.append(f'<g transform="translate({D.n(ix)},{D.n(iy)}) scale({D.n(s, 3)})" stroke="{icol}" stroke-width="1.6" '
             f'stroke-linecap="round" stroke-linejoin="round">{crisp}</g>')

    # 글자
    pad = 22
    tx0 = bx + bs + 18
    has_c = commits > 0
    if big:
        right_w = 250           # 오른쪽 수치·스파크라인 영역
        t_max = tw - tx0 - right_w - 16
        t_size = D.fit_size(title, t_max, 30, 22, D.family_of(title), 800)
        t_txt = D.truncate(title, t_max, t_size, D.family_of(title), 800)
        o.append(D.text(tx0, 54, t_txt, t_size, T["text"], 800))
        sub_max = tw - tx0 - right_w - 16
        ss, lines = _fit_subtitle(subtitle, sub_max, 20, 18, 2, D.family_of(subtitle))
        o.append(D.text_lines(tx0, 88, lines, ss, round(ss * 1.35, 1), T["text2"]))
        row_x0, row_x1, bar_h = tx0, tw - right_w - 28, 6
        min_bar = 64
        if has_c:
            rx_ = tw - 26
            dfs_acc.append(D.linear_gradient(f"{uid}-num", [D.mix(color, "#FFFFFF", 0.35) if dark else D.mix(color, "#000000", 0.1), color],
                                             rx_ - 170, 0, rx_, 0, units="userSpaceOnUse"))
            num = D.fmt_int(int(commits))
            nsz = D.fit_size(num, right_w - 10, 44, 28, "latin", 800)
            nw = D.text_width(num, nsz, "latin", 800)
            o.append(_odo_wrap(D.odometer(p, rx_, 64, num, nsz, f"url(#{uid}-num)", "latin", 800,
                                          delay_ms=base_delay + 300, anchor="end", clip_id=f"{uid}-odo"),
                               f"{uid}-odo", rx_ - nw - 6, rx_ + 6, 64, nsz, base_delay + 300))
            pct = f"{ratio * 100:.1f}%"
            o.append(f'<text x="{rx_}" y="90" text-anchor="end" font-size="16" font-family="{D.esc(D.FONT_MONO)}" fill="{T["muted"]}" '
                     f'class="{p}-fi" style="{D.delay(base_delay + 700)}">commits · '
                     f'<tspan fill="{icol}" font-weight="700">{pct}</tspan></text>')
            # 누적 커밋 곡선(이 도메인 실데이터, 끝점 = 위 숫자)
            wk = _cumulative(data, str(dom.get("key") or ""))
            if len(wk) >= 2 and max(wk) > 0:
                sx0, sx1, sy0, sy1 = tw - right_w + 4, tw - 26, 106, th - 20
                mx = max(wk)
                pts = [(sx0 + (sx1 - sx0) * i / (len(wk) - 1), sy1 - (sy1 - sy0) * (v / mx)) for i, v in enumerate(wk)]
                line = _smooth(pts)
                guides = "".join(f'<path d="M{D.n(sx0)} {D.n(sy0 + (sy1 - sy0) * k / 3)}H{D.n(sx1)}"/>' for k in range(4))
                o.append(f'<g stroke="{T["text2"]}" stroke-width="1" stroke-dasharray="2 5" opacity="{0.22 if dark else 0.3}">{guides}</g>')
                o.append(f'<g class="{p}-fi" style="{D.delay(base_delay + 700)}">'
                         + D.text(sx0, sy0 + 16, "누적", 16, T["muted"], 600, "ko") + "</g>")
                area = line + f"L{D.n(sx1)} {D.n(sy1)}L{D.n(sx0)} {D.n(sy1)}Z"
                dfs_acc.append(D.linear_gradient(f"{uid}-area", [(0, color, 0.34 if dark else 0.22), (1, color, 0)], 0, 0, 0, 1))
                dfs_acc.append(D.linear_gradient(f"{uid}-sline", [(0, color, 0.3), (0.6, color, 1), (1, D.mix(color, "#FFFFFF", 0.4) if dark else color, 1)]))
                o.append(f'<path d="{area}" fill="url(#{uid}-area)" class="{p}-fi" style="{D.delay(base_delay + 900)};animation-duration:1.4s"/>')
                o.append(f'<path d="{line}" pathLength="1" stroke="url(#{uid}-sline)" stroke-width="2" stroke-linecap="round" '
                         f'filter="url(#{p}-glow-s)" class="{p}-draw" style="{D.delay(base_delay + 600)}"/>')
                lx, ly = pts[-1]
                o.append(f'<g class="{p}-pop" style="{D.delay(base_delay + 1900)}"><circle cx="{D.n(lx)}" cy="{D.n(ly)}" r="4" fill="{icol}" '
                         f'filter="url(#{p}-glow-s)"/></g>')
                o.append(f'<g opacity="{0.8 if dark else 0.6}"><circle cx="{D.n(lx)}" cy="{D.n(ly)}" r="4" fill="none" stroke="{color}" '
                         f'stroke-width="1.4" style="{D.anim(p, "k-ping", 3.2, base_delay + 2200, "ease-out")};transform-box:fill-box;transform-origin:center"/></g>')
    else:
        t_max = tw - tx0 - pad
        fam = D.family_of(title)
        t_size = D.fit_size(title, t_max, 23, 19, fam, 700)
        t_txt = D.truncate(title, t_max, t_size, fam, 700)
        o.append(D.text(tx0, 47 if has_c else 56, t_txt, t_size, T["text"], 700))
        if has_c:
            pct = f"{ratio * 100:.1f}%"
            o.append(f'<g class="{p}-fi" style="{D.delay(base_delay + 600)}">'
                     f'<text x="{tx0}" y="72" font-size="16" font-family="{D.esc(D.FONT_MONO)}" fill="{T["text2"]}">'
                     f'<tspan font-weight="700" fill="{T["text"]}">{D.esc(D.fmt_int(int(commits)))}</tspan> commits</text>'
                     + D.text(tw - pad, 72, pct, 16, icol, 700, "mono", "end") + "</g>")
        sub_max = tw - 2 * pad
        ss, lines = _fit_subtitle(subtitle, sub_max, 18, 18, 2, D.family_of(subtitle))
        sy = 102 if has_c else 106
        o.append(D.text_lines(pad, sy, lines, ss, 24, T["text2"]))
        row_x0, row_x1, bar_h = pad, tw - pad, 5
        min_bar = 44

    # 맨 아래 줄 — 왼쪽 metric 필, 오른쪽 남은 폭에 비율 막대(커밋 0 이면 필이 줄 전체)
    pill_y = th - PILL_BOTTOM - PILL_H
    row_w = row_x1 - row_x0
    pill_max = row_w - (min_bar + 14 if has_c else 0)
    pill_svg, pill_w = _metric_pill(T, uid, row_x0, pill_y, pill_max, dom.get("metric"), color, icol,
                                    base_delay + 500, dfs_acc, idx)
    o.append(pill_svg)
    if pill_w:
        bar_x, bar_y = row_x0 + pill_w + 14, pill_y + (PILL_H - bar_h) / 2
    else:
        bar_x, bar_y = row_x0, (th - 26 if big else th - 18)
    bar_w = row_x1 - bar_x

    # 큰 워터마크 아이콘 — 오른쪽 위~중간, 맨 아래 줄 위에서 타일 안에 온전히
    if not big:
        floor = (pill_y if pill_w else bar_y) - 10
        wm = min(84, floor - 30)
        if wm >= 48:
            wm_s = wm / 24
            wm_x, wm_y = tw - wm - 18, 30 + (floor - 30 - wm) / 2
            o.append(f'<g transform="translate({D.n(wm_x)},{D.n(wm_y)}) scale({D.n(wm_s, 3)}) rotate(-10 12 12)" '
                     f'opacity="{0.06 if dark else 0.07}" stroke="{color}" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">'
                     + "".join(f'<path d="{d}"/>' for d in _icon_paths(icon)) + "</g>")

    # 비율 막대 — 자라고, 빛이 스친다
    if has_c:
        fw = max(bar_w * ratio, 8)
        dfs_acc.append(D.linear_gradient(f"{uid}-bar", [D.mix(color, "#0077B6", 0.35), color, D.mix(color, "#FFFFFF", 0.3) if dark else color]))
        o.append(f'<rect x="{D.n(bar_x)}" y="{D.n(bar_y)}" width="{D.n(bar_w)}" height="{bar_h}" rx="{bar_h / 2}" fill="{T["text2"]}" opacity="{0.12 if dark else 0.1}"/>')
        o.append(f'<rect x="{D.n(bar_x)}" y="{D.n(bar_y)}" width="{D.n(fw)}" height="{bar_h}" rx="{bar_h / 2}" fill="url(#{uid}-bar)" '
                 f'style="{D.anim(p, "k-grow", 1.1, base_delay + 500, D.EASE_OUT, 1)};transform-box:fill-box;transform-origin:0 50%"/>')
        o.append(f'<g opacity="{0.9 if dark else 0.55}"><circle cx="{D.n(bar_x + fw)}" cy="{D.n(bar_y + bar_h / 2)}" r="{bar_h * 0.7}" '
                 f'fill="{icol}" filter="url(#{p}-glow-s)" class="{p}-fi" style="{D.delay(base_delay + 1500)}"/></g>')
        dfs_acc.append(f'<clipPath id="{uid}-barclip"><rect x="{D.n(bar_x)}" y="{D.n(bar_y)}" width="{D.n(fw)}" height="{bar_h}" rx="{bar_h / 2}"/></clipPath>')
        o.append(D.motion_only(p, f'<g clip-path="url(#{uid}-barclip)"><g transform="translate({D.n(bar_x)},0)">'
                 f'<rect x="0" y="{D.n(bar_y - 2)}" width="60" height="{bar_h + 4}" fill="url(#{p}-shine)" opacity="{0.75 if dark else 0.9}" '
                 f'style="{D.anim(p, "k-bshine", 6, 2400 + idx * 520, D.EASE_IN_OUT)};--w:{D.n(fw)}px"/></g></g>'))

    # 테두리를 도는 그라디언트 빛(혜성: 꼬리·몸통·머리 세 겹)
    rr = _rrect(0.75, 0.75, tw - 1.5, th - 1.5, TR - 0.5)
    dur = 9 if not big else 11
    ph = -((idx * 1270) % (dur * 1000))
    comet = []
    for kname, sw, op, flt in (("k-run-t", 2.2, 0.35, ""), ("k-run-m", 2.2, 0.75, ""), ("k-run-h", 2.8, 1, f' filter="url(#{p}-iglow)"')):
        dash = {"k-run-t": 0.16, "k-run-m": 0.07, "k-run-h": 0.022}[kname]
        comet.append(f'<g opacity="{D.n(op * (1 if dark else 0.9), 2)}"><path d="{rr}" pathLength="1" stroke="url(#{p}-comet)" stroke-width="{sw}" '
                     f'stroke-linecap="round" stroke-dasharray="{dash} {D.n(1 - dash, 3)}"{flt} '
                     f'style="{D.anim(p, kname, dur, ph, "linear")}"/></g>')
    o.append(D.motion_only(p, "".join(comet)))

    o.append("</g></g>")
    return "".join(o)


def render(theme, data):
    T = D.tokens(theme)
    p = P
    dark = T["dark"]
    domains = [d for d in (data.get("domains") or []) if isinstance(d, dict)][: COLS * ROWS - 1]
    total = _total(data, domains)
    colors = [_color(str(d.get("icon") or ""), i, dark) for i, d in enumerate(domains)]

    bg_defs, bg = _background(T, theme)
    h_defs, header, h_css = _header(T, data, domains, total, colors)

    tile_defs = []
    slots = _tile_slots(len(domains))
    tiles = "".join(_tile(T, theme, data, d, i, slots[i], total, colors[i], tile_defs) for i, d in enumerate(domains))

    comet_stops = ([(0, "#90E0EF"), (0.3, "#00B4D8"), (0.6, "#2DD4BF"), (0.85, "#A78BFA"), (1, "#90E0EF")] if dark
                   else [(0, "#0077B6"), (0.35, "#00B4D8"), (0.65, "#14B8A6"), (1, "#7C3AED")])
    common = D.defs(
        D.card_clip(f"{p}-clip", W, H),
        D.glass_defs(theme, p),
        D.glow_filter(f"{p}-glow-s", 3, 1.0 if dark else 0.45),
        D.glow_filter(f"{p}-iglow", 2.2 if dark else 1.6, 1.0 if dark else 0.5),
        D.linear_gradient(f"{p}-comet", comet_stops, 0, 0, 1, 1),
        D.linear_gradient(f"{p}-shine", [(0, T["shine"], 0), (0.5, T["shine"], 0.9 if dark else 1), (1, T["shine"], 0)]),
        bg_defs,
        h_defs,
        "".join(tile_defs),
    )

    css = (D.keyframes(p, "k-grow", "from{transform:scaleX(0)}")
           + D.keyframes(p, "k-run-t", "from{stroke-dashoffset:.16}to{stroke-dashoffset:-.84}")
           + D.keyframes(p, "k-run-m", "from{stroke-dashoffset:.07}to{stroke-dashoffset:-.93}")
           + D.keyframes(p, "k-run-h", "from{stroke-dashoffset:.022}to{stroke-dashoffset:-.978}")
           + D.keyframes(p, "k-ping", "0%{transform:scale(1);opacity:.9}70%,100%{transform:scale(3.2);opacity:0}")
           + D.keyframes(p, "k-bshine", "0%{transform:translateX(-70px)}35%,100%{transform:translateX(var(--w,360px))}")
           + h_css)

    body = (D.card(W, H, theme, p)
            + common
            + f'<g clip-path="url(#{p}-clip)">{bg}</g>'
            + header
            + tiles)
    names = ", ".join(str(d.get("title") or "") for d in domains)
    desc = f"담당 도메인 {len(domains)}개와 도메인별 커밋 비율: {names}"
    return D.svg_root(W, H, theme, "담당 도메인", desc, body, css, p)
