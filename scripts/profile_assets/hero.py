"""hero (1280×400) — 물결·별자리·AI 코어 오브 위로 이름이 순차 등장하는 머리 배너."""

from __future__ import annotations

import math

from . import design as D

W, H = 1280, 400
P = "hero"

TEXT_X = 72
TEXT_MAX_X = 812          # 오른쪽 오브 영역과 겹치지 않는 글자 한계
ORB_X, ORB_Y = 1046, 176


def _background(T, theme):
    p = P
    dark = T["dark"]
    blobs = [
        # (cx, cy, r, color, opacity 배수, 지연)
        (1090, 40, 360, "#7C3AED", 0.85 if dark else 0.55, 0),
        (190, 400, 420, "#00B4D8", 0.75, -5000),
        (720, 470, 380, "#14B8A6", 0.6, -9000),
        (1180, 360, 260, "#0077B6", 0.7, -3000),
    ]
    dfs = []
    out = []
    for i, (cx, cy, r, c, k, dl) in enumerate(blobs):
        gid = f"{p}-blob{i}"
        dfs.append(D.radial_gradient(gid, [(0, c, T["blob_opacity"] * k), (0.55, c, T["blob_opacity"] * k * 0.35), (1, c, 0)]))
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{gid})" class="{p}-floats" style="animation-delay:{dl}ms"/>')
    # 점 격자: 오브 쪽으로 진해지는 방사형 마스크
    dfs.append(D.dot_grid_pattern(f"{p}-dots", theme, gap=26, r=1.1))
    dfs.append(D.radial_gradient(f"{p}-dotsfade-g", [(0, "#fff", 1), (0.6, "#fff", 0.35), (1, "#fff", 0)],
                                 cx=ORB_X, cy=ORB_Y, r=620, units="userSpaceOnUse"))
    dfs.append(f'<mask id="{p}-dotsfade" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
               f'<rect width="{W}" height="{H}" fill="url(#{p}-dotsfade-g)"/></mask>')
    out.append(f'<rect width="{W}" height="{H}" fill="url(#{p}-dots)" mask="url(#{p}-dotsfade)"/>')
    # 유성 — 긴 쉼 사이로 가끔 스쳐 지나간다
    tail = "#FFFFFF" if dark else T["accent"]
    dfs.append(D.linear_gradient(f"{p}-meteor", [(0, tail, 0), (0.85, tail, 0.75 if dark else 0.55), (1, tail, 1)]))
    for i, (sx, sy, ang, dur, dl) in enumerate([(560, -30, 24, 11, 2600), (880, -40, 30, 13, 7400), (300, -20, 20, 17, 11800)]):
        out.append(D.motion_only(p, f'<g transform="translate({sx},{sy}) rotate({ang})"><g style="{D.anim(p, "k-meteor", dur, dl, "cubic-bezier(.3,0,.7,1)")}">'
                   f'<rect x="-130" y="-1" width="130" height="2" rx="1" fill="url(#{p}-meteor)"/>'
                   f'<circle r="2.2" fill="{tail}"/></g></g>'))
    css = D.keyframes(p, "k-meteor", "0%{transform:translateX(0);opacity:0}2%{opacity:1}12%{transform:translateX(520px);opacity:0}100%{transform:translateX(520px);opacity:0}")
    return "".join(dfs), "".join(out), css


