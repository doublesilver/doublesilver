"""timeline (1280×452) — 입사부터 오늘까지의 가로 여정.

진행선이 스스로 그려지며 선 끝(빛 머리)이 지나가는 순서대로 마일스톤이 팝하고,
글래스 카드가 위/아래 번갈아 떠오른다. 선 뒤에는 일별 커밋 파형(같은 시간축)이
함께 드러나고, 끝에는 'NOW' 비콘이 맥동한다.
"""

from __future__ import annotations

import datetime as _dt

from . import design as D

W, H = 1280, 452
P = "timeline"

AXIS_Y = 250              # 진행선 기본 높이(위 카드가 크면 아래로 조금 내려간다)
HEAD_CLEAR = 70           # 위 카드가 넘지 않을 머리글 아래 경계
X0 = 88                   # 시간축 시작(첫 달 1일)
XE = W - 96               # 시간축 끝(오늘이 속한 달의 다음 달 1일)
X_FUTURE = W - 36         # 미래 점선이 사라지는 곳
EDGE = 24                 # 카드가 카드 배경 가장자리에서 떨어지는 최소 거리

TOP_GAP = 52              # 위 카드 아래변 ↔ 진행선
BOT_GAP = 46              # 진행선 ↔ 아래 카드 윗변(사이에 달 눈금 글자)
CARD_PAD = 18
CARD_GAP = 18             # 같은 쪽 카드 사이 최소 간격
CARD_CAP = 304            # 카드 최대 폭
CARD_MIN = 176

WAVE_UP = 42              # 커밋 파형 위쪽 최대 높이
WAVE_REFLECT = 0.26       # 아래쪽 반사 비율

# 등장 연출 시계(ms) — 2.5초 안에 모두 최종 상태
LINE_START = 150
LINE_DUR = 1300

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


# ---------------------------------------------------------------------------
# 날짜 · 시간축
# ---------------------------------------------------------------------------


def _parse(s):
    """'YYYY-MM-DD' → (date, True), 'YYYY-MM' → (그 달 15일, False). 실패하면 None."""
    try:
        parts = [int(x) for x in str(s).strip().split("-")]
        if len(parts) >= 3:
            return _dt.date(parts[0], parts[1], parts[2]), True
        if len(parts) == 2:
            return _dt.date(parts[0], parts[1], 15), False
    except (ValueError, TypeError):
        pass
    return None


def _month_start(d):
    return d.replace(day=1)


def _next_month(d):
    return (d.replace(day=28) + _dt.timedelta(days=4)).replace(day=1)


class _Scale:
    """시간 → x. 사건(마일스톤·NOW)이 몰린 구간은 늘리고 한산한 구간은 줄이는 단조 비선형 축.

    선형 위치와 균등 위치를 섞되, 사건 사이 최소 간격을 만족하는 가장 작은 섞음 비율을 쓴다.
    달 눈금·커밋 파형도 같은 함수로 그려서 마일스톤과 눈금이 어긋나지 않는다."""

    def __init__(self, start, end, events):
        self.start, self.end = start, end
        self.span = max((end - start).days, 1)
        lo, hi = X0 + 34, XE - 8
        days = [(d - start).days for d in events]
        lin = [X0 + (XE - X0) * dd / self.span for dd in days]
        m = len(events)
        if m >= 2:
            even = [lo + (hi - lo) * k / (m - 1) for k in range(m)]
            gap = min(96, (hi - lo) / (m - 1) * 0.92)
            alpha = 1.0
            for step in range(21):
                a = step / 20
                xs = [(1 - a) * l + a * e for l, e in zip(lin, even)]
                if all(xs[k + 1] - xs[k] >= gap for k in range(m - 1)):
                    alpha = a
                    break
            self.events_x = [(1 - alpha) * l + alpha * e for l, e in zip(lin, even)]
        else:
            self.events_x = [D.clamp(l, lo, hi) for l in lin]
        knots = [(0, X0)]
        for dd, x in zip(days, self.events_x):
            if dd > knots[-1][0] and x >= knots[-1][1]:
                knots.append((dd, x))
            elif dd == knots[-1][0] and x >= knots[-1][1]:
                # 같은 날 사건이 여럿이면 그 날짜는 마지막 사건 자리로 — NOW 가 그 노드와 같은 x 가 되게
                knots[-1] = (dd, x)
        if self.span > knots[-1][0]:
            knots.append((self.span, max(XE, knots[-1][1])))
        self.knots = knots

    def x(self, d):
        dd = (d - self.start).days if not isinstance(d, (int, float)) else d
        k = self.knots
        if dd <= k[0][0]:
            return k[0][1]
        for (d0, x0), (d1, x1) in zip(k, k[1:]):
            if dd <= d1:
                return x0 + (x1 - x0) * (dd - d0) / max(d1 - d0, 1e-9)
        return k[-1][1]


