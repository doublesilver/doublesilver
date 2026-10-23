"""orchestra (1280×580) — 코디네이터를 중심으로 워커가 부채꼴로 둘러싸고,
작업 패킷이 코디네이터 → 워커 → 검증 → 사람 승인 → 출하 순으로 흐르는 멀티 에이전트 도식.

개념 라벨(역할 이름·모델 계열)은 아래 상수가 기본값이고, data["orchestra"] 가 있으면 그쪽이 우선한다.
data["orchestra"] 형태(전부 선택):
  {"eyebrow", "title", "subtitle", "live",
   "coordinator": {"title", "model"},
   "workers": [{"title", "model", "role", "icon"}],      # 3~5개(넘치면 앞 4개 + 마지막), 부채꼴에 고르게 배치
   "ship": {"title", "role"}, "gate": {"title", "sub"},
   "stores": [{"title", "sub", "icon"}, ...],            # 앞의 2개만 사용
   "legend": [{"model", "role"}]}                        # 없으면 등장한 모델로 자동 구성
"""

from __future__ import annotations

import math

from . import design as D

W, H = 1280, 580
P = "orchestra"

# 배치(SVG 단위)
CX, CY = 520, 380          # 코디네이터 중심 = 부채꼴 중심
RX, RY = 320, 200          # 워커가 놓이는 위쪽 반타원
GX = 1108                  # 사람 승인 · 출하 열
SY = 214                   # 출하 노드 중심 y
WK_W, WK_H = 214, 68       # 워커 노드
GATE_W, GATE_H = 232, 100
ST_W, ST_H = 224, 62
ST_Y = 526
ST_X = (250, 790)          # Ledger · Memory 중심 x
LEG = (992, 448, 232, 110) # 모델 범례 패널

MAX_WORKERS = 5
CYCLE = 12.0               # 패킷 한 바퀴(초)
START = 2.2                # 등장 애니메이션이 끝난 뒤 흐르기 시작(초)
DWELL_WORKER = 0.38
DWELL_GATE = 1.25
DWELL_START = 0.3
REST_END = 1.7

DEFAULTS = {
    "eyebrow": "MULTI-AGENT ORCHESTRATION",
    "title": "AI 에이전트 오케스트라",
    "subtitle": "나누고 · 만들고 · 검증하고 · 승인 후 출하",
    "live": "AUTONOMOUS LOOP",
    "coordinator": {"title": "Coordinator", "model": "Opus"},
    "workers": [
        {"title": "Explore", "model": "Haiku", "role": "탐색", "icon": "search"},
        {"title": "Build", "model": "Sonnet", "role": "구현", "icon": "code"},
        {"title": "Test", "model": "Sonnet", "role": "테스트", "icon": "flask"},
        {"title": "Review", "model": "Opus", "role": "리뷰", "icon": "eye"},
        {"title": "Verify", "model": "Fable", "role": "최종 검증", "icon": "shield"},
    ],
    "ship": {"title": "Ship", "role": "프로덕션 출하", "icon": "plane"},
    "gate": {"title": "Human Gate", "sub": "되돌릴 수 없는 작업은 승인 후", "icon": "lock"},
    "stores": [
        {"title": "Ledger", "sub": "발견 → 조치", "icon": "list"},
        {"title": "Memory", "sub": "세션 간 기억", "icon": "db"},
    ],
}
LEGEND_ROLE = {"haiku": "탐색 · 조사", "sonnet": "구현 · 테스트", "opus": "지휘 · 리뷰", "fable": "최종 검증"}
TIER_ORDER = ["haiku", "sonnet", "opus", "fable"]

# 24×24 상자(중심 0,0) 선 아이콘
ICONS = {
    "search": '<circle cx="-2" cy="-2" r="6.5"/><path d="M2.8 2.8L8.5 8.5"/>',
    "code": '<path d="M-4 -7L-10 0L-4 7M4 -7L10 0L4 7"/>',
    "flask": '<path d="M-4.5 -9H4.5M-2.5 -9V-2.5L-8.5 6.5Q-9.5 9 -6.5 9H6.5Q9.5 9 8.5 6.5L2.5 -2.5V-9M-5.5 3.5H5.5"/>',
    "eye": '<path d="M-10.5 0Q0 -9.5 10.5 0Q0 9.5 -10.5 0Z"/><circle r="3.2"/>',
    "shield": '<path d="M0 -10L8.5 -6.8V0Q8.5 7 0 10.5Q-8.5 7 -8.5 0V-6.8Z"/><path d="M-4 0.2L-1.2 3L4.2 -2.6"/>',
    "plane": '<path d="M-10 -0.5L10 -8.5L3.5 9.5L0.5 2.2ZM0.5 2.2L10 -8.5"/>',
    "lock": '<rect x="-7.5" y="-1.5" width="15" height="11" rx="2.5"/><path d="M0 2.5V5.5"/>',
    "list": '<rect x="-8" y="-10" width="16" height="20" rx="2.5"/><path d="M-4 -4.5H4M-4 0H4M-4 4.5H1"/>',
    "db": '<ellipse cx="0" cy="-6" rx="8.5" ry="3.2"/><path d="M-8.5 -6V6A8.5 3.2 0 0 0 8.5 6V-6M-8.5 0A8.5 3.2 0 0 0 8.5 0"/>',
    "spark": "",
}
LOCK_SHACKLE = '<path d="M-4.5 -1.5V-5A4.5 4.5 0 0 1 4.5 -5V-1.5"/>'


# ---------------------------------------------------------------------------
# 데이터 · 색
# ---------------------------------------------------------------------------


def _cfg(data):
    src = data.get("orchestra") or {}
    cfg = {}
    for k, v in DEFAULTS.items():
        sv = src.get(k)
        if isinstance(v, dict):
            cfg[k] = {**v, **(sv or {})}
        elif isinstance(v, list):
            cfg[k] = list(sv) if sv else [dict(x) for x in v]
        else:
            cfg[k] = sv if sv else v
    ws = [w for w in cfg["workers"] if isinstance(w, dict)]
    if len(ws) < 3:
        ws = [dict(x) for x in DEFAULTS["workers"]]
    if len(ws) > MAX_WORKERS:
        # 부채꼴에 겹치지 않고 들어가는 건 5개까지 — 마지막(검증) 단계는 남긴다
        ws = ws[:MAX_WORKERS - 1] + [ws[-1]]
    cfg["workers"] = ws
    st = (cfg["stores"] + [dict(x) for x in DEFAULTS["stores"]])[:2]
    cfg["stores"] = st
    cfg["legend_src"] = src.get("legend")
    return cfg