def _orb(T):
    """AI 코어 + 궤도 링 + 위성 에이전트(코어에서 빛 입자가 흘러간다)."""
    p = P
    dark = T["dark"]
    c1, c2, c3 = T["grad"]
    dfs = [
        D.radial_gradient(f"{p}-halo", [(0, "#00B4D8", 0.42 if dark else 0.22), (0.45, "#0077B6", 0.16 if dark else 0.08), (1, "#0077B6", 0)]),
        D.radial_gradient(f"{p}-core", [(0, "#FFFFFF", 1), (0.28, "#CFF6FF", 1), (0.6, "#00B4D8", 1), (1, "#0077B6", 0.95)], fx=0.38, fy=0.34),
        D.linear_gradient(f"{p}-ring", [(0, c2, 0.95), (0.5, "#7C3AED", 0.75), (1, c3, 0.95)], 0, 0, 1, 1),
        D.linear_gradient(f"{p}-ring2", [(0, c3, 0.9), (1, c1, 0.25)], 0, 0, 1, 1),
        D.linear_gradient(f"{p}-ray", [(0, c2, 0.0), (0.5, c2, 0.55 if dark else 0.45), (1, c3, 0.15)], 0, 0, 1, 0),
        D.glow_filter(f"{p}-glow", 6, 0.9 if dark else 0.5),
        D.glow_filter(f"{p}-glow-s", 3, 1.0 if dark else 0.5),
    ]
    sat_cols = [T["accent"], T["accent2"], T["accent3"], T["accent"], T["accent2"], T["accent3"]]
    R_SAT = 106
    o = [f'<g transform="translate({ORB_X},{ORB_Y})">']
    o.append(f'<circle r="190" fill="url(#{p}-halo)" class="{p}-breathe"/>')
    # 바깥 점선 궤도(천천히 회전)
    o.append(f'<g class="{p}-spin" style="animation-duration:60s"><circle r="150" stroke="url(#{p}-ring2)" stroke-width="1.2" stroke-dasharray="2 9" opacity="{0.8 if dark else 0.9}"/>'
             f'<circle cx="150" cy="0" r="3.4" fill="{T["accent2"]}" filter="url(#{p}-glow-s)"/>'
             f'<circle cx="-150" cy="0" r="2.2" fill="{T["accent"]}"/></g>')
    # 위성 궤도 링(호 조각 역회전)
    o.append(f'<g class="{p}-spinr" style="animation-duration:40s"><circle r="{R_SAT}" stroke="url(#{p}-ring)" stroke-width="1.5" '
             f'stroke-dasharray="70 22 8 22" stroke-linecap="round" opacity="0.75"/></g>')
    # 안쪽 링
    o.append(f'<g class="{p}-spin" style="animation-duration:22s"><circle r="62" stroke="url(#{p}-ring)" stroke-width="1.2" '
             f'stroke-dasharray="3 7" opacity="0.6"/><circle cx="0" cy="-62" r="2.6" fill="{T["accent3"]}" filter="url(#{p}-glow-s)"/></g>')
    # 위성 시스템 — 통째로 아주 천천히 회전
    o.append(f'<g class="{p}-spin" style="animation-duration:90s">')
    for i in range(6):
        ang = -90 + i * 60
        a = math.radians(ang)
        sx, sy = R_SAT * math.cos(a), R_SAT * math.sin(a)
        col = sat_cols[i]
        o.append(f'<path d="M{D.n(sx * 0.32)} {D.n(sy * 0.32)}L{D.n(sx * 0.86)} {D.n(sy * 0.86)}" stroke="{col}" stroke-width="1" opacity="{0.45 if dark else 0.5}"/>')
        # 코어 → 위성으로 흐르는 빛 입자(회전된 축 위에서 x 방향으로만 이동)
        o.append(D.motion_only(p, f'<g transform="rotate({ang})"><circle r="2.6" fill="{col}" filter="url(#{p}-glow-s)" '
                 f'style="{D.anim(p, "k-ray", 2.6, -i * 430, "cubic-bezier(.4,0,.2,1)")}"/></g>'))
        o.append(f'<g transform="translate({D.n(sx)},{D.n(sy)})"><g class="{p}-pop" style="{D.delay(500 + i * 110)}">'
                 f'<circle r="15" fill="{D.rgba(col, 0.14 if dark else 0.10)}" stroke="{D.rgba(col, 0.55)}" stroke-width="1.2"/>'
                 f'<circle r="5.2" fill="{col}" filter="url(#{p}-glow-s)" class="{p}-glow" style="animation-delay:-{i * 650}ms"/></g></g>')
    o.append("</g>")
    # 코어
    o.append(f'<g class="{p}-pop" style="{D.delay(250)}"><g class="{p}-pulse">'
             f'<circle r="34" fill="url(#{p}-core)" filter="url(#{p}-glow)"/>'
             f'<path d="{D.sparkle_path(0, 0, 17, 0.2)}" fill="#FFFFFF" opacity="0.95"/></g></g>')
    o.append("</g>")
    css = D.keyframes(p, "k-ray", "0%{transform:translateX(30px);opacity:0}20%{opacity:1}80%{opacity:1}100%{transform:translateX(88px);opacity:0}")
    return "".join(dfs), "".join(o), css