def _items(data):
    """정렬된 마일스톤 [(date, exact, raw)] 과 since·asof."""
    raw = [t for t in (data.get("timeline") or []) if isinstance(t, dict)]
    parsed = []
    for t in raw:
        p = _parse(t.get("date", ""))
        if p:
            parsed.append((p[0], p[1], t))
    parsed.sort(key=lambda r: r[0])
    since = (_parse(data.get("since", "")) or (None,))[0]
    asof = (_parse(data.get("asof", "")) or (None,))[0]
    if asof is None:
        asof = parsed[-1][0] if parsed else _dt.date.today()
    if since is None:
        since = parsed[0][0] if parsed else asof
    # 월 단위 항목이 오늘 이후로 가지 않게(진행 중인 달은 1일과 오늘 사이 가운데)
    fixed = []
    for d, exact, t in parsed:
        if not exact and d > asof:
            ms = _month_start(d)
            d = ms + (asof - ms) / 2 if asof >= ms else asof
        fixed.append((d, exact, t))
    return fixed, since, asof


# ---------------------------------------------------------------------------
# 카드 레이아웃(위/아래 따로, 겹치지 않게)
# ---------------------------------------------------------------------------


def _layout_side(slots):
    """slots: [{x, want_w}] (x 순) → 각 slot 에 left, w 를 채운다. 겹치면 폭을 줄인다."""
    if not slots:
        return
    avail = W - 2 * EDGE - CARD_GAP * (len(slots) - 1)
    fixed = sum(s["want_w"] for s in slots if s.get("fixed"))
    flex = sum(s["want_w"] for s in slots if not s.get("fixed"))
    k = min(1.0, (avail - fixed) / flex) if flex else 1.0
    for s in slots:
        s["w"] = s["want_w"] if s.get("fixed") else max(s["min_w"], s["want_w"] * k)
    # 노드 가운데 정렬 → 왼쪽부터 밀기 → 오른쪽 끝에서 되밀기(총폭이 맞으면 겹침 없음)
    for s in slots:
        s["left"] = s["x"] - s["w"] / 2
    for i, s in enumerate(slots):
        s["left"] = max(s["left"], EDGE if i == 0 else slots[i - 1]["left"] + slots[i - 1]["w"] + CARD_GAP)
    for i in range(len(slots) - 1, -1, -1):
        lim = W - EDGE if i == len(slots) - 1 else slots[i + 1]["left"] - CARD_GAP
        slots[i]["left"] = min(slots[i]["left"], lim - slots[i]["w"])


def _card_text(t, w):
    """카드 안 글자(크기·줄) 계산."""
    inner = w - CARD_PAD * 2
    title = str(t.get("title", ""))
    sub = str(t.get("sub", ""))
    tfam = D.family_of(title)
    tsize = D.fit_size(title, inner, 23, 19, tfam, 700)
    if D.text_width(title, tsize, tfam, 700) <= inner:
        tlines = [title]
    else:
        tsize, tlines = D.fit_block(title, inner, 21, 18, 2, tfam, 700)
    sfam = D.family_of(sub)
    ssize, slines = D.fit_block(sub, inner, 18, 16, 3 - len(tlines), sfam, 400) if sub else (18, [])
    return tlines, tsize, tfam, slines, ssize, sfam


TITLE_Y, TITLE_LH, SUB_GAP, SUB_LH = 62, 27, 27, 23


def _card_height(n_title, n_sub):
    return TITLE_Y + TITLE_LH * (n_title - 1) + (SUB_GAP + SUB_LH * (n_sub - 1) if n_sub else 0) + 22


# ---------------------------------------------------------------------------
# 렌더
# ---------------------------------------------------------------------------


def _color_at(T, f):
    """진행선 그라디언트(ocean→cyan→teal) 위 위치 f(0..1)의 색. 라이트는 진하게."""
    c = T["grad"]
    col = D.mix(c[0], c[1], f * 2) if f < 0.5 else D.mix(c[1], c[2], (f - 0.5) * 2)
    return col if T["dark"] else D.mix(col, "#003A5C", 0.18)


def _stat(data, key):
    for s in data.get("stats") or []:
        if isinstance(s, dict) and s.get("key") == key:
            return s
    return None