def _tier(model):
    m = str(model or "").lower()
    for t in TIER_ORDER:
        if t in m:
            return t
    return ""


def _mcol(T, model):
    t = _tier(model)
    dark = T["dark"]
    if t == "haiku":
        return "#48CAE4" if dark else "#0284C7"
    if t == "sonnet":
        return T["accent2"]
    if t == "opus":
        return T["accent3"]
    if t == "fable":
        return D.mix("#A78BFA", "#FF6F61", 0.5) if dark else D.mix("#7C3AED", "#E8574B", 0.42)
    return T["accent"]


def _icon(name, color, sw=1.7, scale=1.0, extra=""):
    body = ICONS.get(name) or ICONS["code"]
    tr = f' transform="scale({D.n(scale)})"' if scale != 1 else ""
    return (f'<g{tr} fill="none" stroke="{color}" stroke-width="{D.n(sw)}" stroke-linecap="round" '
            f'stroke-linejoin="round">{body}{extra}</g>')


# ---------------------------------------------------------------------------
# 기하 · 패킷 일정
# ---------------------------------------------------------------------------


def _ell(phi):
    return CX + RX * math.cos(phi), CY - RY * math.sin(phi)


def _arc_len(a, b, steps=480):
    tot, px, py = 0.0, *_ell(a)
    for i in range(1, steps + 1):
        x, y = _ell(a + (b - a) * i / steps)
        tot += math.hypot(x - px, y - py)
        px, py = x, y
    return tot


def _layout(nw):
    phis = [math.pi - i * math.pi / (nw - 1) for i in range(nw)]
    pts = [_ell(p) for p in phis]
    return phis, pts


def _schedule(phis):
    """패킷이 지나는 정류장(코디네이터·워커들·게이트·출하)의 경로 비율과 도착 시각."""
    dists = [0.0, float(RX)]
    for i in range(1, len(phis)):
        dists.append(dists[-1] + _arc_len(phis[i - 1], phis[i]))
    dists.append(dists[-1] + (GX - (CX + RX)))
    dists.append(dists[-1] + (CY - SY))
    L = dists[-1]
    dwells = [DWELL_WORKER] * len(phis) + [DWELL_GATE]
    move_time = CYCLE - DWELL_START - sum(dwells) - REST_END
    v = L / move_time
    kt, kp, spl, arr = [0.0, DWELL_START], [0.0, 0.0], ["0 0 1 1"], [0.0]
    t = DWELL_START
    for k in range(1, len(dists)):
        t += (dists[k] - dists[k - 1]) / v
        kt.append(t); kp.append(dists[k] / L); spl.append(".45 0 .55 1"); arr.append(t)
        if k < len(dists) - 1:
            t += dwells[k - 1]
            kt.append(t); kp.append(dists[k] / L); spl.append("0 0 1 1")
    kt.append(CYCLE); kp.append(1.0); spl.append("0 0 1 1")
    return {"kt": [x / CYCLE for x in kt], "kp": kp, "spl": spl, "arr": arr, "L": L,
            "dwells": [DWELL_START] + dwells + [REST_END]}


def _route_d(pts):
    (x0, y0), (xn, yn) = pts[0], pts[-1]
    return (f"M{CX} {CY}L{D.n(x0)} {D.n(y0)}A{RX} {RY} 0 0 1 {D.n(xn)} {D.n(yn)}"
            f"L{GX} {CY}L{GX} {SY}")


def _pct(t):
    return D.clamp(t / CYCLE * 100, 0, 100)


def _flash_kf(name, t_arr, hold=0.0, peak=1.0, tail=0.9):
    """도착 시각 t_arr 에 켜졌다가(hold 동안 유지) 서서히 꺼지는 루프 keyframes(사이클 기준)."""
    a = _pct(t_arr)
    pre = max(a - 1.6, 0.01)
    h = min(_pct(t_arr + hold), 99.0)
    off = min(_pct(t_arr + hold + tail), 99.9)
    return D.keyframes(P, name, f"0%,{pre:.2f}%{{opacity:0}}{a:.2f}%,{h:.2f}%{{opacity:{peak}}}"
                                 f"{off:.2f}%,100%{{opacity:0}}")


def _sync(name, delay_s=START):
    return D.anim(P, name, CYCLE, int(delay_s * 1000), "linear")


# ---------------------------------------------------------------------------
# 그리기
# ---------------------------------------------------------------------------