def _waves(T):
    p = P
    dark = T["dark"]
    c1, c2, c3 = T["grad"]
    layers = [
        # base_y, amp, period, dur, 방향(-1=왼쪽), 위 색, 위 α, 아래 α
        (336, 10, 640, 16, -1, c1, 0.30 if dark else 0.16, 0.42 if dark else 0.22),
        (352, 8, 512, 12, 1, c2, 0.20 if dark else 0.14, 0.38 if dark else 0.22),
        (368, 6, 427, 9, -1, c3, 0.26 if dark else 0.18, 0.55 if dark else 0.30),
    ]
    dfs, out, css = [], [], []
    for i, (by, amp, per, dur, direc, col, a_top, a_bot) in enumerate(layers):
        gid = f"{p}-wave{i}"
        dfs.append(D.linear_gradient(gid, [(0, col, a_top), (1, c1, a_bot)], 0, 0, 0, 1))
        d = D.wave_path(W, per, amp, by, H + 4, phase=i * 1.3)
        kf = f"k-wave{i}"
        css.append(D.translate_loop_css(p, kf, direc * per, 0))
        start = 0 if direc < 0 else -per
        line = ""
        if i == 2:
            line = (f'<path d="{D.wave_line(W, per, amp, by, phase=i * 1.3)}" stroke="url(#{p}-waveline)" '
                    f'stroke-width="1.6" filter="url(#{p}-glow-s)" opacity="{0.9 if dark else 0.75}"/>')
        out.append(f'<g transform="translate({start},0)"><g style="{D.anim(p, kf, dur)}">'
                   f'<path d="{d}" fill="url(#{gid})"/>{line}</g></g>')
    dfs.append(D.linear_gradient(f"{p}-waveline", [(0, c2, 0.2), (0.3, "#90E0EF", 0.95), (0.6, c3, 0.9), (1, c2, 0.2)],
                                 0, 0, 1, 0))
    return "".join(dfs), "".join(out), "".join(css)


def _text(T, data):
    p = P
    dark = T["dark"]
    max_w = TEXT_MAX_X - TEXT_X
    dfs, out, css = [], [], []

    # 1) 아이브로우 — 상태 점 + 입사일
    since = data.get("since")
    eyebrow = f"SINCE {D.fmt_date(since)}" if since else ""
    eyebrow_end = TEXT_X - 14
    if eyebrow:
        eb_svg, bw = D.eyebrow(p, TEXT_X, 38, eyebrow, T["theme"], "teal", "dot", max_w=520, delay_ms=80)
        eyebrow_end = TEXT_X + bw
        out.append(eb_svg)

    # 2) 이름 — 흐르는 그라디언트 + 빛 스침
    name = data.get("name_en", "")
    name_ko = data.get("name_ko", "")
    base_y = 146
    ns = D.fit_size(name, max_w * (0.72 if name_ko else 1.0), 78, 40, "latin", 800, -1.5)
    if D.text_width(name, ns, "latin", 800, -1.5) > max_w:
        name = D.truncate(name, max_w, ns, "latin", 800)
    nw = D.text_width(name, ns, "latin", 800, -1.5)
    name_txt = D.text(TEXT_X, base_y, name, ns, None, 800, "latin", ls=-1.5)
    per = 520
    dfs.append(D.flow_gradient(f"{p}-name-flow", T["grad_text"] + ([T["accent3"]] if dark else ["#4F46E5"]), per))
    dfs.append(f'<clipPath id="{p}-name-clip">{name_txt}</clipPath>')
    css.append(D.flow_css(p, per))
    band_w = 140
    dfs.append(D.linear_gradient(f"{p}-shine", [(0, T["shine"], 0), (0.5, T["shine"], T["shine_opacity"]), (1, T["shine"], 0)], 0, 0, 1, 0))
    css.append(D.shimmer_css(p, "k-shine", TEXT_X - band_w - 40, TEXT_X + nw + 60, 0.3))
    glow = ""
    if dark:
        glow = (f'<g opacity="0.55" class="{p}-glow" filter="url(#{p}-name-blur)">'
                + D.text(TEXT_X, base_y, name, ns, T["accent"], 800, "latin", ls=-1.5) + "</g>")
        dfs.append(D.blur_filter(f"{p}-name-blur", 14))
    out.append(f'<g class="{p}-fu" style="{D.delay(220)}">{glow}'
               f'<g clip-path="url(#{p}-name-clip)">'
               + D.flow_rect(p, TEXT_X - 10, base_y - ns, nw + 40, ns * 1.3, f"{p}-name-flow", per, dur=9)
               + f'<g style="{D.anim(p, "k-shine", 7, 1700, D.EASE_IN_OUT)}"><rect x="0" y="{D.n(base_y - ns)}" width="{band_w}" '
                 f'height="{D.n(ns * 1.3)}" fill="url(#{p}-shine)" transform="skewX(-18)"/></g>'
               + "</g></g>")

    # 3) 한글 이름 — 이름 오른쪽(자리 없으면 아래 줄 role 앞으로)
    role_y = 190
    if name_ko:
        ks = 34
        kx = TEXT_X + nw + 22
        kw = D.text_width(name_ko, ks, "ko", 600)
        if kx + kw > TEXT_MAX_X:
            ks = D.fit_size(name_ko, TEXT_MAX_X - kx, 34, 22, "ko", 600)
            kw = D.text_width(name_ko, ks, "ko", 600)
        if kx + kw <= TEXT_MAX_X:
            # 투명한 영문 이름 tspan 바로 뒤에 붙여, 실제 렌더된 이름 폭을 그대로 따라간다(추정 오차 없음)
            out.append(f'<g class="{p}-fu" style="{D.delay(420)}">'
                       f'<text x="{TEXT_X}" y="{base_y}" font-family="{D.esc(D.FONT_LATIN)}" font-size="{D.n(ns)}" font-weight="800" letter-spacing="-1.5">'
                       f'<tspan fill-opacity="0">{D.esc(name)}</tspan>'
                       f'<tspan dx="20" dy="-8" fill="{T["border_hi"]}" font-size="{D.n(ks)}" font-weight="300" letter-spacing="0">|</tspan>'
                       f'<tspan dx="12" font-family="{D.esc(D.FONT_KO)}" font-size="{D.n(ks)}" font-weight="600" letter-spacing="0" fill="{T["text2"]}">{D.esc(name_ko)}</tspan>'
                       f'</text></g>')
        else:
            # 이름 옆에 자리가 없으면 아이브로우 줄(입사일 알약 오른쪽)로
            ks = D.fit_size(name_ko, TEXT_MAX_X - eyebrow_end - 16, 22, 16, "ko", 600)
            out.append(f'<g class="{p}-fd" style="{D.delay(160)}">'
                       + D.text(eyebrow_end + 16, 61, D.truncate(name_ko, TEXT_MAX_X - eyebrow_end - 16, ks, "ko", 600), ks, T["text2"], 600, "ko")
                       + "</g>")

    # 4) 직함(영) · 직함(한)
    role = data.get("role_en", "")
    if role:
        rs = D.fit_size(role, max_w, 27, 20, "latin", 600)
        role = D.truncate(role, max_w, rs, "latin", 600)
        out.append(f'<g class="{p}-fu" style="{D.delay(600)}">' + D.text(TEXT_X, role_y, role, rs, T["text"], 650, "latin") + "</g>")
    role_ko = data.get("role_ko", "")
    if role_ko:
        ks2 = D.fit_size(role_ko, max_w, 19, 16, "ko", 500)
        out.append(f'<g class="{p}-fu" style="{D.delay(760)}">' + D.text(TEXT_X, role_y + 30, D.truncate(role_ko, max_w, ks2, "ko"), ks2, T["text2"], 500, "ko") + "</g>")

    # 5) 태그라인 — 타이핑 + 깜빡이는 커서
    tag = data.get("tagline", "")
    if tag:
        fam = "mono" if D.family_of(tag) == "latin" else "ko"
        ts = D.fit_size(tag, max_w - 20, 19, 16, fam, 500)
        tag = D.truncate(tag, max_w - 20, ts, fam)
        ty = role_y + 72
        tsvg, tcss, _ = D.typewriter(p, "tag", TEXT_X + 22, ty, tag, ts, T["accent"], fam, 500, 950, 40,
                                     caret_fill=T["accent2"])
        css.append(tcss)
        out.append(f'<g class="{p}-fi" style="{D.delay(900)}">'
                   + D.text(TEXT_X, ty, "›", ts + 2, T["accent2"], 700, "mono")
                   + tsvg
                   + "</g>")

    # 6) 칩 — 하나씩 팝
    chips = data.get("chips") or []
    if chips:
        svg, _ = D.chips_row(TEXT_X, 278, chips, T["theme"], max_w, size=18, gap=10,
                             variants=["accent", "teal", "accent", "teal", "accent", "violet"],
                             cls_fn=lambda i: (f"{p}-pop", D.delay(1250 + i * 95)))
        out.append(svg)
    return "".join(dfs), "".join(out), "".join(css)


