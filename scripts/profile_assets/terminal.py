"""terminal (1280×460~) — AI 에이전트를 지휘하는 macOS 터미널 세션 재생.

data.terminal 의 줄(kind: cmd | info | ok, text)을 순서대로 타이핑한다.
- 타이핑은 한 번만 재생하고(약 6초 안) 최종 화면에서 멈춘다. README 는 이미지를 불러온 순간부터
  재생하므로, 스크롤해 닿은 사람이 반쯤 찬 화면이 아니라 완결된 화면을 읽게 하려는 것.
  이후에는 마지막 '$' 캐럿 깜빡임과 배경 장식(네온 빔·오로라·스침 빛·별자리)만 무한 루프.
- 글자마다 x 좌표를 직접 지정한다(모노 0.6em, 한글 1.0em 칸). 대체 폰트로 떠도 줄 폭·캐럿·타이핑
  경계가 어긋나지 않게 하려는 것. 공백은 그리지 않고 칸만 비운다(SVG 공백 접힘 회피).
- 줄마다 keyframes 하나: 클립 사각형과 캐럿이 같은 translateX 계단을 공유한다.
  기본 상태(애니메이션 없음) = 클립 이동 0 = 전부 보임 → 축소 모드에서 최종 화면.
"""

from __future__ import annotations

import math
import unicodedata

from . import design as D

P = "terminal"
W = 1280               # 다른 에셋과 같은 폭 → README 에서 같은 배율(0.65)로 줄어든다
MIN_H = 460
TYPE_BUDGET_MS = 5900  # 첫 대기부터 새 프롬프트까지 목표 시간
START_MS = 400         # 첫 타이핑 전 대기
CMD_MS = (900, 1800)   # 명령 줄 한 줄 입력 시간(사람 타자 속도, 짧은 명령은 더 빨리)
CMD_CHAR_MS = 52       # 명령 글자당 평균(약 19cps)
OUT_MS = (380, 600)    # 출력 줄 한 줄 스트리밍 시간
OUT_CHAR_MS = 1000 / 130  # 출력 글자당(약 130cps)
THINK_MS = 650         # 명령 입력 후 첫 출력까지(Thinking… 표시)
LINE_GAP_MS = 140      # 출력 줄 사이 간격
FINAL_GAP_MS = 240     # 마지막 출력 → 새 프롬프트
TAIL_MS = 1300         # 마지막 줄 스침 빛·캐럿이 끝날 여유
CLIP_INSET = 3         # 타이핑 중 클립 오른쪽 경계를 다음 글자 칸보다 이만큼 왼쪽에(다음 글자 획 비침 방지)

MX, MY = 56, 30       # 카드 안 창 여백(가로는 stats·domains 그리드와 같은 56)
TITLE_H = 46
PAD_X = 34
PAD_TOP = 40
PAD_BOTTOM = 40
WIN_R = 16

GLYPHS = {"⏺": "info", "●": "info", "✓": "ok", "✔": "ok"}


# ---------------------------------------------------------------------------
# 글자 칸 · 줄바꿈
# ---------------------------------------------------------------------------

def _cell(ch: str) -> float:
    """글자 칸 폭(em). 넓은 글자(한글·CJK)는 1.0, 나머지 0.6."""
    return 1.0 if unicodedata.east_asian_width(ch) in ("W", "F") or ord(ch) >= 0x1F000 else 0.6


def _wrap_cells(chars, size, max_w):
    """chars: [(ch, role)] → 행 목록. 공백에서 끊고, 단어가 너무 길면 글자 단위로 자른다.
    공백 여러 개는 그대로 보존한다(줄 첫머리 공백만 제거)."""
    rows, cur, cur_w, last_space = [], [], 0.0, -1
    for ch, role in chars:
        cw = _cell(ch) * size
        if cur_w + cw > max_w and cur:
            if ch == " ":
                rows.append(cur)
                cur, cur_w, last_space = [], 0.0, -1
                continue
            if last_space > 0:
                head, tail = cur[:last_space], cur[last_space + 1:]
                rows.append(head)
                cur = tail
            else:
                rows.append(cur)
                cur = []
            while cur and cur[0][0] == " ":
                cur.pop(0)
            cur_w = sum(_cell(c) * size for c, _ in cur)
            last_space = max((i for i, (c, _) in enumerate(cur) if c == " "), default=-1)
        if ch == " " and not cur:
            continue
        if ch == " ":
            last_space = len(cur)
        cur.append((ch, role))
        cur_w += cw
    if cur:
        rows.append(cur)
    # 줄 끝 공백 제거
    out = []
    for r in rows:
        while r and r[-1][0] == " ":
            r.pop()
        out.append(r)
    return out or [[]]