def _background(T, theme):
    p = P
    dark = T["dark"]
    blobs = [(CX, CY - 20, 360, "#7C3AED", 0.75 if dark else 0.45, 0),
             (1160, 120, 320, "#00B4D8", 0.7, -4000),
             (110, 560, 340, "#14B8A6", 0.6, -8000),
             (1120, 560, 260, "#0077B6", 0.7, -2000)]
    dfs, out = [], []
    for i, (cx, cy, r, c, k, dl) in enumerate(blobs):
        gid = f"{p}-blob{i}"
        dfs.append(D.radial_gradient(gid, [(0, c, T["blob_opacity"] * k), (0.55, c, T["blob_opacity"] * k * 0.3), (1, c, 0)]))
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})" class="{p}-floats" style="animation-delay:{dl}ms"/>')
    dfs.append(D.dot_grid_pattern(f"{p}-dots", theme, gap=26, r=1.1))
    dfs.append(D.radial_gradient(f"{p}-dotsfade-g", [(0, "#fff", 0.9), (0.55, "#fff", 0.3), (1, "#fff", 0)],
                                 cx=CX, cy=CY - 60, r=640, units="userSpaceOnUse"))
    dfs.append(f'<mask id="{p}-dotsfade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
               f'<rect width="{W}" height="{H}" fill="url(#{p}-dotsfade-g)"/></mask>')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#{p}-dots)" mask="url(#{p}-dotsfade)"/>')
    # 궤도 가이드: 바깥 큰 타원 두 겹(점선이 천천히 흐른다)
    op = 0.5 if dark else 0.6
    for i, (rx, ry, dash, dur, rev) in enumerate([(RX + 120, RY + 80, "2 10", 30, False), (RX - 120, RY - 70, "1.5 8", 22, True)]):
        out.append(f'<g opacity="{op * (0.55 if i == 0 else 0.7)}"><ellipse cx="{CX}" cy="{CY}" rx="{rx}" ry="{ry}" stroke="{T["line"]}" '
                   f'stroke-width="1" stroke-dasharray="{dash}" style="{D.anim(p, "k-dash-r" if rev else "k-dash", dur)}"/></g>')
    css = (D.keyframes(p, "k-dash", "to{stroke-dashoffset:-240}")
           + D.keyframes(p, "k-dash-r", "to{stroke-dashoffset:240}"))
    stars = D.constellation(p, theme, (24, 24, W - 48, H - 48), count=26, seed=29, link_dist=150,
                            dim_box=(80, 130, 1160, 440), dim=0.35)
    out.append(f'<g class="{p}-fi" style="animation-duration:2.4s"><g opacity="{0.75 if dark else 0.6}">{stars}</g></g>')
    return "".join(dfs), "".join(out), css


def _edges(T, phis, pts, cols, gate_col, sched):
    p = P
    dark = T["dark"]
    c1, c2, c3 = T["grad"]
    dfs = [
        D.linear_gradient(f"{p}-arc", [(0, cols[0], 0.95), (0.5, c2, 0.95), (1, cols[-1], 0.95)],
                          CX - RX, 0, CX + RX, 0, units="userSpaceOnUse"),
        D.linear_gradient(f"{p}-out", [(0, cols[-1], 0.9), (1, gate_col, 0.9)], CX + RX, 0, GX, 0, units="userSpaceOnUse"),
        D.linear_gradient(f"{p}-up", [(0, gate_col, 0.9), (1, T["accent2"], 0.95)], 0, CY, 0, SY, units="userSpaceOnUse"),
        D.glow_filter(f"{p}-glow-s", 3, 1.0 if dark else 0.45),
        D.glow_filter(f"{p}-glow", 6, 0.9 if dark else 0.4),
    ]
    out, css = [], []
    (x0, y0), (xn, yn) = pts[0], pts[-1]
    arc_d = f"M{D.n(x0)} {D.n(y0)}A{RX} {RY} 0 0 1 {D.n(xn)} {D.n(yn)}"
    out_d = f"M{D.n(xn)} {CY}L{GX} {CY}"
    up_d = f"M{GX} {CY}L{GX} {SY}"
    # 1) 스포크 — 코디네이터에서 각 워커로(흐르는 점선)
    sp = []
    for i, (x, y) in enumerate(pts):
        sp.append(f'<path d="M{CX} {CY}L{D.n(x)} {D.n(y)}" stroke="{D.rgba(cols[i], 0.55 if dark else 0.5)}" stroke-width="1.3" '
                  f'stroke-dasharray="3 7" style="{D.anim(p, "k-spoke", 2.2, -i * 300)}"/>')
    css.append(D.keyframes(p, "k-spoke", "to{stroke-dashoffset:-20}"))
    out.append(f'<g class="{p}-fi" style="{D.delay(650)};animation-duration:1.4s"><g opacity="{0.8 if dark else 0.75}">{"".join(sp)}</g></g>')
    # 2) 주 경로 — 넓은 번짐 + 본선(그리기 등장) + 흐르는 빛 점선
    for d, gid, dl in ((arc_d, "arc", 500), (out_d, "out", 1500), (up_d, "up", 1750)):
        out.append(f'<g opacity="{0.35 if dark else 0.18}"><path d="{d}" stroke="url(#{p}-{gid})" stroke-width="9" '
                   f'stroke-linecap="round" filter="url(#{p}-glow)" class="{p}-fi" style="{D.delay(dl + 300)}"/></g>')
        out.append(f'<path d="{d}" pathLength="1" stroke="url(#{p}-{gid})" stroke-width="2.2" stroke-linecap="round" '
                   f'class="{p}-draw" style="{D.delay(dl)};animation-duration:{"1.6s" if gid == "arc" else "0.7s"}"/>')
        out.append(f'<g class="{p}-fi" style="{D.delay(dl + 900)}"><path d="{d}" stroke="{T["shine"] if dark else T["accent"]}" '
                   f'stroke-opacity="{0.75 if dark else 0.55}" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="1 15" '
                   f'style="{D.anim(p, "k-conv", 1.8)}"/></g>')
    css.append(D.keyframes(p, "k-conv", "to{stroke-dashoffset:-32}"))
    # 3) 진행 방향 셰브론(정적 — 축소 모드에서도 흐름 방향이 읽힌다)
    chev = []
    for i in range(len(phis) - 1):
        m = (phis[i] + phis[i + 1]) / 2
        x, y = _ell(m)
        dx, dy = RX * math.sin(m), RY * math.cos(m)   # d/dphi 의 반대(phi 가 줄어드는 방향)
        ang = math.degrees(math.atan2(dy, dx))
        chev.append((x, y, ang, cols[i + 1]))
    chev.append(((CX + RX + WK_W / 2 + GX - GATE_W / 2) / 2, CY, 0, gate_col))
    chev.append((GX, (CY - GATE_H / 2 + SY + WK_H / 2) / 2, -90, T["accent2"]))
    for x, y, ang, col in chev:
        out.append(f'<g transform="translate({D.n(x)},{D.n(y)}) rotate({D.n(ang, 1)})"><g class="{p}-fi" style="{D.delay(1900)}">'
                   f'<circle r="9" fill="{T["bg"]}" stroke="{D.rgba(col, 0.55)}" stroke-width="1.2"/>'
                   f'<path d="M-2.2 -3.6L2 0L-2.2 3.6" stroke="{col}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></g></g>')
    # 4) 저장소 링크(Ledger·Memory ↔ 코디네이터)
    store_paths = []
    for k, sx in enumerate(ST_X):
        side = -1 if sx < CX else 1
        ax, ay = sx + side * -(ST_W / 2 - 46), ST_Y - ST_H / 2
        bx, by = CX + side * 46, CY + 28
        d = f"M{D.n(ax)} {D.n(ay)}C{D.n(ax)} {D.n(ay - 70)} {D.n(bx + side * 70)} {D.n(by + 30)} {D.n(bx)} {D.n(by)}"
        store_paths.append(d)
        out.append(f'<g class="{p}-fi" style="{D.delay(1500)}"><path d="{d}" stroke="{D.rgba(T["accent3"], 0.6 if dark else 0.5)}" '
                   f'stroke-width="1.4" stroke-dasharray="4 6" style="{D.anim(p, "k-spoke", 2.6, k * -900)}"/></g>')
    return "".join(dfs), "".join(out), "".join(css), store_paths