def render(theme, data):
    T = D.tokens(theme)
    p = P
    dark = T["dark"]
    items, since, asof = _items(data)

    start = _month_start(min([since] + [d for d, _, _ in items]))
    end = _next_month(max([asof] + [d for d, _, _ in items]))
    # 사건 = 마일스톤 + NOW. 오늘 날짜의 마일스톤이 있으면 NOW 를 따로 두지 않고 그 노드에 합친다
    # (따로 두면 최소 간격만큼 벌어져 0일 구간이 시간이 흐른 것처럼 보인다)
    same_day = [i for i, (d, _, _) in enumerate(items) if d == asof]
    merged = same_day[-1] if same_day else None
    events = sorted([(d, 0, i) for i, (d, _, _) in enumerate(items)] + ([] if same_day else [(asof, 1, -1)]))
    S = _Scale(start, end, [e[0] for e in events])

    # ── 위치 ────────────────────────────────────────────────
    n_items = len(items)
    xs = [0.0] * n_items
    x_now = XE
    for (d, kind, i), x in zip(events, S.events_x):
        if kind == 1:
            x_now = x
        else:
            xs[i] = x
    if merged is not None:
        x_now = xs[merged]
    assert abs(S.x(asof) - x_now) < 1e-6, "NOW 위치와 시간축의 오늘 위치가 어긋남"
    # 진행선은 입사일(since)에서 출발한다 — 그 앞은 흐린 트랙만
    x_start = min(D.clamp(S.x(since), X0, x_now - 40), xs[0] if xs else x_now)
    span_px = max(x_now - x_start, 1)

    def t_at(x):  # 빛 머리가 x 에 닿는 시각(ms)
        return LINE_START + LINE_DUR * D.clamp((x - x_start) / span_px, 0, 1)

    # ── 카드 슬롯 ──────────────────────────────────────────
    sides = {"top": [], "bot": []}
    for i, (d, exact, t) in enumerate(items):
        side = "top" if i % 2 == 0 else "bot"
        title, sub = str(t.get("title", "")), str(t.get("sub", ""))
        date_w = D.text_width(D.fmt_date(str(t.get("date", ""))) + "   00", 16, "mono", 600) + CARD_PAD * 2
        want = max(D.text_width(title, 23, D.family_of(title), 700),
                   min(D.text_width(sub, 18, D.family_of(sub)), CARD_CAP)) + CARD_PAD * 2
        sides[side].append({"i": i, "x": xs[i], "want_w": D.clamp(max(want, date_w), CARD_MIN, CARD_CAP),
                            "min_w": max(date_w, 150)})
    if merged is not None:   # 합쳐진 노드 카드의 반대편
        now_side = "bot" if merged % 2 == 0 else "top"
    else:                    # 마지막 카드 반대편
        now_side = "bot" if (n_items % 2 == 1) else "top"
    now_label = "NOW"
    now_date = D.fmt_date(asof.isoformat())
    now_w = D.text_width(now_label, 18, "mono", 700) + D.text_width("  " + now_date, 16, "mono", 500) + 30 + 26
    sides[now_side].append({"i": "now", "x": x_now, "want_w": now_w, "fixed": True})
    for side in sides.values():
        side.sort(key=lambda s: s["x"])
        _layout_side(side)
    slot_of = {s["i"]: (side_name, s) for side_name, side in sides.items() for s in side}

    # 같은 쪽 카드 높이를 맞춘다
    texts = {}
    side_h = {"top": 0, "bot": 0}
    for side_name, side in sides.items():
        for s in side:
            if s["i"] == "now":
                continue
            ct = _card_text(items[s["i"]][2], s["w"])
            texts[s["i"]] = ct
            side_h[side_name] = max(side_h[side_name], _card_height(len(ct[0]), len(ct[3])))
    # 위 카드가 머리글을 덮지 않게, 아래 카드가 바닥을 넘지 않게 축 높이를 고른다
    ay = D.clamp(HEAD_CLEAR + side_h["top"] + TOP_GAP, AXIS_Y, H - 16 - BOT_GAP - side_h["bot"])
    top_y1 = ay - TOP_GAP                      # 위 카드 아래변
    # 가로 직선은 bbox 높이가 0 이라 기본(objectBoundingBox) 필터 영역이 비어 아무것도 안 그려진다
    # → 선 전용 필터는 userSpaceOnUse 영역으로 따로 만든다
    fr = f'filterUnits="userSpaceOnUse" x="0" y="{D.n(ay - 40)}" width="{W}" height="80"'
    line_filters = (f'<filter id="{p}-soft" {fr}><feGaussianBlur stdDeviation="9"/></filter>'
                    f'<filter id="{p}-glow-line" {fr} color-interpolation-filters="sRGB">'
                    f'<feGaussianBlur in="SourceGraphic" stdDeviation="3.5" result="b"/>'
                    f'<feComponentTransfer in="b" result="bb"><feFuncA type="linear" slope="{1.2 if T["dark"] else 0.7}"/></feComponentTransfer>'
                    f'<feMerge><feMergeNode in="bb"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')
    bot_y0 = ay + BOT_GAP                      # 아래 카드 윗변

    # ── defs ───────────────────────────────────────────────
    c1, c2, c3 = T["grad"]
    line_cols = [c1, c2, c3] if dark else ["#005F92", "#0087C2", "#0D9488"]
    dfs = [
        D.card_clip(f"{p}-clip", W, H),
        D.glass_defs(theme, p),
        D.linear_gradient(f"{p}-line", line_cols, x_start, 0, x_now, 0, units="userSpaceOnUse"),
        D.linear_gradient(f"{p}-wave", [(0, c1, 1), (0.55, c2, 1), (1, "#7C3AED", 1)], x_start, 0, x_now, 0, units="userSpaceOnUse"),
        D.linear_gradient(f"{p}-wave-l", [(0, D.mix(c1, "#003A5C", 0.28), 1), (0.55, D.mix(c2, "#003A5C", 0.28), 1), (1, D.mix("#7C3AED", "#003A5C", 0.2), 1)],
                          x_start, 0, x_now, 0, units="userSpaceOnUse"),
        D.linear_gradient(f"{p}-future", [(0, T["accent"], 0.7), (1, T["accent"], 0)], x_now, 0, X_FUTURE, 0, units="userSpaceOnUse"),
        D.linear_gradient(f"{p}-beam", [(0, T["coral"], 0), (0.5, T["coral"], 0.55 if dark else 0.35), (1, T["coral"], 0)], 0, 0, 0, 1),
        D.linear_gradient(f"{p}-cardbar", [(0, c2, 1), (1, c3, 0)]),
        D.glow_filter(f"{p}-glow", 5, 0.95 if dark else 0.45),
        D.glow_filter(f"{p}-glow-s", 2.6, 1.0 if dark else 0.5),
        D.dot_grid_pattern(f"{p}-dots", theme, gap=26, r=1.0),
        D.fade_mask(f"{p}-fadey", W, H, axis="y", edge=0.22),
        D.radial_gradient(f"{p}-halo", [(0, "#00B4D8", 0.5 if dark else 0.28), (1, "#00B4D8", 0)]),
        D.radial_gradient(f"{p}-nowhalo", [(0, T["coral"], 0.55 if dark else 0.3), (1, T["coral"], 0)]),
    ]
    css = []
    dfs.append(line_filters)

    # ── 배경 ───────────────────────────────────────────────
    bg = [f'<g clip-path="url(#{p}-clip)">']
    blobs = [(180, 470, 380, "#00B4D8", 0.7, 0), (700, -60, 360, "#7C3AED", 0.55 if dark else 0.4, -6000),
             (1180, 420, 340, "#14B8A6", 0.6, -10000), (1020, 40, 260, "#0077B6", 0.6, -3000)]
    for i, (cx, cy, r, c, k, dl) in enumerate(blobs):
        gid = f"{p}-blob{i}"
        dfs.append(D.radial_gradient(gid, [(0, c, T["blob_opacity"] * k), (0.55, c, T["blob_opacity"] * k * 0.35), (1, c, 0)]))
        bg.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})" class="{p}-floats" style="animation-delay:{dl}ms;animation-duration:18s"/>')
    bg.append(f'<rect width="{W}" height="{H}" fill="url(#{p}-dots)" mask="url(#{p}-fadey)" opacity="0.8"/>')

    # 달 경계 세로선(흐리게) + 오늘까지는 은은한 진행 영역
    month_marks = []
    m = start
    while m <= end:
        month_marks.append(m)
        m = _next_month(m)
    grid = [f'<g mask="url(#{p}-fadey)" stroke="{T["line"]}" stroke-width="1" stroke-dasharray="2 6" opacity="{0.22 if dark else 0.3}">']
    for m in month_marks:
        x = S.x(m)
        grid.append(f'<path d="M{D.n(x)} 72V{H - 16}"/>')
    grid.append("</g>")
    bg.append("".join(grid))

    # 반짝이는 미세 입자
    R = D.rng(42)
    stars = [f'<g fill="{T["particle"]}">']
    for k in range(26):
        x, y = R.uniform(30, W - 30), R.uniform(30, H - 30)
        r = R.uniform(0.8, 1.9)
        op = R.uniform(0.35, 0.8) * (1 if dark else 0.6)
        stars.append(f'<g opacity="{D.n(op, 2)}"><circle cx="{D.n(x)}" cy="{D.n(y)}" r="{D.n(r)}" class="{p}-tw" style="animation-delay:-{(k * 613) % 3600}ms"/></g>')
    stars.append("</g>")
    bg.append("".join(stars))
    bg.append("</g>")

    # ── 머리글 ─────────────────────────────────────────────
    head = []
    hx, hy = 72, 48
    sp = D.sparkle_path(hx + 9, hy - 6, 10)
    head.append(f'<g class="{p}-fi"><path d="{sp}" fill="{T["accent3"]}" filter="url(#{p}-glow-s)" class="{p}-pulse"/></g>')
    eyebrow = "JOURNEY"
    ex = hx + 30
    ew = D.text_width(eyebrow, 18, "mono", 700, letter_spacing=3)
    head.append(f'<g class="{p}-fi" style="{D.delay(60)}">' + D.text(ex, hy, eyebrow, 18, T["accent"], 700, "mono", ls=3) + "</g>")
    rng_txt = f"{D.fmt_date(since.isoformat())}  →  {D.fmt_date(asof.isoformat())}"
    rx = ex + ew + 22
    head.append(f'<g class="{p}-fi" style="{D.delay(160)}">'
                f'<path d="M{D.n(rx - 11)} {hy - 14}V{hy + 2}" stroke="{T["border_hi"]}" stroke-width="1.5"/>'
                + D.text(rx + 2, hy, rng_txt, 18, T["text2"], 500, "mono") + "</g>")
    # 오른쪽 칩: 데이터의 stats 에서
    labels = []
    for key in ("days", "commits"):
        s = _stat(data, key)
        if s and s.get("value") not in (None, ""):
            labels.append(f'{s.get("value")} {s.get("label", "")}'.strip())
    if labels:
        left_used = rx + 2 + D.text_width(rng_txt, 18, "mono", 500) + 28
        max_w = (W - 56) - left_used
        if max_w > 120:
            sizes = [D.text_width(l, 16, D.family_of(l), 600) + 26 for l in labels]
            est = sum(sizes) + 10 * (len(labels) - 1)
            cx0 = max(left_used, (W - 56) - min(est, max_w))
            chips, _ = D.chips_row(cx0, hy - 23, labels, theme, max_w, size=16, variants=["teal", "violet"],
                                   cls_fn=lambda i: (f"{p}-pop", D.stagger(i, 240, 110)))
            head.append(chips)

    # ── 커밋 파형(같은 시간축, 진행선과 함께 드러난다) ─────────
    commits = data.get("commits") or {}
    series = [r for r in commits.get("series") or [] if isinstance(r, dict)]
    wave = ""
    if series:
        vmax = max((r.get("total") or 0) for r in series) or 1
        segs = []
        for r in series:
            dd = _parse(r.get("date", ""))
            v = r.get("total") or 0
            if not dd or v <= 0:
                continue
            x = S.x((dd[0] - start).days + 0.5)
            if x > x_now + 4:
                continue
            h = max(2.0, WAVE_UP * (v / vmax) ** 0.5)
            day = (dd[0] - start).days
            bw = D.clamp((S.x(day + 1) - S.x(day)) * 0.56, 0.8, 3.4)   # 압축된 구간에선 막대를 가늘게
            segs.append(f"M{D.n(x - bw / 2)} {D.n(ay - 6)}h{D.n(bw)}v-{D.n(h - bw / 2)}a{D.n(bw / 2)} {D.n(bw / 2)} 0 0 0-{D.n(bw)} 0z")
        dfs.append(f'<path id="{p}-wavepath" d="{"".join(segs)}"/>')   # 채움은 <use> 쪽에서(테마별로 다르게)
        rw = x_now - x_start + 12
        dfs.append(f'<clipPath id="{p}-wclip"><rect x="{D.n(x_start - 6)}" y="{ay - WAVE_UP - 20}" width="{D.n(rw)}" height="{WAVE_UP * 2 + 40}" '
                   f'style="{D.anim(p, "k-reveal", LINE_DUR / 1000, LINE_START, "linear", "1")};transform-box:fill-box;transform-origin:0 0"/></clipPath>')
        css.append(D.keyframes(p, "k-reveal", "from{transform:scaleX(0)}"))
        refl = ay * (1 + WAVE_REFLECT)
        # 라이트는 밝은 표면 위라 그대로 두면 흐린 얼룩 → 진행선처럼 어둡게 섞고 더 진하게
        main_fill = f' fill="url(#{p}-wave{"" if dark else "-l"})"'
        wave = (f'<g clip-path="url(#{p}-wclip)">'
                f'<g opacity="{0.55 if dark else 0.78}"><use href="#{p}-wavepath"{main_fill}/></g>'
                f'<g opacity="{0.22 if dark else 0.16}"><use href="#{p}-wavepath" fill="url(#{p}-wave)" transform="translate(0 {D.n(refl - 12 * WAVE_REFLECT)}) scale(1 -{WAVE_REFLECT})"/></g>'
                "</g>")

    # ── 축: 트랙 · 눈금 · 진행선 · 미래 점선 ──────────────────
    ax = []
    ax.append(f'<g class="{p}-fi" style="{D.delay(60)}">'
              f'<path d="M{X0} {ay}H{XE}" stroke="{T["border_hi"]}" stroke-width="{4 if dark else 3}" stroke-linecap="round" opacity="{0.5 if dark else 0.8}"/>')
    # 달 이름 행(축 아래)을 지나가는 것: 아래 카드 줄기(홀수 번째 노드)와 NOW. 위 카드 노드는
    # 원만 피하면 된다(줄기가 위로 간다) → 여유 폭을 다르게 준다
    obstacles = [(x, 22 if (i % 2 == 1 or i == merged) else 6) for i, x in enumerate(xs)] + [(x_now, 22)]
    for k, m in enumerate(month_marks):
        x = S.x(m)
        future = m > asof
        col = T["muted"] if not future else D.rgba(T["muted"][:7], 0.6)
        ax.append(f'<path d="M{D.n(x)} {ay - 7}V{ay + 7}" stroke="{T["muted"]}" stroke-width="1.5" stroke-linecap="round"/>')
        # 달 이름은 항상 눈금 오른쪽. 노드·NOW 와 겹치면: 연도 빼기 → 생략(머리글에 기간이 있다)
        short = MONTHS[m.month - 1]
        full = short + (f" {m.year}" if k == 0 or m.month == 1 else "")
        for lab in (full, short):
            lw = D.text_width(lab, 16, "mono", 600, letter_spacing=1.5)
            lx0, lx1 = x + 8, x + 8 + lw
            if lx0 < 30 or lx1 > W - 30:
                continue
            if any(lx0 - mg < ox < lx1 + mg for ox, mg in obstacles):
                continue
            ax.append(D.text(lx0, ay + 30, lab, 16, col, 600, "mono", ls=1.5))
            break
    ax.append("</g>")
    # 미래 점선(흐르는 대시)
    ax.append(f'<g class="{p}-fi" style="{D.delay(LINE_START + LINE_DUR)}"><path d="M{D.n(x_now)} {ay}H{X_FUTURE}" stroke="url(#{p}-future)" '
              f'stroke-width="2.5" stroke-linecap="round" stroke-dasharray="2 10" style="{D.anim(p, "k-dash", 1.6)}"/></g>')
    css.append(D.keyframes(p, "k-dash", "from{stroke-dashoffset:0}to{stroke-dashoffset:-12}"))
    # 진행선: 글로우 번짐 + 본선 + 하이라이트
    line_d = f"M{D.n(x_start)} {ay}H{D.n(x_now)}"
    draw_style = f"animation-duration:{LINE_DUR}ms;animation-timing-function:linear;{D.delay(LINE_START)}"
    ax.append(f'<g opacity="{0.9 if dark else 0.45}"><g class="{p}-glow"><path d="{line_d}" pathLength="1" stroke="url(#{p}-line)" stroke-width="12" '
              f'stroke-linecap="round" filter="url(#{p}-soft)" class="{p}-draw" style="{draw_style}"/></g></g>')
    ax.append(f'<path d="{line_d}" pathLength="1" stroke="url(#{p}-line)" stroke-width="4.5" stroke-linecap="round" class="{p}-draw" style="{draw_style}"/>')
    if dark:
        ax.append(f'<g opacity="0.55"><path d="{line_d}" pathLength="1" stroke="#FFFFFF" stroke-width="1.2" stroke-linecap="round" class="{p}-draw" style="{draw_style}"/></g>')
    # 에너지 펄스: 등장이 끝난 뒤 선을 따라 주기적으로 흐른다
    ax.append(D.motion_only(p, f'<path d="{line_d}" pathLength="1" stroke="{"#E0FAFF" if dark else "#00B4D8"}" stroke-width="4" stroke-linecap="round" '
                               f'stroke-dasharray="0.09 1.2" filter="url(#{p}-glow-line)" style="{D.anim(p, "k-energy", 6, LINE_START + LINE_DUR + 900, D.EASE_IN_OUT)}"/>'))
    css.append(D.keyframes(p, "k-energy", "0%{stroke-dashoffset:.1;opacity:0}6%{opacity:1}55%{stroke-dashoffset:-1;opacity:1}56%,100%{stroke-dashoffset:-1;opacity:0}"))
    # 빛 머리: 선 끝을 따라 달린다(축소 모드에선 NOW 비콘만 남는다)
    head_dx = x_now - x_start
    css.append(D.keyframes(p, "k-head", f"0%{{transform:translateX(-{D.n(head_dx)}px);opacity:1}}92%{{opacity:1}}100%{{transform:translateX(0);opacity:0}}"))
    ax.append(D.motion_only(p, f'<g transform="translate({D.n(x_now)} {ay})"><g style="{D.anim(p, "k-head", LINE_DUR / 1000, LINE_START, "linear", "1")}">'
                               f'<circle r="16" fill="url(#{p}-halo)"/><circle r="5" fill="{"#FFFFFF" if dark else T["accent"]}" filter="url(#{p}-glow-s)"/></g></g>'))

    # ── 마일스톤 · 카드 ────────────────────────────────────
    css.append(D.keyframes(p, "k-ripple", "0%{transform:scale(.7);opacity:0}8%{opacity:.75}70%,100%{transform:scale(2.5);opacity:0}"))
    css.append(D.keyframes(p, "k-burst", "0%{transform:scale(.5);opacity:.95}100%{transform:scale(3.2);opacity:0}"))
    nodes, cards = [], []
    for i, (d, exact, t) in enumerate(items):
        x = xs[i]
        f = D.clamp((x - x_start) / span_px, 0, 1)
        col = _color_at(T, f)
        t_hit = t_at(x)
        # 노드
        # NOW 와 합쳐진 노드는 coral 리플이 대신한다(두 색 리플이 겹치면 지저분하다)
        ripple = "" if i == merged else D.motion_only(
            p, f'<circle r="11" stroke="{col}" stroke-width="2" fill="none" '
               f'style="{D.anim(p, "k-ripple", 3.6, t_hit + 500 + (i * 700) % 3600, "ease-out")};transform-box:fill-box;transform-origin:center"/>')
        nodes.append(f'<g transform="translate({D.n(x)} {ay})">'
                     + ripple
                     + D.motion_only(p, f'<circle r="12" fill="none" stroke="{col}" stroke-width="3" opacity="0" '
                                        f'style="{D.anim(p, "k-burst", 0.9, t_hit - 40, D.EASE_OUT, "1", "forwards")};transform-box:fill-box;transform-origin:center"/>')
                     + f'<g class="{p}-pop" style="{D.delay(t_hit - 60)}">'
                     f'<circle r="20" fill="url(#{p}-halo)" class="{p}-glow" style="animation-delay:-{(i * 900) % 4000}ms"/>'
                     f'<circle r="11" fill="{T["bg"]}" stroke="{col}" stroke-width="2.5"/>'
                     f'<circle r="5.5" fill="{col}" filter="url(#{p}-glow-s)"/>'
                     "</g></g>")
        # 카드
        side, s = slot_of[i]
        w, left = s["w"], s["left"]
        tlines, tsize, tfam, slines, ssize, sfam = texts[i]
        k_side = [q["i"] for q in sides[side]].index(i)
        h = side_h[side]
        y0 = top_y1 - h if side == "top" else bot_y0
        # 줄기: 노드 → 카드(카드가 밀렸으면 꺾인다)
        sx = D.clamp(x, left + 26, left + w - 26)
        if side == "top":
            ya, yb = ay - 13, top_y1
        else:
            ya, yb = ay + 13, bot_y0
        # 같은 쪽 꺾임선이 겹치지 않게 꺾는 높이를 번갈아
        ymid = ya + (yb - ya) * (0.36 if k_side % 2 == 0 else 0.68)
        stem = f"M{D.n(x)} {ya}V{D.n(ymid)}H{D.n(sx)}V{yb}" if abs(sx - x) > 1 else f"M{D.n(x)} {ya}V{yb}"
        cards.append(f'<path d="{stem}" pathLength="1" stroke="{col}" stroke-width="1.5" stroke-linecap="round" opacity="{0.75 if dark else 0.85}" '
                     f'class="{p}-draw" style="animation-duration:420ms;{D.delay(t_hit + 80)}"/>')
        anim_cls = f"{p}-fd" if side == "top" else f"{p}-fu"
        g = [f'<g class="{anim_cls}" style="animation-duration:800ms;{D.delay(t_hit + 180)}">',
             D.glass(left, y0, w, h, theme, p, r=16)]
        # 카드 안 위쪽 색 막대 + 연결점
        g.append(f'<rect x="{D.n(left + CARD_PAD)}" y="{D.n(y0 + 1)}" width="{D.n(min(64, w - 2 * CARD_PAD))}" height="2.5" rx="1.25" fill="url(#{p}-cardbar)"/>')
        dot_y = yb
        g.append(f'<circle cx="{D.n(sx)}" cy="{D.n(dot_y)}" r="3.2" fill="{col}" filter="url(#{p}-glow-s)"/>')
        tx = left + CARD_PAD
        date_txt = D.truncate(D.fmt_date(str(t.get("date", ""))), w - 2 * CARD_PAD - 40, 16, "mono", 600)
        g.append(D.text(tx, y0 + 32, date_txt, 16, T["accent"], 600, "mono", ls=0.5))
        g.append(D.text(left + w - CARD_PAD, y0 + 32, f"{i + 1:02d}", 16, T["muted"], 600, "mono", anchor="end"))
        g.append(D.text_lines(tx, y0 + TITLE_Y, tlines, tsize, TITLE_LH, T["text"], 700, tfam))
        if slines:
            g.append(D.text_lines(tx, y0 + TITLE_Y + TITLE_LH * (len(tlines) - 1) + SUB_GAP, slines, ssize, SUB_LH, T["text2"], 400, sfam))
        g.append("</g>")
        cards.append("".join(g))

    # ── NOW 비콘 ───────────────────────────────────────────
    t_now = LINE_START + LINE_DUR
    # 빛기둥은 NOW 표지 반대쪽으로 — 그쪽에 카드가 x_now 를 덮고 있으면 카드 앞에서 멈춘다
    other = "top" if now_side == "bot" else "bot"
    blocked = any(q["i"] != "now" and q["left"] - 6 <= x_now <= q["left"] + q["w"] + 6 for q in sides[other])
    if other == "top":
        by0, by1 = ((top_y1 + 4) if blocked else 70), ay - 16
    else:
        by0, by1 = ay + 16, ((bot_y0 - 4) if blocked else H - 24)
    now = [f'<g opacity="{0.9 if dark else 0.8}" class="{p}-fi" style="{D.delay(t_now - 100)}">'
           f'<g class="{p}-breathe" style="animation-duration:5s"><rect x="{D.n(x_now - 1)}" y="{by0}" width="2" height="{by1 - by0}" fill="url(#{p}-beam)"/></g></g>']
    now.append(f'<g transform="translate({D.n(x_now)} {ay})">')
    for k in range(2):
        now.append(D.motion_only(p, f'<circle r="12" stroke="{T["coral"]}" stroke-width="2" fill="none" '
                                    f'style="{D.anim(p, "k-ripple", 3.2, t_now + 200 + k * 1600, "ease-out")};transform-box:fill-box;transform-origin:center"/>'))
    now.append(f'<g class="{p}-pop" style="{D.delay(t_now - 120)}">'
               f'<circle r="26" fill="url(#{p}-nowhalo)" class="{p}-glow" style="animation-duration:3s"/>'
               f'<circle r="12" fill="{T["bg"]}" stroke="{T["coral"]}" stroke-width="2.5"/>'
               f'<circle r="6" fill="{T["coral"]}" filter="url(#{p}-glow-s)" class="{p}-pulse" style="animation-duration:2.4s"/></g></g>')
    side, s = slot_of["now"]
    pw, pl = s["w"], s["left"]
    ph = 36
    py = (bot_y0 if side == "bot" else top_y1 - ph)
    psx = D.clamp(x_now, pl + 18, pl + pw - 18)
    ya, yb = (ay + 15, py) if side == "bot" else (ay - 15, py + ph)
    ymid = (ya + yb) / 2
    stem = f"M{D.n(x_now)} {ya}V{D.n(ymid)}H{D.n(psx)}V{D.n(yb)}" if abs(psx - x_now) > 1 else f"M{D.n(x_now)} {ya}V{D.n(yb)}"
    now.append(f'<path d="{stem}" pathLength="1" stroke="{T["coral"]}" stroke-width="1.5" stroke-linecap="round" opacity="0.8" '
               f'class="{p}-draw" style="animation-duration:380ms;{D.delay(t_now + 60)}"/>')
    pill_fill = D.rgba(T["coral"], 0.14 if dark else 0.08)
    pill_stroke = D.rgba(T["coral"], 0.55 if dark else 0.45)
    lab_col = D.mix(T["coral"], "#FFFFFF", 0.25) if dark else D.mix(T["coral"], "#000000", 0.15)
    anim_cls = f"{p}-fu" if side == "bot" else f"{p}-fd"
    now.append(f'<g class="{anim_cls}" style="animation-duration:700ms;{D.delay(t_now + 160)}">'
               f'<rect x="{D.n(pl)}" y="{D.n(py)}" width="{D.n(pw)}" height="{ph}" rx="{ph / 2}" fill="{pill_fill}" stroke="{pill_stroke}" stroke-width="1.4"/>'
               f'<g class="{p}-glow" style="animation-duration:2.4s"><circle cx="{D.n(pl + 18)}" cy="{D.n(py + ph / 2)}" r="4.5" fill="{T["coral"]}"/></g>'
               f'<text x="{D.n(pl + 31)}" y="{D.n(py + ph / 2 + 6.2)}" font-family="{D.esc(D.FONT_MONO)}" font-size="18" font-weight="700" fill="{lab_col}" letter-spacing="1.5">'
               f'{now_label}<tspan font-size="16" font-weight="500" fill="{T["text2"]}" letter-spacing="0">  {D.esc(now_date)}</tspan></text></g>')

    body = (D.card(W, H, theme, p)
            + D.defs(*dfs)
            + "".join(bg)
            + wave
            + "".join(ax)
            + "".join(cards)
            + "".join(nodes)
            + "".join(now)
            + "".join(head))
    titles = " → ".join(str(t.get("title", "")) for _, _, t in items)
    desc = f"{D.fmt_date(since.isoformat())}부터 {D.fmt_date(asof.isoformat())}까지의 여정: {titles}"
    return D.svg_root(W, H, theme, "입사 이후 여정 타임라인", desc, body, "".join(css), p)