# ---------------------------------------------------------------------------
# 구문 색 역할
# ---------------------------------------------------------------------------

def _roles(kind: str, s: str):
    """문자마다 색 역할을 붙인다."""
    out = []
    if kind == "cmd":
        in_q, q = False, ""
        word_idx, prev_space, word_start = 0, True, 0
        words = []
        i = 0
        # 단어 단위로 먼저 나눠 첫 단어 = 프로그램, '-' 로 시작 = 플래그
        for i, ch in enumerate(s):
            if in_q:
                out.append((ch, "str"))
                if ch == q:
                    in_q = False
                continue
            if ch in "\"'":
                in_q, q = True, ch
                out.append((ch, "str"))
                prev_space = False
                continue
            if ch == " ":
                out.append((ch, "sp"))
                if not prev_space:
                    word_idx += 1
                prev_space = True
                continue
            if prev_space:
                word_start = i
            prev_space = False
            word = s[word_start:].split(" ")[0]
            if word_idx == 0:
                out.append((ch, "prog"))
            elif word.startswith("-"):
                out.append((ch, "flag"))
            else:
                out.append((ch, "arg"))
        return out
    base = "info" if kind == "info" else "ok"
    for i, ch in enumerate(s):
        if ch in "→·|—" or ch == "←":
            out.append((ch, "sym"))
        elif kind == "ok" and (ch.isdigit() or (ch in ",.%/" and 0 < i < len(s) - 1 and s[i - 1].isdigit() and s[i + 1].isdigit())):
            out.append((ch, "num"))
        else:
            out.append((ch, base))
    return out


def _palette(T):
    dark = T["dark"]
    return {
        "prompt": T["accent2"],
        "prog": "#90E0EF" if dark else "#005F92",
        "flag": T["accent3"],
        "arg": T["accent2"],
        "str": T["text"],
        "sp": T["text"],
        "info": T["accent"],
        "ok": T["accent2"],
        "num": T["text"],
        "sym": T["accent3"] if dark else "#6D4BC9",
    }


_BOLD = {"prog", "num"}


# ---------------------------------------------------------------------------
# 렌더
# ---------------------------------------------------------------------------