def _packets(T, pts, cols, gate_col, sched, store_paths, route_d):
    """SMIL 패킷(축소 모드에서 숨김) + 지나간 자리를 밝히는 트레이스."""
    p = P
    dark = T["dark"]
    kt = ";".join(f"{x:.4f}" for x in sched["kt"])
    kp = ";".join(f"{x:.4f}" for x in sched["kp"])
    ks = ";".join(sched["spl"])
    begin = f"{START}s"
    # 정류장별 색: 출발(코디네이터) → 워커들 → 게이트 → 출하
    stops_col = [T["accent3"]] + cols + [gate_col, T["accent2"]]
    seq = [stops_col[0], stops_col[0]]
    for k in range(1, len(stops_col)):
        seq.append(stops_col[k])
        if k < len(stops_col) - 1:
            seq.append(stops_col[k])
    seq.append(stops_col[-1])
    fills = ";".join(seq)
    o = []
    # 트레이스 — 패킷과 같은 일정으로 경로가 차오르고, 출하 후 사라진다
    tr = []
    for t_, p_, s_ in zip(sched["kt"], sched["kp"], sched["spl"] + ["0 0 1 1"]):
        tr.append(f"{t_ * 100:.3f}%{{stroke-dashoffset:{1 - p_:.4f};animation-timing-function:cubic-bezier({s_.replace(' ', ',')})}}")
    arr_ship = _pct(sched["arr"][-1])
    css = D.keyframes(p, "k-trace", "".join(tr))
    css += D.keyframes(p, "k-trace-o", f"0%,{arr_ship + 4:.2f}%{{opacity:1}}{min(arr_ship + 11, 99.5):.2f}%,100%{{opacity:0}}")
    o.append(f'<g opacity="{0.9 if dark else 0.8}"><g style="{_sync("k-trace-o")}"><path d="{route_d}" pathLength="1" stroke="url(#{p}-trace)" '
             f'stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="1 2" stroke-dashoffset="1" '
             f'filter="url(#{p}-glow-s)" style="{_sync("k-trace")}"/></g></g>')
    # 디스패치 — 코디네이터가 다른 워커들에게도 일감을 흘려보낸다
    for i, (x, y) in enumerate(pts[1:], 1):
        d = f"M{CX} {CY}L{D.n(x)} {D.n(y)}"
        b = f"{0.6 + i * 0.55:.2f}s"
        o.append(f'<circle r="2.6" fill="{cols[i]}" opacity="0" filter="url(#{p}-glow-s)">'
                 f'<animateMotion path="{d}" dur="3.2s" begin="{b}" repeatCount="indefinite" calcMode="spline" keyTimes="0;1" keySplines=".5 0 .3 1"/>'
                 f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.15;.8;1" dur="3.2s" begin="{b}" repeatCount="indefinite"/></circle>')
    # 저장소 왕복 — 기록하러 가고(→Ledger/Memory) 꺼내 온다(→코디네이터)
    for k, d in enumerate(store_paths):
        for j, (kpts, col) in enumerate((("0;1", T["accent3"]), ("1;0", T["accent"]))):
            b = f"{1.2 + k * 0.9 + j * 2.1:.2f}s"
            o.append(f'<circle r="2.8" fill="{col}" opacity="0" filter="url(#{p}-glow-s)">'
                     f'<animateMotion path="{d}" dur="4.2s" begin="{b}" repeatCount="indefinite" keyPoints="{kpts}" keyTimes="0;1" calcMode="spline" keySplines=".45 0 .55 1"/>'
                     f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.12;.85;1" dur="4.2s" begin="{b}" repeatCount="indefinite"/></circle>')
    # 주 패킷 — 혜성 꼬리 3개 + 코어(색이 정류장마다 바뀐다)
    mot = (f'path="{route_d}" dur="{CYCLE}s" repeatCount="indefinite" calcMode="spline" '
           f'keyTimes="{kt}" keyPoints="{kp}" keySplines="{ks}"')
    # 시작 전에는 원점(0,0)에 머무니 숨겨 둔다
    o.append(f'<g visibility="hidden"><set attributeName="visibility" to="visible" begin="{begin}"/>')
    for j, (r, a) in enumerate([(2.0, 0.22), (2.8, 0.34), (3.6, 0.5), (4.6, 0.7)]):
        lag = (4 - j) * 0.06
        o.append(f'<circle r="{r}" fill="{T["particle"]}" opacity="{a}"><animateMotion {mot} begin="{START + lag:.2f}s"/></circle>')
    o.append(f'<circle r="22" fill="url(#{p}-halo)"><animateMotion {mot} begin="{begin}"/></circle>')
    o.append(f'<circle r="7" fill="{stops_col[0]}" filter="url(#{p}-glow-s)"><animateMotion {mot} begin="{begin}"/>'
             f'<animate attributeName="fill" values="{fills}" keyTimes="{kt}" dur="{CYCLE}s" begin="{begin}" repeatCount="indefinite"/></circle>')
    o.append(f'<circle r="3" fill="#FFFFFF"><animateMotion {mot} begin="{begin}"/></circle></g>')
    dfs = (D.linear_gradient(f"{p}-trace", [(0, T["accent3"], 0.9), (0.2, cols[0], 1), (0.55, T["accent"], 1), (0.8, cols[-1], 1), (1, T["accent2"], 1)],
                             0, 0, 1, 0)
           + D.radial_gradient(f"{p}-halo", [(0, T["particle"], 0.7 if dark else 0.4), (0.4, T["accent"], 0.25 if dark else 0.15), (1, T["accent"], 0)]))
    return dfs, D.motion_only(p, "".join(o)), css


def _coordinator(T, cfg, sched):
    p = P
    dark = T["dark"]
    dfs = [
        D.radial_gradient(f"{p}-c-halo", [(0, "#7C3AED", 0.45 if dark else 0.22), (0.5, "#00B4D8", 0.16 if dark else 0.08), (1, "#00B4D8", 0)]),
        D.radial_gradient(f"{p}-c-core", [(0, "#FFFFFF", 1), (0.25, "#E4DAFF", 1), (0.62, "#8B5CF6", 1), (1, "#0077B6", 1)], fx=0.36, fy=0.32),
        D.linear_gradient(f"{p}-c-ring", [(0, "#00B4D8", 0.95), (0.5, "#7C3AED", 0.85), (1, "#2DD4BF", 0.95)], 0, 0, 1, 1),
    ]
    css = D.keyframes(p, "k-ripple", "0%{transform:scale(.75);opacity:.7}100%{transform:scale(2.3);opacity:0}")
    # 출발 순간 한 번 크게 퍼지는 디스패치 파동
    css += D.keyframes(p, "k-dispatch", f"0%{{transform:scale(.8);opacity:.9}}{_pct(1.1):.2f}%{{transform:scale(2.6);opacity:0}}100%{{transform:scale(2.6);opacity:0}}")
    o = [f'<g transform="translate({CX},{CY})">']
    o.append(f'<circle r="150" fill="url(#{p}-c-halo)" class="{p}-breathe"/>')
    rip = "".join(f'<circle r="56" stroke="{T["accent3"] if i % 2 == 0 else T["accent"]}" stroke-width="1.4" '
                  f'style="{D.anim(p, "k-ripple", 6, -i * 2000, D.EASE_OUT)};transform-box:fill-box;transform-origin:center"/>'
                  for i in range(3))
    o.append(D.motion_only(p, f'<g opacity="{0.8 if dark else 0.6}">{rip}</g>'))
    o.append(D.motion_only(p, f'<circle r="56" stroke="{T["accent"]}" stroke-width="2" opacity="0" '
                              f'style="{_sync("k-dispatch", START)};transform-box:fill-box;transform-origin:center"/>'))
    o.append(f'<g class="{p}-pop" style="{D.delay(200)}">')
    o.append(f'<g class="{p}-spin" style="animation-duration:40s"><circle r="88" stroke="url(#{p}-c-ring)" stroke-width="1.2" '
             f'stroke-dasharray="2 8" opacity="{0.8 if dark else 0.9}"/>'
             f'<circle cx="88" cy="0" r="3.6" fill="{T["accent2"]}" filter="url(#{p}-glow-s)"/>'
             f'<circle cx="-88" cy="0" r="2.4" fill="{T["accent"]}"/></g>')
    o.append(f'<g class="{p}-spinr" style="animation-duration:24s"><circle r="70" stroke="url(#{p}-c-ring)" stroke-width="1.6" '
             f'stroke-dasharray="60 18 6 18" stroke-linecap="round" opacity="0.85"/>'
             f'<circle cx="0" cy="-70" r="3" fill="{T["accent3"]}" filter="url(#{p}-glow-s)"/></g>')
    o.append(f'<g class="{p}-pulse"><circle r="46" fill="url(#{p}-c-core)" filter="url(#{p}-glow)"/>'
             f'<circle r="46" stroke="#FFFFFF" stroke-opacity="0.35" stroke-width="1"/>'
             f'<path d="{D.sparkle_path(0, 0, 20, 0.2)}" fill="#FFFFFF" opacity="0.96"/>'
             f'<path d="{D.sparkle_path(15, -15, 6, 0.24)}" fill="#FFFFFF" opacity="0.8" class="{p}-tw"/></g>')
    o.append("</g></g>")
    # 라벨 알약 — "Coordinator · Opus"
    c = cfg["coordinator"]
    title, model = str(c.get("title", "")), str(c.get("model", ""))
    mcol = _mcol(T, model)
    size = 20
    def lw(sz):
        return (D.text_width(title, sz, D.family_of(title), 700)
                + (D.text_width(" · " + model, sz * 0.9, "latin", 600) if model else 0))
    while size > 16 and lw(size) > 300:
        size -= 0.5
    tw = min(lw(size), 300)
    pw, ph = tw + 44, 40
    py = CY + 72
    o.append(f'<g class="{p}-fu" style="{D.delay(800)}">'
             f'<rect x="{D.n(CX - pw / 2)}" y="{py}" width="{D.n(pw)}" height="{ph}" rx="20" fill="{T["bg"]}" opacity="0.95"/>'
             f'<rect x="{D.n(CX - pw / 2)}" y="{py}" width="{D.n(pw)}" height="{ph}" rx="20" fill="url(#{p}-glass-fill)" '
             f'stroke="{D.rgba(mcol, 0.55)}" stroke-width="1.4" filter="url(#{p}-glass-shadow)"/>'
             f'<text x="{CX}" y="{D.n(py + ph / 2 + size * 0.36)}" text-anchor="middle" font-size="{D.n(size)}" font-weight="700" '
             f'fill="{T["text"]}" font-family="{D.esc(D.FONTS[D.family_of(title)])}">{D.esc(D.truncate(title, 300, size, D.family_of(title), 700))}'
             + (f'<tspan fill="{T["muted"]}" font-weight="400"> · </tspan><tspan fill="{mcol}" font-weight="650" font-size="{D.n(size * 0.9)}" '
                f'font-family="{D.esc(D.FONT_LATIN)}">{D.esc(model)}</tspan>' if model else "")
             + "</text></g>")
    return "".join(dfs), "".join(o), css


def _node_box(x, y, w, h, T, col, cls_style, inner, flash_kf=None, r=20):
    """글래스 노드 + 색 테두리 + (선택) 패킷 도착 섬광."""
    p = P
    dark = T["dark"]
    flash = ""
    if flash_kf:
        flash = D.motion_only(p, f'<rect x="{D.n(x)}" y="{D.n(y)}" width="{D.n(w)}" height="{D.n(h)}" rx="{r}" '
                                 f'fill="{D.rgba(col, 0.16 if dark else 0.08)}" stroke="{col}" stroke-width="2.2" opacity="0" '
                                 f'filter="url(#{p}-glow-s)" style="{_sync(flash_kf)}"/>')
    # 불투명 바탕 — 뒤를 지나는 간선이 글래스 너머로 비쳐 글자를 가리지 않게
    return (f'<g class="{p}-pop" style="{cls_style}">'
            + f'<rect x="{D.n(x)}" y="{D.n(y)}" width="{D.n(w)}" height="{D.n(h)}" rx="{r}" fill="{T["bg"]}" opacity="0.95"/>'
            + D.glass(x, y, w, h, T["theme"], p, r=r)
            + f'<rect x="{D.n(x)}" y="{D.n(y)}" width="{D.n(w)}" height="{D.n(h)}" rx="{r}" stroke="{D.rgba(col, 0.42 if dark else 0.38)}" stroke-width="1.2"/>'
            + flash + inner + "</g>")


def _badge(cx, cy, T, col, icon, r=19, extra=""):
    dark = T["dark"]
    return (f'<g transform="translate({D.n(cx)},{D.n(cy)})">'
            f'<circle r="{r}" fill="{D.rgba(col, 0.15 if dark else 0.10)}" stroke="{D.rgba(col, 0.6)}" stroke-width="1.2"/>'
            + _icon(icon, col, 1.7, 0.78, extra) + "</g>")


def _two_line(x, y1, y2, title, model, mcol, role, T, max_w, title_size=21):
    """제목 줄 + (모델 · 역할) 줄. 길이가 바뀌어도 max_w 안에 들어가게 축소·말줄임."""
    fam_t = D.family_of(title)
    ts = D.fit_size(title, max_w, title_size, 16, fam_t, 700)
    title = D.truncate(title, max_w, ts, fam_t, 700)
    out = D.text(x, y1, title, ts, T["text"], 700, fam_t)
    ms, rs = 16.5, 16
    model, role = str(model or ""), str(role or "")
    sep = " · " if model and role else ""
    mw = D.text_width(model, ms, "latin", 600) if model else 0
    sw = D.text_width(sep, rs, "latin")
    rem = max_w - mw - sw
    fam_r = D.family_of(role)
    if role and D.text_width(role, rs, fam_r, 500) > rem:
        role = D.truncate(role, rem, rs, fam_r, 500) if rem > rs * 2.2 else ""
        sep = sep if role else ""
    if model and mw > max_w:
        model = D.truncate(model, max_w, ms, "latin", 600)
    spans = ""
    if model:
        spans += f'<tspan fill="{mcol}" font-weight="650" font-size="{ms}" font-family="{D.esc(D.FONT_LATIN)}">{D.esc(model)}</tspan>'
    if sep:
        spans += f'<tspan fill="{T["muted"]}" font-family="{D.esc(D.FONT_LATIN)}">{sep}</tspan>'
    if role:
        spans += f'<tspan fill="{T["text2"]}" font-weight="500" font-family="{D.esc(D.FONTS[fam_r])}">{D.esc(role)}</tspan>'
    out += f'<text x="{D.n(x)}" y="{D.n(y2)}" font-size="{rs}">{spans}</text>'
    return out


def _nodes(T, cfg, pts, cols, gate_col, sched):
    p = P
    dark = T["dark"]
    out, css = [], []
    arr = sched["arr"]  # [코디네이터 출발, 워커..., 게이트, 출하]
    # 워커
    for i, (w, (x, y)) in enumerate(zip(cfg["workers"], pts)):
        kf = f"k-f{i}"
        css.append(_flash_kf(kf, arr[i + 1], DWELL_WORKER, 1, 0.9))
        nx, ny = x - WK_W / 2, y - WK_H / 2
        inner = (_badge(nx + 34, y, T, cols[i], w.get("icon") or "code")
                 + _two_line(nx + 62, y - 4, y + 20, str(w.get("title", "")), w.get("model", ""), cols[i], w.get("role", ""),
                             T, WK_W - 62 - 14))
        out.append(_node_box(nx, ny, WK_W, WK_H, T, cols[i], D.delay(700 + i * 110), inner, kf))
    # 사람 승인 게이트
    g = cfg["gate"]
    gx, gy = GX - GATE_W / 2, CY - GATE_H / 2
    css.append(_flash_kf("k-fg", arr[-2], DWELL_GATE, 1, 0.8))
    t_ok = arr[-2] + DWELL_GATE * 0.45
    css.append(D.keyframes(p, "k-ok", f"0%,{_pct(t_ok) - 0.6:.2f}%{{opacity:0;transform:scale(.4)}}{_pct(t_ok + 0.18):.2f}%{{opacity:1;transform:scale(1.15)}}"
                                      f"{_pct(t_ok + 0.32):.2f}%,{_pct(arr[-2] + DWELL_GATE + 0.5):.2f}%{{opacity:1;transform:scale(1)}}"
                                      f"{_pct(arr[-2] + DWELL_GATE + 1.0):.2f}%,100%{{opacity:0;transform:scale(1)}}"))
    css.append(D.keyframes(p, "k-shackle", f"0%,{_pct(t_ok) - 0.6:.2f}%{{transform:translateY(0)}}{_pct(t_ok + 0.2):.2f}%,{_pct(arr[-2] + DWELL_GATE + 0.3):.2f}%{{transform:translateY(-3.5px)}}"
                                           f"{_pct(arr[-2] + DWELL_GATE + 0.8):.2f}%,100%{{transform:translateY(0)}}"))
    shackle = (f'<g style="{_sync("k-shackle")}">{LOCK_SHACKLE}</g>')
    sub = str(g.get("sub", ""))
    max_w = GATE_W - 62 - 16
    ss, lines = D.fit_block(sub, max_w, 16.5, 16, 2, D.family_of(sub), 500)
    gtitle = str(g.get("title", ""))
    gts = D.fit_size(gtitle, max_w, 21, 16, D.family_of(gtitle), 700)
    ty = gy + (32 if len(lines) > 1 else 42)
    badge_ok = D.motion_only(p, f'<g transform="translate({D.n(gx + GATE_W - 18)},{D.n(gy + 18)})"><g opacity="0" style="{_sync("k-ok")};transform-box:fill-box;transform-origin:center">'
                               f'<circle r="11" fill="{T["accent2"]}" filter="url(#{p}-glow-s)"/>'
                               f'<path d="M-4.5 0.3L-1.4 3.4L4.6 -3" stroke="{T["bg"]}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></g></g>')
    inner = (f'<g transform="translate({D.n(gx + 34)},{D.n(CY)})">'
             f'<circle r="20" fill="{D.rgba(gate_col, 0.15 if dark else 0.10)}" stroke="{D.rgba(gate_col, 0.6)}" stroke-width="1.2"/>'
             f'<circle r="20" stroke="{gate_col}" stroke-width="1.4" class="{p}-glow" style="animation-duration:3s"/>'
             + _icon("lock", gate_col, 1.7, 0.78, shackle) + "</g>"
             + D.text(gx + 62, ty, D.truncate(gtitle, max_w, gts, D.family_of(gtitle), 700), gts, T["text"], 700)
             + D.text_lines(gx + 62, ty + 25, lines, ss, 21, T["text2"], 500)
             + badge_ok)
    out.append(_node_box(gx, gy, GATE_W, GATE_H, T, gate_col, D.delay(1250), inner, "k-fg"))
    # 출하
    s = cfg["ship"]
    sx, sy = GX - WK_W / 2, SY - WK_H / 2
    css.append(_flash_kf("k-fs", arr[-1], 0.5, 1, 1.2))
    css.append(D.keyframes(p, "k-burst", f"0%,{_pct(arr[-1]) - 0.2:.2f}%{{transform:scale(1);opacity:0}}{_pct(arr[-1]):.2f}%{{transform:scale(1);opacity:.95}}"
                                         f"{_pct(arr[-1] + 1.1):.2f}%,100%{{transform:scale(1.17,1.6);opacity:0}}"))
    # 버스트 링은 노드 박스 윤곽에서 바깥으로 퍼지고, 박스보다 먼저 그려 불투명 바탕 뒤에 둔다 — 글자를 덮지 않게
    burst = D.motion_only(p, "".join(
        f'<rect x="{D.n(sx)}" y="{D.n(sy)}" width="{WK_W}" height="{WK_H}" rx="20" stroke="{T["accent2"] if j == 0 else T["accent"]}" '
        f'stroke-width="{2 - j * 0.6}" vector-effect="non-scaling-stroke" opacity="0" '
        f'style="{_sync("k-burst", START + j * 0.18)};transform-box:fill-box;transform-origin:center"/>' for j in range(2)))
    out.append(burst)
    inner = (_badge(sx + 34, SY, T, T["accent2"], s.get("icon") or "plane")
             + _two_line(sx + 62, SY - 4, SY + 20, str(s.get("title", "")), "", T["accent2"], s.get("role", ""), T, WK_W - 62 - 14))
    out.append(_node_box(sx, sy, WK_W, WK_H, T, T["accent2"], D.delay(1350), inner, "k-fs"))
    # 저장소 Ledger · Memory
    for k, (st, cx) in enumerate(zip(cfg["stores"], ST_X)):
        col = T["accent3"]
        x0, y0 = cx - ST_W / 2, ST_Y - ST_H / 2
        title, sub = str(st.get("title", "")), str(st.get("sub", ""))
        mw = ST_W - 60 - 14
        ts = D.fit_size(title, mw, 20, 16, D.family_of(title), 700)
        fam_s = D.family_of(sub)
        sz = D.fit_size(sub, mw, 16.5, 16, fam_s, 500)
        inner = (_badge(x0 + 32, ST_Y, T, col, st.get("icon") or DEFAULTS["stores"][k]["icon"], r=18)
                 + D.text(x0 + 60, ST_Y - 4, D.truncate(title, mw, ts, D.family_of(title), 700), ts, T["text"], 700)
                 + D.text(x0 + 60, ST_Y + 19, D.truncate(sub, mw, sz, fam_s, 500), sz, T["text2"], 500, fam_s))
        out.append(_node_box(x0, y0, ST_W, ST_H, T, col, D.delay(1400 + k * 90), inner, None, r=18))
    return "".join(out), "".join(css)


def _header(T, cfg):
    p = P
    dark = T["dark"]
    out, dfs = [], []
    # 아이브로우
    eb = str(cfg["eyebrow"])
    out.append(D.eyebrow(p, 72, 34, eb, T["theme"], "violet", "sparkle", max_w=560)[0])
    # 라이브 칩(오른쪽)
    out.append(D.eyebrow(p, W - 56, 34, str(cfg["live"]), T["theme"], "teal", "dot", max_w=360, anchor="end",
                         delay_ms=160)[0])
    # 제목 + 부제(같은 줄, 투명 제목 tspan 뒤에 이어 붙여 실제 폭을 따라간다)
    title, sub = str(cfg["title"]), str(cfg["subtitle"])
    max_w = W - 56 - 72
    fam_t = D.family_of(title)
    ts = D.fit_size(title, max_w * 0.62, 44, 30, fam_t, 800)
    title = D.truncate(title, max_w * 0.62, ts, fam_t, 800)
    tw = D.text_width(title, ts, fam_t, 800)
    rem = max_w - tw - 44
    fam_s = D.family_of(sub)
    ss = D.fit_size(sub, rem, 19, 16, fam_s, 500)
    sub = D.truncate(sub, rem, ss, fam_s, 500) if rem > 80 else ""
    ty = 112
    # 흐르는 그라디언트 글자 + 가끔 스치는 빛띠(글자 모양 clipPath 안)
    per = 460
    title_txt = D.text(72, ty, title, ts, None, 800, fam_t, ls=-0.5)
    dfs.append(D.flow_gradient(f"{p}-title-flow", T["grad_text"] + [T["accent3"]], per))
    dfs.append(f'<clipPath id="{p}-title-clip">{title_txt}</clipPath>')
    dfs.append(D.linear_gradient(f"{p}-shine", [(0, T["shine"], 0), (0.5, T["shine"], T["shine_opacity"]), (1, T["shine"], 0)]))
    css = D.flow_css(p, per) + D.shimmer_css(p, "k-shine", 72 - 170, 72 + tw + 80, 0.3)
    glow = ""
    if dark:
        dfs.append(D.blur_filter(f"{p}-title-blur", 12))
        glow = (f'<g opacity="0.45" class="{p}-glow" filter="url(#{p}-title-blur)">'
                + D.text(72, ty, title, ts, T["accent3"], 800, fam_t, ls=-0.5) + "</g>")
    out.append(f'<g class="{p}-fu" style="{D.delay(180)}">{glow}<g clip-path="url(#{p}-title-clip)">'
               + D.flow_rect(p, 62, ty - ts, tw + 30, ts * 1.35, f"{p}-title-flow", per, dur=8)
               + f'<g style="{D.anim(p, "k-shine", 7, 2400, D.EASE_IN_OUT)}"><rect x="0" y="{D.n(ty - ts)}" width="120" '
                 f'height="{D.n(ts * 1.35)}" fill="url(#{p}-shine)" transform="skewX(-18)"/></g>'
               + "</g></g>")
    if sub:
        out.append(f'<g class="{p}-fu" style="{D.delay(380)}">'
                   f'<text x="72" y="{ty}" font-size="{D.n(ts)}" font-weight="800" letter-spacing="-0.5" font-family="{D.esc(D.FONTS[fam_t])}">'
                   f'<tspan fill-opacity="0">{D.esc(title)}</tspan>'
                   f'<tspan dx="18" dy="-6" fill="{T["border_hi"]}" font-size="{D.n(ts * 0.75)}" font-weight="300" letter-spacing="0">|</tspan>'
                   f'<tspan dx="14" font-size="{D.n(ss)}" font-weight="500" letter-spacing="0" fill="{T["text2"]}" font-family="{D.esc(D.FONTS[fam_s])}">{D.esc(sub)}</tspan>'
                   f'</text></g>')
    return "".join(dfs), "".join(out), css


def _legend(T, cfg, models):
    p = P
    x, y, w, h = LEG
    src = cfg.get("legend_src")
    rows = []
    if src:
        rows = [(str(r.get("model", "")), str(r.get("role", ""))) for r in src if isinstance(r, dict)]
    else:
        seen = []
        for m in models:
            t = _tier(m)
            key = t or m
            if m and key not in [(tt or mm) for mm, tt in seen]:
                seen.append((m, t))
        seen.sort(key=lambda s: TIER_ORDER.index(s[1]) if s[1] in TIER_ORDER else 9)
        rows = [(m, LEGEND_ROLE.get(t, "")) for m, t in seen]
    rows = rows[:4]
    if not rows:
        return ""
    out = [f'<g class="{p}-fu" style="{D.delay(1550)}">', D.glass(x, y, w, h, T["theme"], p, r=18)]
    step = (h - 20) / max(len(rows), 1)
    col_w = min(max(D.text_width(m, 17, "latin", 650) for m, _ in rows), 80)
    rx = x + 34 + col_w + 10
    for i, (m, role) in enumerate(rows):
        col = _mcol(T, m)
        cy = y + 10 + step * (i + 0.5)
        out.append(f'<circle cx="{x + 20}" cy="{D.n(cy)}" r="5" fill="{col}" filter="url(#{p}-glow-s)" class="{p}-glow" style="animation-delay:-{i * 900}ms"/>')
        out.append(D.text(x + 34, cy + 6, D.truncate(m, col_w, 17, "latin", 650), 17, col, 650, "latin"))
        fam = D.family_of(role)
        out.append(D.text(rx, cy + 6, D.truncate(role, x + w - 14 - rx, 16, fam, 500), 16, T["text2"], 500, fam))
    out.append("</g>")
    return "".join(out)


def render(theme, data) -> str:
    T = D.tokens(theme)
    p = P
    cfg = _cfg(data)
    workers = cfg["workers"]
    phis, pts = _layout(len(workers))
    cols = [_mcol(T, w.get("model", "")) for w in workers]
    gate_col = T["coral"]
    sched = _schedule(phis)
    route_d = _route_d(pts)

    bg_defs, bg, bg_css = _background(T, theme)
    ed_defs, edges, ed_css, store_paths = _edges(T, phis, pts, cols, gate_col, sched)
    pk_defs, packets, pk_css = _packets(T, pts, cols, gate_col, sched, store_paths, route_d)
    co_defs, coord, co_css = _coordinator(T, cfg, sched)
    nodes, nd_css = _nodes(T, cfg, pts, cols, gate_col, sched)
    hd_defs, header, hd_css = _header(T, cfg)
    models = [cfg["coordinator"].get("model", "")] + [w.get("model", "") for w in workers]
    legend = _legend(T, cfg, models)

    body = (D.card(W, H, theme, p)
            + D.defs(D.card_clip(f"{p}-clip", W, H), D.glass_defs(theme, p), bg_defs, ed_defs, pk_defs, co_defs, hd_defs)
            + f'<g clip-path="url(#{p}-clip)">' + bg + "</g>"
            + edges + packets + coord + nodes + legend + header)

    c = cfg["coordinator"]
    title = f"{cfg['title']} — {c.get('title', '')} · {c.get('model', '')}"
    flow = " → ".join([f"{w.get('title', '')} · {w.get('model', '')}" for w in workers]
                      + [cfg["gate"].get("title", ""), cfg["ship"].get("title", "")])
    stores = ", ".join(f"{s.get('title', '')}({s.get('sub', '')})" for s in cfg["stores"])
    desc = (f"{c.get('title', '')} · {c.get('model', '')} 가 일을 나눠 워커에게 보내고 작업 패킷이 {flow} 순으로 흐른다. "
            f"{cfg['gate'].get('title', '')}: {cfg['gate'].get('sub', '')}. 저장소: {stores}.")
    return D.svg_root(W, H, theme, title, desc, body, bg_css + ed_css + pk_css + co_css + nd_css + hd_css, p)