def render(theme, data) -> str:
    T = D.tokens(theme)
    p = P
    bg_defs, bg, bg_css = _background(T, theme)
    orb_defs, orb, orb_css = _orb(T)
    wv_defs, waves, wv_css = _waves(T)
    tx_defs, txt, tx_css = _text(T, data)
    stars = D.constellation(p, theme, (24, 20, 1232, 310), count=34, seed=11, link_dist=170,
                            dim_box=(40, 24, 800, 300), dim=0.28)
    body = (D.card(W, H, theme, p)
            + D.defs(D.card_clip(f"{p}-clip", W, H), bg_defs, orb_defs, wv_defs, tx_defs)
            + f'<g clip-path="url(#{p}-clip)">'
            + bg
            + f'<g class="{p}-fi" style="animation-duration:2.4s">{stars}</g>'
            + f'<g class="{p}-fi" style="animation-duration:1.6s;{D.delay(100)}">{orb}</g>'
            + waves
            + "</g>"
            + txt)
    name = data.get("name_en", "")
    title = f"{name} {data.get('name_ko', '')} — {data.get('role_en', '')}".strip()
    desc = " · ".join(x for x in [data.get("tagline", ""), " / ".join(data.get("chips") or [])] if x)
    return D.svg_root(W, H, theme, title, desc, body, bg_css + orb_css + wv_css + tx_css, p)