def render(theme, data) -> str:
    T = D.tokens(theme)
    p = P
    dark = T["dark"]
    PAL = _palette(T)

    lines = []
    for item in (data.get("terminal") or []):
        if not isinstance(item, dict):
            continue
        kind = item.get("kind", "info")
        kind = kind if kind in ("cmd", "info", "ok") else "info"
        s = str(item.get("text", "")).strip()
        if s and s[0] in GLYPHS:
            s = s[1:].lstrip()
        if s:
            lines.append((kind, s))
    title = str(data.get("terminal_title") or "claude")

    win_x, win_w = MX, W - MX * 2
    text_x = win_x + PAD_X
    content_w = win_w - PAD_X * 2

    # 글자 크기: 24 에서 18 까지 줄여 7행 안에 들도록. 그래도 넘치면 높이를 늘린다.
    def layout(size):
        gutter = 2 * 0.6 * size
        rows = []  # (line_idx, kind, cells, is_first)
        for li, (kind, s) in enumerate(lines):
            wrapped = _wrap_cells(_roles(kind, s), size, content_w - gutter)
            for ri, r in enumerate(wrapped):
                rows.append((li, kind, r, ri == 0))
        return gutter, rows

    size = 24.0
    while True:
        gutter, rows = layout(size)
        if len(rows) <= 7 or size <= 18:
            break
        size -= 0.5
    lh = round(size * 1.72, 1)
    n_rows = len(rows) + 1  # 마지막 프롬프트 행
    win_h_need = TITLE_H + PAD_TOP + (n_rows - 1) * lh + size * 0.35 + PAD_BOTTOM + 18
    H = int(max(MIN_H, math.ceil(win_h_need + MY * 2)))
    win_y, win_h = MY, H - MY * 2
    y0 = win_y + TITLE_H + PAD_TOP + size * 0.8

    # ---- 시간표(한 번만 재생) ------------------------------------------------
    # 명령 줄은 사람 타자 속도, 출력 줄은 줄당 0.4~0.6초 스트리밍. 데이터가 길어져 목표 시간을
    # 넘으면 출력·간격만 줄인다(명령 타자감은 유지). 그래도 넘치면 그냥 길어진다(한 번 재생이라 무해).
    R = D.rng(11)
    line_rows = {}
    for idx, r in enumerate(rows):
        line_rows.setdefault(r[0], []).append(idx)
    line_chars = {li: sum(len(rows[i][2]) for i in ix) for li, ix in line_rows.items()}

    def line_ms(li, kind):
        c = line_chars.get(li, 0)
        if kind == "cmd":
            return D.clamp(c * CMD_CHAR_MS, *CMD_MS)
        return D.clamp(c * OUT_CHAR_MS, *OUT_MS)

    n_lines = len(lines)
    cmd_total = sum(line_ms(li, k) for li, (k, _) in enumerate(lines) if k == "cmd")
    n_think = sum(1 for i in range(n_lines) if lines[i][0] == "cmd" and (i + 1 >= n_lines or lines[i + 1][0] != "cmd"))
    out_total = sum(line_ms(li, k) for li, (k, _) in enumerate(lines) if k != "cmd")
    gaps_total = sum(LINE_GAP_MS for i in range(1, n_lines) if lines[i - 1][0] != "cmd")
    fixed = START_MS + cmd_total + n_think * THINK_MS + FINAL_GAP_MS
    flex = out_total + gaps_total
    squeeze = D.clamp((TYPE_BUDGET_MS - fixed) / flex, 0.55, 1.0) if flex else 1.0
    think, gap = THINK_MS, LINE_GAP_MS * squeeze

    t = START_MS
    sched = [None] * len(rows)  # 행마다 (start, [char reveal times], end)
    think_windows = []
    prev_kind = None
    for li, (kind, _s) in enumerate(lines):
        ix = line_rows.get(li, [])
        if not ix:
            continue
        if prev_kind == "cmd" and kind != "cmd":
            think_windows.append((t + 80, t + think, ix[0]))
            t += think
        elif prev_kind == "cmd" and kind == "cmd":
            t += think * 0.6
        elif prev_kind is not None:
            t += gap
        # 글자별 가중치(명령은 리듬이 들쭉날쭉, 출력은 고르게) → 줄 시간에 맞춰 정규화
        weights = []
        for i in ix:
            for ch, _ in rows[i][2]:
                w = R.uniform(0.55, 1.6) if kind == "cmd" else R.uniform(0.8, 1.2)
                if kind == "cmd" and ch == " ":
                    w *= 1.5
                weights.append(w)
        dur = line_ms(li, kind) * (1.0 if kind == "cmd" else squeeze)
        tw_ = sum(weights) or 1.0
        k = 0
        for i in ix:
            start, times = t, []
            for _ in rows[i][2]:
                t += dur * weights[k] / tw_
                k += 1
                times.append(t)
            sched[i] = (start, times, t)
        prev_kind = kind
    if lines and lines[-1][0] == "cmd":
        think_windows.append((t + 80, t + think, len(rows)))
        t += think
    t_final = t + FINAL_GAP_MS
    loop_ms = t_final + TAIL_MS
    L = round(loop_ms / 1000, 3)

    def pct(ms):
        return f"{D.clamp(ms / loop_ms * 100, 0, 100):.3f}".rstrip("0").rstrip(".") + "%"

    def once(name, ease="linear"):
        """타이핑 계열 애니메이션: 한 번 재생 후 마지막 상태로 정지."""
        return D.anim(p, name, L, 0, ease, "1", "both")

    # ---- defs -----------------------------------------------------------------
    c1, c2, c3 = T["grad"]
    win_cx, win_cy = win_x + win_w / 2, win_y + win_h / 2
    beam_r = math.hypot(win_w, win_h) / 2 + 20
    dfs = [
        D.card_clip(f"{p}-clip", W, H),
        f'<clipPath id="{p}-wclip"><rect x="{win_x}" y="{win_y}" width="{win_w}" height="{win_h}" rx="{WIN_R}"/></clipPath>',
        D.blur_filter(f"{p}-blob", 46),
        D.blur_filter(f"{p}-soft", 6),
        D.glow_filter(f"{p}-glow", 3.2, 0.9 if dark else 0.45),
        D.glow_filter(f"{p}-glowt", 2.2, 0.55 if dark else 0.0),
        D.shadow_filter(f"{p}-shadow", theme, dy=18, std=24),
        D.linear_gradient(f"{p}-win", [(0, "#0A1424", 0.92), (1, "#0B1B2E", 0.86)] if dark
                          else [(0, "#FFFFFF", 0.94), (1, "#F3FAFF", 0.9)], 0, 0, 0, 1),
        D.linear_gradient(f"{p}-bar", [(0, "#13243A", 0.95), (1, "#0E1C2F", 0.95)] if dark
                          else [(0, "#F4F9FD", 1), (1, "#E8F2FA", 1)], 0, 0, 0, 1),
        D.linear_gradient(f"{p}-edge", [(0, "#90E0EF", 0.42), (0.5, "#90E0EF", 0.12), (1, "#2DD4BF", 0.32)] if dark
                          else [(0, "#9FCBE6", 1), (0.5, "#D0E7F5", 1), (1, "#8FD3C9", 1)], 0, 0, 1, 1),
        D.linear_gradient(f"{p}-beam", [(0, c2, 0), (0.44, c2, 0), (0.485, "#90E0EF" if dark else c2, 1),
                                         (0.5, "#FFFFFF" if dark else c1, 1), (0.515, T["violet"], 1),
                                         (0.56, T["violet"], 0), (1, T["violet"], 0)]),
        D.linear_gradient(f"{p}-prog", [c1, c2, c3, T["violet"]]),
        D.linear_gradient(f"{p}-sheen", [(0, T["shine"], 0), (0.5, T["shine"], 0.07 if dark else 0.55), (1, T["shine"], 0)]),
        D.radial_gradient(f"{p}-refl", [(0, c2, 0.16 if dark else 0.10), (1, c2, 0)]),
        D.linear_gradient(f"{p}-ai", T["grad_ai"], 0, 0, 1, 1),
        D.linear_gradient(f"{p}-uline", [(0, c2, 0.85 if dark else 0.7), (1, T["accent2"], 0.85 if dark else 0.7)]),
        D.linear_gradient(f"{p}-hlok", [(0, T["accent2"], 0), (0.12, T["accent2"], 0.16 if dark else 0.12), (1, T["accent2"], 0)]),
        D.linear_gradient(f"{p}-hlinfo", [(0, T["violet"], 0), (0.12, T["violet"], 0.18 if dark else 0.10), (1, c2, 0)]),
        f'<mask id="{p}-ring" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
        f'<rect x="{win_x}" y="{win_y}" width="{win_w}" height="{win_h}" rx="{WIN_R}" fill="none" stroke="#fff" stroke-width="2"/></mask>',
        f'<mask id="{p}-ring2" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
        f'<rect x="{win_x}" y="{win_y}" width="{win_w}" height="{win_h}" rx="{WIN_R}" fill="none" stroke="#fff" stroke-width="10"/></mask>',
    ]

    css = []
    css.append(D.shimmer_css(p, "k-sheen", -420, win_w + 120, 0.3))

    body = [D.card(W, H, theme, p), D.defs(*dfs)]

    # ---- 배경: 오로라 덩어리 · 별자리 ----------------------------------------
    bo = T["blob_opacity"]
    body.append(f'<g clip-path="url(#{p}-clip)">')
    body.append(f'<g opacity="{bo}" filter="url(#{p}-blob)">')
    for i, (bx, by, r, col) in enumerate(((90, 60, 150, c1), (W - 80, H - 50, 170, T["violet"]),
                                          (W * 0.62, -10, 120, c3), (W * 0.22, H + 10, 130, c2))):
        body.append(f'<g transform="translate({D.n(bx)},{D.n(by)})"><circle r="{r}" fill="{col}" class="{p}-floats" '
                    f'style="animation-delay:-{i * 3500}ms;animation-duration:{16 + i * 2}s"/></g>')
    body.append("</g>")
    body.append(D.constellation(p, theme, (0, 0, W, H), count=22, seed=5, link_dist=150,
                                dim_box=(win_x, win_y, win_w, win_h), dim=0.0))
    body.append("</g>")

    # ---- 창 -------------------------------------------------------------------
    # 바깥 네온 번짐(빔) — 회전하는 그라디언트를 테두리 링으로만 보이게
    beam_op = 0.9 if dark else 0.55
    beam = (f'<g transform="translate({D.n(win_cx)},{D.n(win_cy)}) rotate(-28)">'
            f'<rect x="{D.n(-beam_r)}" y="{D.n(-beam_r)}" width="{D.n(beam_r * 2)}" height="{D.n(beam_r * 2)}" '
            f'fill="url(#{p}-beam)" class="{p}-spin" style="animation-duration:10s"/></g>')
    body.append(f'<rect x="{win_x}" y="{win_y}" width="{win_w}" height="{win_h}" rx="{WIN_R}" fill="url(#{p}-win)" filter="url(#{p}-shadow)"/>')
    body.append(f'<g opacity="{0.55 if dark else 0.3}" filter="url(#{p}-soft)"><g mask="url(#{p}-ring2)">{beam}</g></g>')
    # 창 내부 장식(반사광 · 스침 빛)
    body.append(f'<g clip-path="url(#{p}-wclip)">')
    body.append(f'<ellipse cx="{win_x + 160}" cy="{win_y + TITLE_H + 30}" rx="420" ry="190" fill="url(#{p}-refl)" class="{p}-breathe"/>')
    body.append(f'<rect x="{win_x}" y="{win_y}" width="{win_w}" height="{TITLE_H}" fill="url(#{p}-bar)"/>')
    body.append(f'<path d="M{win_x} {win_y + TITLE_H}H{win_x + win_w}" stroke="{T["border"]}" stroke-width="1"/>')
    body.append(f'<g transform="translate({win_x},{win_y}) skewX(-18)"><rect x="0" y="0" width="220" height="{win_h}" '
                f'fill="url(#{p}-sheen)" style="{D.anim(p, "k-sheen", 9, 1800, D.EASE_IN_OUT)}"/></g>')
    body.append("</g>")
    body.append(f'<rect x="{win_x + 0.75}" y="{win_y + 0.75}" width="{win_w - 1.5}" height="{win_h - 1.5}" rx="{WIN_R}" fill="none" stroke="url(#{p}-edge)" stroke-width="1.5"/>')
    body.append(f'<path d="M{win_x + WIN_R} {win_y + 2}H{win_x + win_w - WIN_R}" stroke="url(#{p}-card-hl)" stroke-width="1"/>')
    body.append(f'<g opacity="{beam_op}"><g mask="url(#{p}-ring)">{beam}</g></g>')

    # 제목 표시줄 — 신호등 · 제목 · LIVE
    ty = win_y + TITLE_H / 2
    for i, col in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
        cx = win_x + 24 + i * 22
        body.append(f'<circle cx="{cx}" cy="{D.n(ty)}" r="6.5" fill="{col}" stroke="{D.rgba("#000000", 0.18)}" stroke-width="0.8"/>'
                    f'<circle cx="{cx}" cy="{D.n(ty - 2)}" r="2.6" fill="#FFFFFF" opacity="0.28"/>')
    tsize = D.fit_size(title, win_w - 360, 17, 16, "mono", 600)
    ttxt = D.truncate(title, win_w - 360, tsize, "mono", 600)
    tw = D.text_width(ttxt, tsize, "mono", 600)
    tx = win_cx - tw / 2 + 12
    body.append(f'<path d="{D.sparkle_path(tx - 16, ty, 7.5)}" fill="url(#{p}-ai)" class="{p}-pulse" filter="url(#{p}-glowt)"/>')
    body.append(D.text(tx, ty + tsize * 0.36, ttxt, tsize, T["text2"], 600, "mono"))
    chip_svg, cw = D.chip(0, 0, "LIVE", theme, size=16, variant="teal", dot=True)
    chip_svg, _ = D.chip(win_x + win_w - 20 - cw, ty - 16, "LIVE", theme, size=16, variant="teal", h=32, dot=True)
    body.append(chip_svg)
    dot_cx = win_x + win_w - 20 - cw + round(16 * 0.8) + 16 * 0.25
    body.append(f'<g class="{p}-m"><circle cx="{D.n(dot_cx)}" cy="{D.n(ty)}" r="6" fill="{T["accent2"]}" opacity="0.35" class="{p}-pulse"/></g>')

    # ---- 본문 행 --------------------------------------------------------------
    rows_svg = ["<g>"]
    cw_unit = 0.6 * size
    for idx, (li, kind, cells, first) in enumerate(rows):
        start, times, end = sched[idx]
        y = y0 + idx * lh
        x0 = text_x + gutter
        # 글자 x 좌표
        xs, cx = [], x0
        for ch, _ in cells:
            xs.append(cx)
            cx += _cell(ch) * size
        row_w = cx - x0
        cum = [xs[i] + _cell(cells[i][0]) * size - x0 for i in range(len(cells))]
        # keyframes: 클립·캐럿 공용 translateX 계단. 클립 오른쪽 끝(이동 0 일 때 x0+row_w+2)이
        # 다음 글자 칸 시작보다 왼쪽에 오도록 CLIP_INSET 만큼 덜 연다. 줄의 마지막 글자는 전부 연다.
        kf = [f"0%{{transform:translateX({D.n(-row_w - 14)}px)}}"]
        for j, (tm, c) in enumerate(zip(times, cum)):
            off = 0 if j == len(cum) - 1 else c - row_w - 2 - CLIP_INSET
            kf.append(f"{pct(tm)}{{transform:translateX({D.n(off)}px)}}")
        kf.append("100%{transform:translateX(0)}")
        css.append(D.keyframes(p, f"k-r{idx}", "".join(kf)))
        # 캐럿 표시 구간
        nxt = sched[idx + 1][0] if idx + 1 < len(sched) else t_final
        car_off = min(nxt, end + 420)
        css.append(D.keyframes(p, f"k-c{idx}", f"0%{{opacity:0}}{pct(start)}{{opacity:1}}{pct(car_off)}{{opacity:0}}100%{{opacity:0}}"))
        # 앞머리(프롬프트/글리프) 등장
        lead = ""
        gx = text_x
        if first:
            css.append(D.keyframes(p, f"k-g{idx}", f"0%{{opacity:0}}{pct(0 if idx == 0 else max(start - (40 if kind == 'cmd' else 0), 0))}{{opacity:1}}100%{{opacity:1}}"))
            gst = f'style="{once(f"k-g{idx}", "step-end")}"'
            if kind == "cmd":
                lead = (f'<g {gst}>' + D.text(gx, y, "$", size, PAL["prompt"], 700, "mono") + "</g>")
            elif kind == "info":
                cy = y - size * 0.34
                lead = (f'<g {gst}><g transform="translate({D.n(gx + size * 0.32)},{D.n(cy)})">'
                        f'<g opacity="{0.5 if dark else 0.3}"><circle r="{D.n(size * 0.42)}" fill="{T["violet"]}" class="{p}-pulse" filter="url(#{p}-soft)"/></g>'
                        f'<circle r="{D.n(size * 0.26)}" fill="url(#{p}-ai)" filter="url(#{p}-glow)"/></g></g>')
            else:
                cy = y - size * 0.34
                s2 = size * 0.3
                lead = (f'<g {gst}><g transform="translate({D.n(gx + size * 0.32)},{D.n(cy)})">'
                        f'<path d="M{D.n(-s2)} {D.n(s2 * 0.05)}L{D.n(-s2 * 0.25)} {D.n(s2 * 0.75)}L{D.n(s2 * 1.05)} {D.n(-s2 * 0.8)}" '
                        f'stroke="{PAL["ok"]}" stroke-width="{D.n(size * 0.13)}" stroke-linecap="round" stroke-linejoin="round" filter="url(#{p}-glowt)"/></g></g>')
        # 색 묶음 tspan(공백은 그리지 않음)
        spans, run, run_role, run_x = [], "", None, []
        unders = []  # 핵심 수치 밑 글로우 밑줄(모바일 축소에서도 수치가 덩어리로 보이게)

        def flush():
            if run:
                wt = f' font-weight="{800 if run_role == "num" else 700}"' if run_role in _BOLD else ""
                spans.append(f'<tspan x="{" ".join(D.n(v) for v in run_x)}" fill="{PAL[run_role]}"{wt}>{D.esc(run)}</tspan>')
                if run_role == "num" and len(run) >= 2:
                    ux = run_x[0]
                    uw = run_x[-1] + _cell(run[-1]) * size - ux
                    unders.append(f'<rect x="{D.n(ux)}" y="{D.n(y + size * 0.2)}" width="{D.n(uw)}" height="{D.n(max(2.0, size * 0.11))}" '
                                  f'rx="1.2" fill="url(#{p}-uline)"/>')

        for (ch, role), xx in zip(cells, xs):
            if ch == " ":
                flush()
                run, run_role, run_x = "", None, []
                continue
            if role != run_role and run:
                flush()
                run, run_x = "", []
            run_role = role
            run += ch
            run_x.append(xx)
        flush()
        txt = (f'<text y="{D.n(y)}" font-size="{D.n(size)}" font-weight="500" font-family="{D.esc(D.FONT_MONO)}">'
               + "".join(spans) + "</text>")
        txt = "".join(unders) + txt
        cid = f"{p}-rc{idx}"
        rst = once(f"k-r{idx}", "step-end")
        top = y - size * 1.05
        # 출력 한 줄이 끝나는 순간 행 뒤로 빛이 한 번 스친다(줄마다 1회 — 번쩍임 제한 안쪽)
        last_of_line = idx + 1 >= len(rows) or rows[idx + 1][0] != li
        if kind != "cmd" and last_of_line:
            first_idx = next(j for j in range(len(rows)) if rows[j][0] == li)
            hy = y0 + first_idx * lh - size * 1.12
            hh = (idx - first_idx) * lh + size * 1.6
            css.append(D.keyframes(p, f"k-hl{idx}", f"0%{{opacity:0;transform:translateX(-40px)}}{pct(end - 80)}{{opacity:0;transform:translateX(-40px)}}"
                                                    f"{pct(end + 120)}{{opacity:1;transform:translateX(0)}}{pct(end + 1100)}{{opacity:0;transform:translateX(60px)}}"
                                                    f"100%{{opacity:0;transform:translateX(60px)}}"))
            rows_svg.append(D.motion_only(p,
                f'<g opacity="0" style="{once(f"k-hl{idx}", D.EASE_OUT)}">'
                f'<rect x="{D.n(text_x - 14)}" y="{D.n(hy)}" width="{D.n(min(win_w - PAD_X, row_w + gutter + 120))}" height="{D.n(hh)}" rx="8" '
                f'fill="url(#{p}-hl{"ok" if kind == "ok" else "info"})"/></g>'))
        rows_svg.append(
            f'<clipPath id="{cid}"><rect x="{D.n(x0 - 2)}" y="{D.n(top)}" width="{D.n(row_w + 4)}" height="{D.n(size * 1.5)}" style="{rst}"/></clipPath>'
            + lead
            + f'<g clip-path="url(#{cid})"{" filter=" + chr(34) + "url(#" + p + "-glowt)" + chr(34) if dark and kind != "cmd" else ""}>{txt}</g>'
            + f'<g style="{rst}"><rect x="{D.n(x0 + row_w + 2)}" y="{D.n(y - size * 0.86)}" width="{D.n(size * 0.55)}" height="{D.n(size * 1.08)}" rx="2" '
              f'fill="{T["accent"] if kind == "cmd" else T["accent3"]}" opacity="0" style="{once(f"k-c{idx}", "step-end")}"/></g>'
        )

    # Thinking… (명령 → 첫 출력 사이, 그 자리에 잠깐)
    for k, (a, b, at_idx) in enumerate(think_windows):
        y = y0 + at_idx * lh
        css.append(D.keyframes(p, f"k-th{k}", f"0%{{opacity:0}}{pct(a)}{{opacity:1}}{pct(b)}{{opacity:0}}100%{{opacity:0}}"))
        sx = text_x + size * 0.32
        sy = y - size * 0.34
        rows_svg.append(D.motion_only(p,
            f'<g opacity="0" style="{once(f"k-th{k}", "step-end")}">'
            f'<g transform="translate({D.n(sx)},{D.n(sy)})"><path d="{D.sparkle_path(0, 0, size * 0.48)}" fill="url(#{p}-ai)" '
            f'class="{p}-spin" style="animation-duration:1.8s" filter="url(#{p}-glowt)"/></g>'
            + f'<g class="{p}-breathe" style="animation-duration:1.6s">'
            + D.text(text_x + gutter, y, "Thinking…", size, T["accent3"], 500, "mono") + "</g></g>"))

    # 마지막 프롬프트 + 깜빡 캐럿(기본 상태에서도 보임)
    fy = y0 + len(rows) * lh
    css.append(D.keyframes(p, "k-final", f"0%{{opacity:0}}{pct(t_final)}{{opacity:1}}100%{{opacity:1}}"))
    rows_svg.append(f'<g style="{once("k-final", "step-end")}">'
                    + D.text(text_x, fy, "$", size, PAL["prompt"], 700, "mono")
                    + f'<rect x="{D.n(text_x + gutter + 1)}" y="{D.n(fy - size * 0.86)}" width="{D.n(size * 0.55)}" height="{D.n(size * 1.08)}" rx="2" '
                      f'fill="{T["accent"]}" class="{p}-blink" filter="url(#{p}-glowt)"/></g>')
    # 첫 명령 전 대기 캐럿(프롬프트 옆에서 깜빡임) — 움직일 때만
    if rows and rows[0][1] == "cmd":
        css.append(D.keyframes(p, "k-idle", f"0%{{opacity:1}}{pct(sched[0][0])}{{opacity:0}}100%{{opacity:0}}"))
        rows_svg.append(D.motion_only(p,
            f'<g opacity="0" style="{once("k-idle", "step-end")}"><rect x="{D.n(text_x + gutter + 1)}" y="{D.n(y0 - size * 0.86)}" '
            f'width="{D.n(size * 0.55)}" height="{D.n(size * 1.08)}" rx="2" fill="{T["accent"]}" class="{p}-blink"/></g>'))
    rows_svg.append("</g>")
    body.extend(rows_svg)

    # ---- 진행 막대(창 아래쪽) — 세션 진행에 맞춰 차오른다 -----------------------
    bx, bw, byy = win_x + PAD_X, win_w - PAD_X * 2, win_y + win_h - 20
    cmd_end = sched[0][2] if sched else 0
    out_end = sched[-1][2] if sched else 0
    css.append(D.keyframes(p, "k-prog", f"0%{{transform:scaleX(0)}}{pct(START_MS)}{{transform:scaleX(0)}}{pct(cmd_end)}{{transform:scaleX(.1)}}"
                                        f"{pct(out_end)}{{transform:scaleX(1)}}100%{{transform:scaleX(1)}}"))
    # 머리점: 100% 에 닿으면 그 자리에 남아 글로우 맥동(진행 막대도 100% 에서 정지)
    css.append(D.keyframes(p, "k-head", f"0%{{transform:translateX({-bw}px);opacity:0}}{pct(START_MS)}{{transform:translateX({-bw}px);opacity:1}}"
                                        f"{pct(cmd_end)}{{transform:translateX({D.n(-bw * 0.9)}px)}}{pct(out_end)}{{transform:translateX(0);opacity:1}}"
                                        f"100%{{transform:translateX(0);opacity:1}}"))
    body.append(f'<rect x="{bx}" y="{byy}" width="{bw}" height="3" rx="1.5" fill="{T["border"]}" opacity="{0.7 if dark else 1}"/>')
    body.append(f'<rect x="{bx}" y="{byy}" width="{bw}" height="3" rx="1.5" fill="url(#{p}-prog)" filter="url(#{p}-glowt)" '
                f'style="{once("k-prog")};transform-box:fill-box;transform-origin:0 0"/>')
    body.append(f'<g opacity="0" style="{once("k-head")}"><g class="{p}-glow">'
                f'<circle cx="{bx + bw}" cy="{byy + 1.5}" r="9" fill="{T["violet"]}" opacity="{0.35 if dark else 0.22}" '
                f'class="{p}-pulse" filter="url(#{p}-soft)"/>'
                f'<circle cx="{bx + bw}" cy="{byy + 1.5}" r="5" fill="{T["shine"] if dark else c2}" filter="url(#{p}-glow)"/></g></g>')

    desc = " / ".join(s for _, s in lines) or "AI 에이전트 터미널 세션"
    return D.svg_root(W, H, theme, title, desc, "".join(body), "".join(css), p)
