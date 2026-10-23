"""divider (1280×36) — 흐르는 그라디언트 선 위로 빛 펄스가 지나가는 섹션 구분선."""

from __future__ import annotations

from . import design as D

W, H = 1280, 36
P = "divider"
CY = 18


def render(theme, data) -> str:
    T = D.tokens(theme)
    p = P
    dark = T["dark"]
    c1, c2, c3 = T["grad"]
    per = 640
    line_cols = [c1, c2, c3, T["violet"], c2]
    dfs = [
        D.fade_mask(f"{p}-fade", W, H, "x", 0.16),
        D.flow_gradient(f"{p}-flow", line_cols, per),
        # 펄스 코어는 양 테마 모두 흰색. 라이트는 청록 선과 대비가 없어 ocean 테두리 층(rim)을 밑에 깔아 '반짝임'을 만든다.
        D.linear_gradient(f"{p}-pulse", [(0, T["shine"], 0), (0.5, T["shine"], 0.95), (1, T["shine"], 0)]),
        D.linear_gradient(f"{p}-rim", [(0, c1, 0), (0.5, c1, 0.9), (1, T["violet"], 0)]),
        D.linear_gradient(f"{p}-halo", [(0, c2, 0), (0.5, c2, 0.55 if dark else 0.25), (1, c3, 0)]),
        D.glow_filter(f"{p}-glow", 3, 0.9 if dark else 0.5),
        D.blur_filter(f"{p}-blur", 4),
    ]
    css = D.flow_css(p, per) + D.keyframes(
        p, "k-run", "0%{transform:translateX(-260px);opacity:0}6%{opacity:1}44%{opacity:1}50%{transform:translateX(1380px);opacity:0}100%{transform:translateX(1380px);opacity:0}")
    css += D.keyframes(p, "k-runr", "0%,50%{transform:translateX(1380px);opacity:0}56%{opacity:.8}94%{opacity:.8}100%{transform:translateX(-260px);opacity:0}")

    body = [D.defs(*dfs), f'<g mask="url(#{p}-fade)">']
    # 바탕 헤어라인 + 은은한 번짐
    body.append(f'<rect x="0" y="{CY - 3}" width="{W}" height="6" fill="url(#{p}-flow)" opacity="{0.28 if dark else 0.18}" filter="url(#{p}-blur)"/>')
    # 흐르는 그라디언트 선(모바일 0.3배 축소에서도 남도록 3)
    body.append(D.flow_rect(p, 0, CY - 1.5, W, 3, f"{p}-flow", per, dur=10))
    # 빛 펄스 — 왼→오, 잠시 뒤 오→왼(더 옅게)
    def pulse(x, w, h, halo_x, halo_w, halo_h):
        rim = "" if dark else (f'<rect x="{x - 6}" y="{CY - h / 2 - 1.2}" width="{w + 12}" height="{h + 2.4}" rx="{h / 2 + 1.2}" '
                               f'fill="url(#{p}-rim)"/>')
        return (f'<rect x="{halo_x}" y="{CY - halo_h / 2}" width="{halo_w}" height="{halo_h}" rx="{halo_h / 2}" fill="url(#{p}-halo)" filter="url(#{p}-blur)"/>'
                f'{rim}<rect x="{x}" y="{CY - h / 2}" width="{w}" height="{h}" rx="{h / 2}" fill="url(#{p}-pulse)" filter="url(#{p}-glow)"/>')

    # 축소 모드에선 animation:none 으로 펄스가 왼쪽 끝 기본 위치에 남으므로 통째로 숨긴다.
    body.append(D.motion_only(p,
        f'<g style="{D.anim(p, "k-run", 9, 400, D.EASE_IN_OUT)}">{pulse(40, 140, 3.5, 0, 220, 12)}</g>'
        f'<g style="{D.anim(p, "k-runr", 9, 400, D.EASE_IN_OUT)}">{pulse(50, 120, 3, 20, 180, 10)}</g>'))
    # 반짝이는 점들
    for i, x in enumerate((260, 470, 810, 1020)):
        # 라이트에서 짙은 점은 먼지처럼 읽혀 흰 채움+c2 테두리+글로우로 '빛나는 점'을 만든다.
        dot = (f'r="2.2" fill="{T["particle"]}"' if dark else f'r="2.6" fill="#FFFFFF" stroke="{c2}" stroke-width="1" filter="url(#{p}-glow)"')
        body.append(f'<circle cx="{x}" cy="{CY}" {dot} class="{p}-tw" style="animation-delay:-{i * 900}ms"/>')
    body.append("</g>")
    # 가운데 장식 — 다이아몬드 + 글로우 맥동
    body.append(f'<g transform="translate({W // 2},{CY})">'
                f'<g class="{p}-glow"><circle r="12" fill="{D.rgba(c2, 0.22 if dark else 0.14)}" filter="url(#{p}-blur)"/></g>'
                f'<rect x="-8" y="-8" width="16" height="16" rx="2.5" transform="rotate(45)" fill="{T["bg"] if dark else "#FFFFFF"}" '
                f'stroke="{c2}" stroke-width="2"/>'
                f'<rect x="-3.4" y="-3.4" width="6.8" height="6.8" rx="1.2" transform="rotate(45)" fill="{T["accent2"]}" filter="url(#{p}-glow)"/>'
                f"</g>")
    return D.svg_root(W, H, theme, "Section divider", "흐르는 딥오션 그라디언트 구분선", "".join(body), css, p)
