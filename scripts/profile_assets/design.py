"""'Deep Ocean Neon' 디자인 시스템 — 토큰과 SVG 헬퍼.

모든 에셋 모듈은 여기 있는 토큰·헬퍼만으로 그린다. 규칙과 예시는 DESIGN.md.

핵심 약속
- 접두사(prefix) = 에셋 이름(예: 'hero'). id·class·keyframes 이름은 전부 '<prefix>-' 로 시작한다.
- 모션은 CSS 애니메이션이 기본이다. prefers-reduced-motion 에서 CSS 한 줄로 모두 꺼지기 때문이다.
  SMIL(<animate>, <animateMotion>)은 CSS 로 끌 수 없으니 motion_only() 로 감싸 축소 모드에서 숨긴다.
- 등장 애니메이션은 keyframes 에 'from' 만 둔다. 끝 상태 = 요소의 기본 상태가 되므로
  애니메이션이 꺼져도(축소 모드·미지원 렌더러) 읽을 수 있는 최종 화면이 그대로 남는다.
- CSS transform 애니메이션을 거는 요소에는 transform 속성을 같이 두지 않는다(덮어쓴다).
  위치는 바깥 <g transform="translate(..)"> 로, 움직임은 안쪽 요소의 class 로.
"""

from __future__ import annotations

import math
import random
import unicodedata
from xml.sax.saxutils import escape as _xml_escape

# ---------------------------------------------------------------------------
# 팔레트 · 폰트
# ---------------------------------------------------------------------------

PALETTE = {
    "abyss": "#0B1220",
    "gh_dark": "#0d1117",
    "ocean": "#0077B6",
    "cyan": "#00B4D8",
    "aqua": "#90E0EF",
    "teal": "#14B8A6",
    "mint": "#2DD4BF",
    "violet": "#7C3AED",
    "violet_soft": "#A78BFA",
    "coral": "#FF6F61",
    "white": "#FFFFFF",
}

FONT_KO = "Pretendard, 'Apple SD Gothic Neo', 'Noto Sans KR', 'Malgun Gothic', sans-serif"
FONT_LATIN = "Inter, 'Segoe UI', 'Helvetica Neue', Arial, Pretendard, 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif"
FONT_MONO = "'JetBrains Mono', 'SFMono-Regular', Menlo, Consolas, 'Apple SD Gothic Neo', 'Noto Sans KR', monospace"
FONTS = {"ko": FONT_KO, "latin": FONT_LATIN, "mono": FONT_MONO}

# 글자 크기 규칙(viewBox 폭 1280 기준, README 에서 0.65배로 줄어든다)
SIZE = {
    "display": 76,   # 히어로 이름
    "h1": 48,
    "h2": 34,
    "h3": 26,
    "body": 20,
    "small": 18,     # 본문 최소
    "caption": 16,   # 캡션 최소
}

EASE_OUT = "cubic-bezier(.16,1,.3,1)"      # 등장(감속)
EASE_IN_OUT = "cubic-bezier(.45,0,.55,1)"  # 루프
EASE_BACK = "cubic-bezier(.34,1.56,.64,1)" # 살짝 튀는 팝

# ---------------------------------------------------------------------------
# 테마 토큰
# ---------------------------------------------------------------------------

_TOKENS = {
    "dark": {
        "theme": "dark",
        "page": "#0d1117",
        "bg": "#0B1220",
        "bg2": "#0E1E33",
        "bg3": "#0A1626",
        "surface": "rgba(144,224,239,0.045)",
        "surface_hi": "rgba(144,224,239,0.09)",
        "border": "rgba(144,224,239,0.16)",
        "border_hi": "rgba(144,224,239,0.34)",
        "highlight": "rgba(255,255,255,0.10)",
        "text": "#E8F6FC",
        "text2": "#A9C1D3",
        "muted": "#6E879D",
        "accent": "#00B4D8",
        "accent2": "#2DD4BF",
        "accent3": "#A78BFA",
        "violet": "#7C3AED",
        "coral": "#FF6F61",
        "ok": "#2DD4BF",
        "grad": ["#0077B6", "#00B4D8", "#14B8A6"],
        "grad_text": ["#90E0EF", "#00B4D8", "#2DD4BF"],
        "grad_ai": ["#00B4D8", "#7C3AED"],
        "particle": "#90E0EF",
        "line": "#48CAE4",
        "glow_opacity": 0.85,
        "blob_opacity": 0.38,
        "grid_opacity": 0.07,
        "shine": "#FFFFFF",
        "shine_opacity": 0.55,
    },
    "light": {
        "theme": "light",
        "page": "#ffffff",
        "bg": "#F6FBFF",
        "bg2": "#E9F5FC",
        "bg3": "#FFFFFF",
        "surface": "rgba(255,255,255,0.72)",
        "surface_hi": "rgba(255,255,255,0.92)",
        "border": "#D0E7F5",
        "border_hi": "#9FCBE6",
        "highlight": "rgba(255,255,255,0.95)",
        "text": "#0B1F33",
        "text2": "#4A6178",
        "muted": "#7A90A4",
        "accent": "#0077B6",
        "accent2": "#0D9488",
        "accent3": "#7C3AED",
        "violet": "#7C3AED",
        "coral": "#E8574B",
        "ok": "#0D9488",
        "grad": ["#0077B6", "#00B4D8", "#14B8A6"],
        "grad_text": ["#005F92", "#0096C7", "#0D9488"],
        "grad_ai": ["#0077B6", "#7C3AED"],
        "particle": "#0077B6",
        "line": "#0096C7",
        "glow_opacity": 0.35,
        "blob_opacity": 0.20,
        "grid_opacity": 0.10,
        "shine": "#FFFFFF",
        "shine_opacity": 0.85,
    },
}


def tokens(theme: str) -> dict:
    """테마 토큰 dict 를 돌려준다(복사본)."""
    if theme not in _TOKENS:
        raise ValueError(f"unknown theme: {theme!r}")
    t = dict(_TOKENS[theme])
    t["dark"] = theme == "dark"
    t["theme"] = theme
    return t


# ---------------------------------------------------------------------------
# 기본 유틸
# ---------------------------------------------------------------------------


def esc(s) -> str:
    """텍스트·속성값 이스케이프(&, <, >, ", ')."""
    return _xml_escape(str(s), {'"': "&quot;", "'": "&#39;"})


def n(v, digits: int = 2) -> str:
    """좌표 숫자를 짧게(불필요한 0 제거)."""
    if isinstance(v, int):
        return str(v)
    s = f"{v:.{digits}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def fmt_int(v) -> str:
    """12439 -> '12,439'. 이미 문자열이면 그대로."""
    if isinstance(v, str):
        return v
    return f"{int(round(v)):,}"


def fmt_compact(v) -> str:
    """12439 -> '12.4k', 1200000 -> '1.2M'."""
    v = float(v)
    for unit, div in (("M", 1e6), ("k", 1e3)):
        if abs(v) >= div:
            s = f"{v / div:.1f}".rstrip("0").rstrip(".")
            return s + unit
    return fmt_int(v)


def fmt_date(iso: str, sep: str = ".") -> str:
    """'2026-06-22' -> '2026.06.22', '2026-07' -> '2026.07'."""
    return str(iso).replace("-", sep)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * t


def rng(seed=7) -> random.Random:
    """결정적 난수 — 빌드마다 같은 그림이 나오게."""
    return random.Random(seed)


def hex_to_rgb(h: str):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgba(h: str, a: float) -> str:
    r, g, b = hex_to_rgb(h)
    return f"rgba({r},{g},{b},{n(a, 3)})"


def mix(c1: str, c2: str, t: float) -> str:
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return "#%02X%02X%02X" % tuple(int(round(lerp(x, y, t))) for x, y in zip(a, b))


def attrs(**kw) -> str:
    """키워드 → SVG 속성 문자열. '_' 는 '-' 로, 끝 '_' 는 제거(class_ → class). None 은 생략."""
    out = []
    for k, v in kw.items():
        if v is None or v is False:
            continue
        k = k.rstrip("_").replace("_", "-")
        if k.startswith("xlink-"):
            k = "xlink:" + k[6:]
        out.append(f'{k}="{esc(v) if not isinstance(v, (int, float)) else n(v)}"')
    return (" " + " ".join(out)) if out else ""


# ---------------------------------------------------------------------------
# 글자 폭 추정 · 줄바꿈 · 맞춤
# ---------------------------------------------------------------------------

_NARROW = set("iIl|.,:;'!`·‧")
_WIDE_SYMBOLS = set("—–→←↑↓✓✔✗✦★●○◆◇■□⏺…")


def char_em(ch: str, family: str = "latin") -> float:
    """한 글자의 폭(em). 대체 폰트로 떠도 넘치지 않게 넉넉히 잡는다."""
    if ch == "\n":
        return 0.0
    ea = unicodedata.east_asian_width(ch)
    if ea in ("W", "F"):
        return 1.0
    if ord(ch) >= 0x1F000:  # 이모지 등
        return 1.1
    if family == "mono":
        return 0.6
    if ch in _WIDE_SYMBOLS:
        return 1.0
    if ch == " ":
        return 0.3
    if ch.isdigit():
        return 0.62
    if ch in _NARROW:
        return 0.34
    if ch in "mwMW@%&":
        return 0.9
    if ch.isupper():
        return 0.7
    if ch.isalpha():
        return 0.6
    return 0.6


def text_width(s: str, size: float, family: str = "latin", weight: int = 400, letter_spacing: float = 0) -> float:
    """문자열 폭 추정(SVG 단위). weight≥600 이면 6% 가산."""
    s = str(s)
    w = sum(char_em(c, family) for c in s) * size
    if weight >= 600:
        w *= 1.06
    if letter_spacing:
        w += letter_spacing * max(len(s) - 1, 0)
    return w


def fit_size(s: str, max_w: float, size: float, min_size: float = 16, family: str = "latin",
             weight: int = 400, letter_spacing: float = 0) -> float:
    """max_w 안에 들어가는 가장 큰 글자 크기(size 부터 0.5씩 줄여 min_size 까지)."""
    cur = size
    while cur > min_size and text_width(s, cur, family, weight, letter_spacing) > max_w:
        cur -= 0.5
    return max(cur, min_size)


def truncate(s: str, max_w: float, size: float, family: str = "latin", weight: int = 400) -> str:
    """폭을 넘으면 말줄임(…)."""
    s = str(s)
    if text_width(s, size, family, weight) <= max_w:
        return s
    while s and text_width(s + "…", size, family, weight) > max_w:
        s = s[:-1]
    return s.rstrip() + "…"


def wrap(s: str, size: float, max_w: float, family: str = "latin", weight: int = 400,
         max_lines: int | None = None) -> list[str]:
    """단어(공백) 기준 줄바꿈. 한 단어가 폭보다 길면 글자 단위로 자른다.
    max_lines 를 넘으면 마지막 줄을 말줄임한다."""
    words = str(s).split()
    lines: list[str] = []
    cur = ""
    for w in words:
        cand = (cur + " " + w) if cur else w
        if text_width(cand, size, family, weight) <= max_w:
            cur = cand
            continue
        if cur:
            lines.append(cur)
            cur = ""
        while text_width(w, size, family, weight) > max_w and len(w) > 1:
            cut = len(w)
            while cut > 1 and text_width(w[:cut], size, family, weight) > max_w:
                cut -= 1
            lines.append(w[:cut])
            w = w[cut:]
        cur = w
    if cur:
        lines.append(cur)
    if max_lines and len(lines) > max_lines:
        rest = " ".join(lines[max_lines - 1:])
        lines = lines[:max_lines - 1] + [truncate(rest, max_w, size, family, weight)]
    return lines or [""]


def fit_block(s: str, max_w: float, size: float, min_size: float, max_lines: int,
              family: str = "latin", weight: int = 400) -> tuple[float, list[str]]:
    """max_lines 줄 안에 들어갈 때까지 줄바꿈 → 축소. (글자크기, 줄목록)을 돌려준다."""
    cur = size
    while True:
        lines = wrap(s, cur, max_w, family, weight)
        if len(lines) <= max_lines or cur <= min_size:
            return cur, wrap(s, cur, max_w, family, weight, max_lines)
        cur -= 0.5


def family_of(s: str) -> str:
    """한글이 섞이면 'ko', 아니면 'latin'."""
    return "ko" if any(unicodedata.east_asian_width(c) in ("W", "F") for c in str(s)) else "latin"


# ---------------------------------------------------------------------------
# 텍스트
# ---------------------------------------------------------------------------


def text(x, y, s, size=20, fill=None, weight=400, family="auto", anchor="start", cls=None,
         style=None, ls=None, opacity=None, **extra) -> str:
    """<text> 한 줄. family: 'ko' | 'latin' | 'mono' | 'auto'(한글 있으면 ko)."""
    fam = family_of(s) if family == "auto" else family
    return (f"<text{attrs(x=x, y=y, font_size=size, font_weight=weight if weight != 400 else None, fill=fill, text_anchor=anchor if anchor != 'start' else None, class_=cls, style=style, letter_spacing=ls, opacity=opacity, **extra)}"
            f' font-family="{esc(FONTS[fam])}">{esc(s)}</text>')


def text_lines(x, y, lines, size=20, line_h=None, fill=None, weight=400, family="auto", anchor="start",
               cls=None, style=None, ls=None, **extra) -> str:
    """여러 줄 <text> — 줄마다 <tspan x dy>."""
    line_h = line_h or round(size * 1.4, 1)
    joined = " ".join(lines)
    fam = family_of(joined) if family == "auto" else family
    spans = "".join(f'<tspan x="{n(x)}" dy="{n(0 if i == 0 else line_h)}">{esc(l)}</tspan>' for i, l in enumerate(lines))
    return (f"<text{attrs(x=x, y=y, font_size=size, font_weight=weight if weight != 400 else None, fill=fill, text_anchor=anchor if anchor != 'start' else None, class_=cls, style=style, letter_spacing=ls, **extra)}"
            f' font-family="{esc(FONTS[fam])}">{spans}</text>')


# ---------------------------------------------------------------------------
# defs: 그라디언트 · 필터 · 패턴
# ---------------------------------------------------------------------------


def _stops(stops) -> str:
    """stops: ['#hex', ...] (균등) 또는 [(offset, '#hex'[, opacity]), ...]."""
    out = []
    if stops and isinstance(stops[0], str):
        k = len(stops) - 1 or 1
        stops = [(i / k, c) for i, c in enumerate(stops)]
    for st in stops:
        off, color = st[0], st[1]
        op = st[2] if len(st) > 2 else None
        out.append(f'<stop offset="{n(off, 3)}" stop-color="{color}"' + (f' stop-opacity="{n(op, 3)}"' if op is not None else "") + "/>")
    return "".join(out)


def linear_gradient(id, stops, x1=0, y1=0, x2=1, y2=0, units=None, spread=None, transform=None) -> str:
    """선형 그라디언트. units='userSpaceOnUse' 면 좌표는 SVG 단위."""
    return (f"<linearGradient{attrs(id=id, x1=x1, y1=y1, x2=x2, y2=y2, gradientUnits=units, spreadMethod=spread, gradientTransform=transform)}>"
            f"{_stops(stops)}</linearGradient>")


def radial_gradient(id, stops, cx=0.5, cy=0.5, r=0.5, fx=None, fy=None, units=None) -> str:
    return (f"<radialGradient{attrs(id=id, cx=cx, cy=cy, r=r, fx=fx, fy=fy, gradientUnits=units)}>"
            f"{_stops(stops)}</radialGradient>")


def flow_gradient(id, colors, period=640, vertical=False) -> str:
    """흐르는 그라디언트용 반복 그라디언트(userSpaceOnUse, spread=repeat).
    첫 색을 끝에 다시 붙여 이음매가 없다. flow_rect() 와 함께 쓴다."""
    cols = list(colors) + [colors[0]]
    if vertical:
        return linear_gradient(id, cols, 0, 0, 0, period, units="userSpaceOnUse", spread="repeat")
    return linear_gradient(id, cols, 0, 0, period, 0, units="userSpaceOnUse", spread="repeat")


def glow_filter(id, std=6, strength=1.0) -> str:
    """원본 + 흐린 사본을 겹치는 네온 글로우. strength 는 흐린 층 불투명도."""
    return (f'<filter id="{id}" x="-50%" y="-50%" width="200%" height="200%" color-interpolation-filters="sRGB">'
            f'<feGaussianBlur in="SourceGraphic" stdDeviation="{n(std)}" result="b"/>'
            f'<feComponentTransfer in="b" result="bb"><feFuncA type="linear" slope="{n(strength)}"/></feComponentTransfer>'
            f'<feMerge><feMergeNode in="bb"/><feMergeNode in="SourceGraphic"/></feMerge></filter>')


def blur_filter(id, std=20) -> str:
    """순수 블러(오로라 덩어리·빛 번짐)."""
    return (f'<filter id="{id}" x="-50%" y="-50%" width="200%" height="200%">'
            f'<feGaussianBlur stdDeviation="{n(std)}"/></filter>')


def shadow_filter(id, theme, dy=8, std=14) -> str:
    """카드 그림자. 다크는 시안 기운, 라이트는 남색 그림자."""
    color = "#00B4D8" if theme == "dark" else "#0B3A5C"
    op = 0.18 if theme == "dark" else 0.12
    return (f'<filter id="{id}" x="-20%" y="-20%" width="140%" height="160%">'
            f'<feDropShadow dx="0" dy="{n(dy)}" stdDeviation="{n(std)}" flood-color="{color}" flood-opacity="{n(op)}"/></filter>')


def dot_grid_pattern(id, theme, gap=24, r=1.1) -> str:
    T = tokens(theme)
    return (f'<pattern id="{id}" width="{gap}" height="{gap}" patternUnits="userSpaceOnUse">'
            f'<circle cx="{n(gap / 2)}" cy="{n(gap / 2)}" r="{n(r)}" fill="{T["particle"]}" opacity="{n(T["grid_opacity"] * 4, 3)}"/></pattern>')


def fade_mask(id, w, h, axis="x", edge=0.12) -> str:
    """양 끝이 투명해지는 마스크(선·띠가 자연스럽게 사라지게)."""
    gid = id + "-g"
    x2, y2 = ("1", "0") if axis == "x" else ("0", "1")
    grad = linear_gradient(gid, [(0, "#fff", 0), (edge, "#fff", 1), (1 - edge, "#fff", 1), (1, "#fff", 0)], 0, 0, x2, y2)
    return f'{grad}<mask id="{id}" maskUnits="userSpaceOnUse" x="0" y="0" width="{n(w)}" height="{n(h)}"><rect width="{n(w)}" height="{n(h)}" fill="url(#{gid})"/></mask>'


def defs(*items) -> str:
    return "<defs>" + "".join(i for i in items if i) + "</defs>"


# ---------------------------------------------------------------------------
# 카드 · 글래스 · 칩
# ---------------------------------------------------------------------------


def card(w, h, theme, prefix, r=20, x=0, y=0, glow_edge=True) -> str:
    """에셋 전체 배경 카드(둥근 사각 + 은은한 테두리 + 위쪽 안쪽 하이라이트).
    어느 GitHub 배경 위에서도 완결된다. 자체 defs 포함."""
    T = tokens(theme)
    p = prefix
    sw = 1.5
    ix, iy, iw, ih = x + sw / 2, y + sw / 2, w - sw, h - sw
    fill = linear_gradient(f"{p}-card-fill", [T["bg"], T["bg2"], T["bg3"]], 0, 0, 1, 1)
    if glow_edge:
        if T["dark"]:
            st = [(0, "#90E0EF", 0.38), (0.35, "#00B4D8", 0.14), (0.7, "#7C3AED", 0.18), (1, "#14B8A6", 0.34)]
        else:
            st = [(0, "#9FCBE6", 1), (0.5, "#D0E7F5", 1), (1, "#8FD3C9", 1)]
        stroke_grad = linear_gradient(f"{p}-card-stroke", st, 0, 0, 1, 1)
        stroke = f"url(#{p}-card-stroke)"
    else:
        stroke_grad, stroke = "", T["border"]
    hl = linear_gradient(f"{p}-card-hl", [(0, T["highlight"], 0), (0.5, T["highlight"], 1), (1, T["highlight"], 0)])
    return (defs(fill, stroke_grad, hl)
            + f'<rect x="{n(ix)}" y="{n(iy)}" width="{n(iw)}" height="{n(ih)}" rx="{r}" fill="url(#{p}-card-fill)" stroke="{stroke}" stroke-width="{sw}"/>'
            + f'<path d="M{n(ix + r)} {n(iy + 1.2)}H{n(ix + iw - r)}" stroke="url(#{p}-card-hl)" stroke-width="1" fill="none"/>')


def card_clip(id, w, h, r=20, x=0, y=0) -> str:
    """카드 모양 clipPath — 배경 장식이 둥근 모서리 밖으로 새지 않게."""
    return f'<clipPath id="{id}"><rect x="{n(x + 0.75)}" y="{n(y + 0.75)}" width="{n(w - 1.5)}" height="{n(h - 1.5)}" rx="{r}"/></clipPath>'


def glass_defs(theme, prefix) -> str:
    """glass() 가 참조하는 공통 defs. 에셋당 한 번 넣는다."""
    T = tokens(theme)
    p = prefix
    if T["dark"]:
        fill = linear_gradient(f"{p}-glass-fill", [(0, "#90E0EF", 0.085), (1, "#90E0EF", 0.025)], 0, 0, 0, 1)
        stroke = linear_gradient(f"{p}-glass-stroke", [(0, "#90E0EF", 0.34), (0.5, "#90E0EF", 0.10), (1, "#2DD4BF", 0.24)], 0, 0, 1, 1)
    else:
        fill = linear_gradient(f"{p}-glass-fill", [(0, "#FFFFFF", 0.95), (1, "#F2F9FE", 0.85)], 0, 0, 0, 1)
        stroke = linear_gradient(f"{p}-glass-stroke", [(0, "#B9DCF0", 1), (0.5, "#D0E7F5", 1), (1, "#A8DCD3", 1)], 0, 0, 1, 1)
    hl = linear_gradient(f"{p}-glass-hl", [(0, T["highlight"], 0), (0.5, T["highlight"], 1), (1, T["highlight"], 0)])
    return fill + stroke + hl + shadow_filter(f"{p}-glass-shadow", theme)


def glass(x, y, w, h, theme, prefix, r=20, shadow=True, cls=None, style=None) -> str:
    """글래스모피즘 패널(반투명 채움 + 그라디언트 테두리 + 안쪽 위 하이라이트 선).
    glass_defs(theme, prefix) 를 defs 에 먼저 넣어야 한다."""
    p = prefix
    flt = f' filter="url(#{p}-glass-shadow)"' if shadow else ""
    return (f"<g{attrs(class_=cls, style=style)}>"
            f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{r}" fill="url(#{p}-glass-fill)" stroke="url(#{p}-glass-stroke)" stroke-width="1.5"{flt}/>'
            f'<path d="M{n(x + r)} {n(y + 1.5)}H{n(x + w - r)}" stroke="url(#{p}-glass-hl)" stroke-width="1" fill="none"/>'
            "</g>")


def chip(x, y, label, theme, size=18, variant="accent", h=None, pad=None, cls=None, style=None,
         family="auto", dot=False) -> tuple[str, float]:
    """알약 모양 칩. (svg, 폭) 을 돌려준다. variant: accent | teal | violet | neutral | coral.
    dot=True 면 왼쪽에 작은 점(상태 표시)."""
    T = tokens(theme)
    color = {"accent": T["accent"], "teal": T["accent2"], "violet": T["accent3"],
             "neutral": T["text2"], "coral": T["coral"]}.get(variant, T["accent"])
    fam = family_of(label) if family == "auto" else family
    h = h or round(size * 2)
    pad = pad if pad is not None else round(size * 0.8)
    dot_w = size * 0.9 if dot else 0
    tw = text_width(label, size, fam, 600)
    w = tw + pad * 2 + dot_w
    fill_op = 0.12 if T["dark"] else 0.08
    stroke_op = 0.45 if T["dark"] else 0.35
    txt_fill = mix(color, "#FFFFFF", 0.35) if T["dark"] else mix(color, "#000000", 0.12)
    parts = [f"<g{attrs(class_=cls, style=style)}>",
             f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" rx="{n(h / 2)}" fill="{rgba(color, fill_op)}" stroke="{rgba(color, stroke_op)}" stroke-width="1.2"/>']
    if dot:
        parts.append(f'<circle cx="{n(x + pad + size * 0.25)}" cy="{n(y + h / 2)}" r="{n(size * 0.22)}" fill="{color}"/>')
    parts.append(text(x + pad + dot_w + tw / 2, y + h / 2 + size * 0.35, label, size, txt_fill, 600, fam, "middle"))
    parts.append("</g>")
    return "".join(parts), w


def eyebrow(prefix, x, y, label, theme, variant="teal", icon="dot", size=16, max_w=None, anchor="start",
            cls="fd", delay_ms=60) -> tuple[str, float]:
    """섹션 머리 위 모노 라벨 칩(높이 32). 여러 에셋이 같은 모양을 쓰도록 한 곳에 둔다.
    icon: 'dot'(맥동 상태 점) | 'sparkle'(AI 반짝임). anchor='end' 면 x 가 오른쪽 끝. (svg, 폭)."""
    T = tokens(theme)
    color = {"teal": T["accent2"], "violet": T["accent3"], "accent": T["accent"]}.get(variant, T["accent2"])
    h, ls = 32, 2
    tx_off = 36 if icon == "sparkle" else 34
    if max_w is not None and text_width(label, size, "mono", 600, ls) > max_w - tx_off - 16:
        # truncate 는 자간을 모른다 → 자간 포함 폭이 들어올 때까지 직접 줄인다
        room = max_w - tx_off - 16
        s = label
        while s and text_width(s.rstrip() + "…", size, "mono", 600, ls) > room:
            s = s[:-1]
        label = s.rstrip() + "…"
    w = tx_off + text_width(label, size, "mono", 600, ls) + 16
    x0 = x - w if anchor == "end" else x
    cy = y + h / 2
    if icon == "sparkle":
        mark = (f'<path d="{sparkle_path(x0 + 20, cy, 8, 0.24)}" fill="{color}" class="{prefix}-tw" '
                f'style="animation-duration:3s"/>')
    else:
        mark = (f'<circle cx="{n(x0 + 19)}" cy="{n(cy)}" r="7" fill="{color}" opacity="0.35" class="{prefix}-pulse"/>'
                f'<circle cx="{n(x0 + 19)}" cy="{n(cy)}" r="3.8" fill="{color}"/>')
    svg = (f'<g class="{prefix}-{cls}" style="{delay(delay_ms)}">'
           f'<rect x="{n(x0)}" y="{n(y)}" width="{n(w)}" height="{h}" rx="16" '
           f'fill="{rgba(color, 0.11 if T["dark"] else 0.07)}" stroke="{rgba(color, 0.42)}" stroke-width="1.2"/>'
           + mark + text(x0 + tx_off, cy + 5.5, label, size, color, 600, "mono", ls=ls) + "</g>")
    return svg, w


def chips_row(x, y, labels, theme, max_w, size=18, gap=10, variants=None, cls_fn=None) -> tuple[str, float]:
    """칩을 한 줄로 배치. 넘치면 글자를 16까지 줄이고, 그래도 넘치면 '+N' 칩으로 접는다.
    cls_fn(i) -> (class, style) 로 칩마다 등장 애니메이션을 줄 수 있다. (svg, 실제 폭)."""
    variants = variants or ["accent", "teal", "accent", "teal", "accent", "violet"]

    def total(sz, items):
        h = round(sz * 2)
        pad = round(sz * 0.8)
        return sum(text_width(l, sz, family_of(l), 600) + pad * 2 for l in items) + gap * max(len(items) - 1, 0), h

    items = list(labels)
    sz = size
    while sz > 16 and total(sz, items)[0] > max_w:
        sz -= 0.5
    hidden = 0
    while len(items) > 1 and total(sz, items + ([f"+{hidden}"] if hidden else []))[0] > max_w:
        items.pop()
        hidden += 1
    if hidden:
        items.append(f"+{hidden}")
    out, cx = [], x
    for i, l in enumerate(items):
        c, s = cls_fn(i) if cls_fn else (None, None)
        svg, w = chip(cx, y, l, theme, sz, "neutral" if l.startswith("+") and hidden else variants[i % len(variants)], cls=c, style=s)
        out.append(svg)
        cx += w + gap
    return "".join(out), cx - gap - x


# ---------------------------------------------------------------------------
# 모션 — 공통 keyframes · 유틸리티 class
# ---------------------------------------------------------------------------

# 유틸리티 class 이름(접두사 뒤에 붙는다). build 의 애니메이션 요소 개수 검사가 이 목록을 쓴다.
ANIM_CLASSES = ["fu", "fi", "fd", "pop", "draw", "type", "glow", "tw", "float", "floats", "spin", "spinr",
                "pulse", "blink", "breathe", "sway", "odo"]


def base_css(prefix: str) -> str:
    """공통 keyframes + 유틸리티 class. svg_root 가 자동으로 넣는다.

    등장(1회, 최종 상태로 멈춤 — 'from' 만 있는 keyframes):
      .p-fu  fade-up   0.9s   (아래 16px 에서 떠오름)
      .p-fi  fade-in   1.0s
      .p-fd  fade-down 0.9s
      .p-pop scale-in  0.7s   (fill-box 중심, 살짝 튐)
      .p-draw 선 그리기 1.6s  (path 에 pathLength="1" 필수)
      .p-type 타이핑   1.4s   (clipPath 안 사각형을 scaleX 로 펼침 — typewriter() 사용)
      .p-odo 롤링 숫자 1.8s   (odometer() 가 씀)
    루프(배경):
      .p-glow 글로우 맥동 4s · .p-tw 반짝임 3.6s · .p-float 둥실 7s · .p-floats 큰 덩어리 표류 14s
      .p-spin 회전 36s · .p-spinr 역회전 28s (로컬 원점 기준 — translate 된 <g> 안에 둔다)
      .p-pulse 크기 맥동 3.2s (fill-box 중심) · .p-breathe 불투명도 숨쉬기 6s · .p-sway 좌우 흔들림 9s
      .p-blink 커서 깜빡임 1.1s(초당 1회 — 3Hz 제한 안쪽)
    지연은 style="animation-delay:XXXms" 또는 delay(ms) 로 준다.
    """
    p = prefix
    return f"""
@keyframes {p}-k-fu{{from{{opacity:0;transform:translateY(16px)}}}}
@keyframes {p}-k-fd{{from{{opacity:0;transform:translateY(-14px)}}}}
@keyframes {p}-k-fi{{from{{opacity:0}}}}
@keyframes {p}-k-pop{{from{{opacity:0;transform:scale(.6)}}}}
@keyframes {p}-k-draw{{from{{stroke-dashoffset:1}}}}
@keyframes {p}-k-type{{from{{transform:scaleX(0)}}}}
@keyframes {p}-k-odo{{from{{transform:translateY(0)}}}}
@keyframes {p}-k-glow{{0%,100%{{opacity:.55}}50%{{opacity:1}}}}
@keyframes {p}-k-tw{{0%,100%{{opacity:.25}}50%{{opacity:1}}}}
@keyframes {p}-k-float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-7px)}}}}
@keyframes {p}-k-floats{{0%,100%{{transform:translate(0,0)}}33%{{transform:translate(28px,-14px)}}66%{{transform:translate(-18px,12px)}}}}
@keyframes {p}-k-spin{{to{{transform:rotate(360deg)}}}}
@keyframes {p}-k-spinr{{to{{transform:rotate(-360deg)}}}}
@keyframes {p}-k-pulse{{0%,100%{{transform:scale(1)}}50%{{transform:scale(1.12)}}}}
@keyframes {p}-k-breathe{{0%,100%{{opacity:.35}}50%{{opacity:.8}}}}
@keyframes {p}-k-sway{{0%,100%{{transform:translateX(0)}}50%{{transform:translateX(-22px)}}}}
@keyframes {p}-k-blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
.{p}-fu{{animation:{p}-k-fu .9s {EASE_OUT} both}}
.{p}-fd{{animation:{p}-k-fd .9s {EASE_OUT} both}}
.{p}-fi{{animation:{p}-k-fi 1s ease-out both}}
.{p}-pop{{animation:{p}-k-pop .7s {EASE_BACK} both;transform-box:fill-box;transform-origin:center}}
.{p}-draw{{stroke-dasharray:1;stroke-dashoffset:0;animation:{p}-k-draw 1.6s {EASE_OUT} both}}
.{p}-type{{animation:{p}-k-type 1.4s steps(28,end) both;transform-box:fill-box;transform-origin:0 0}}
.{p}-odo{{animation:{p}-k-odo 1.8s {EASE_OUT} both}}
.{p}-glow{{animation:{p}-k-glow 4s {EASE_IN_OUT} infinite}}
.{p}-tw{{animation:{p}-k-tw 3.6s {EASE_IN_OUT} infinite}}
.{p}-float{{animation:{p}-k-float 7s {EASE_IN_OUT} infinite}}
.{p}-floats{{animation:{p}-k-floats 14s {EASE_IN_OUT} infinite}}
.{p}-spin{{animation:{p}-k-spin 36s linear infinite}}
.{p}-spinr{{animation:{p}-k-spinr 28s linear infinite}}
.{p}-pulse{{animation:{p}-k-pulse 3.2s {EASE_IN_OUT} infinite;transform-box:fill-box;transform-origin:center}}
.{p}-breathe{{animation:{p}-k-breathe 6s {EASE_IN_OUT} infinite}}
.{p}-sway{{animation:{p}-k-sway 9s {EASE_IN_OUT} infinite}}
.{p}-blink{{animation:{p}-k-blink 1.1s step-end infinite}}
"""


def reduced_motion_css(prefix: str) -> str:
    """prefers-reduced-motion: 모든 CSS 애니메이션을 끄고(=최종 상태) SMIL 영역(.p-m)은 숨긴다.
    .p-s 는 축소 모드에서만 보이는 정적 대체물."""
    p = prefix
    return (f"\n.{p}-s{{display:none}}"
            f"\n@media (prefers-reduced-motion: reduce){{*{{animation:none!important;transition:none!important}}"
            f".{p}-m{{display:none!important}}.{p}-s{{display:inline!important}}}}\n")


def delay(ms) -> str:
    """style 속성용 지연 문자열."""
    return f"animation-delay:{int(ms)}ms"


def anim(prefix, name, dur, delay_ms=0, ease="linear", iteration="infinite", fill="both", direction=None) -> str:
    """임의 keyframes 를 거는 style 문자열. name 은 접두사 없이(예: 'k-wave1')."""
    d = f" {direction}" if direction else ""
    return f"animation:{prefix}-{name} {dur}s {ease} {int(delay_ms)}ms {iteration}{d} {fill}"


def stagger(i, base=0, step=90) -> str:
    """순차 등장 지연: base + i*step ms."""
    return delay(base + i * step)


def keyframes(prefix, name, body) -> str:
    """사용자 정의 keyframes. name 은 접두사 없이."""
    return f"@keyframes {prefix}-{name}{{{body}}}\n"


def translate_loop_css(prefix, name, dx=0, dy=0) -> str:
    """(0,0) → (dx,dy) 로 끝없이 이동하는 keyframes. 주기 패턴(물결 등)을 이음매 없이 흘린다."""
    return keyframes(prefix, name, f"from{{transform:translate(0,0)}}to{{transform:translate({n(dx)}px,{n(dy)}px)}}")


def shimmer_css(prefix, name, start_x, end_x, active=0.28) -> str:
    """빛띠가 start_x → end_x 로 스치고(주기의 앞 active 비율) 나머지는 쉬는 keyframes.
    style=anim(prefix, name, 7, delay_ms, EASE_IN_OUT) 로 띠 요소에 건다."""
    pct = int(active * 100)
    return keyframes(prefix, name, f"0%{{transform:translateX({n(start_x)}px)}}{pct}%,100%{{transform:translateX({n(end_x)}px)}}")


def motion_only(prefix, content) -> str:
    """축소 모드에서 숨길 장식(SMIL 포함)을 감싼다."""
    return f'<g class="{prefix}-m">{content}</g>'


def static_only(prefix, content) -> str:
    """축소 모드에서만 보일 정적 대체물."""
    return f'<g class="{prefix}-s">{content}</g>'


# ---------------------------------------------------------------------------
# 복합 모션 헬퍼
# ---------------------------------------------------------------------------


def flow_rect(prefix, x, y, w, h, grad_id, period, dur=8, clip_id=None, mask_id=None, reverse=False, opacity=None) -> str:
    """흐르는 그라디언트 띠. flow_gradient(grad_id, ..., period) 와 짝.
    폭 w+period 의 사각을 period 만큼 계속 밀어 그라디언트가 흐르는 것처럼 보인다(CSS → 축소 모드에서 멈춤).
    keyframes '<p>-k-flow<period>' 는 flow_css(prefix, period) 로 style 에 넣는다."""
    kf = f"k-flow{int(period)}{'r' if reverse else ''}"
    wrap_attr = attrs(clip_path=f"url(#{clip_id})" if clip_id else None, mask=f"url(#{mask_id})" if mask_id else None, opacity=opacity)
    rx = x - period if not reverse else x - period
    return (f"<g{wrap_attr}><rect x=\"{n(rx)}\" y=\"{n(y)}\" width=\"{n(w + period * 2)}\" height=\"{n(h)}\" fill=\"url(#{grad_id})\""
            f" style=\"{anim(prefix, kf, dur)}\"/></g>")


def flow_css(prefix, period, reverse=False) -> str:
    kf = f"k-flow{int(period)}{'r' if reverse else ''}"
    return translate_loop_css(prefix, kf, -period if reverse else period, 0)


def odometer(prefix, x, y, value: str, size, fill, family="latin", weight=800, delay_ms=0, step_ms=70,
             anchor="start", clip_id=None, spins=1) -> str:
    """롤링 숫자(슬롯머신처럼 굴러 최종값에 멈춘다). 숫자가 아닌 글자(, . + % k)는 고정.
    clip_id: 이 숫자 전용 고유 id(필수, 예 'stats-odo3'). y 는 글자 기준선.
    축소 모드·애니메이션 미지원이면 최종값이 그대로 보인다(기본 상태 = 최종값)."""
    value = str(value)
    fam = FONTS[family]
    lh = size * 1.2
    total_w = text_width(value, size, family, weight)
    x0 = x - total_w if anchor == "end" else (x - total_w / 2 if anchor == "middle" else x)
    clip_id = clip_id or f"{prefix}-odo"
    top = y - size * 0.95
    parts = [f'<clipPath id="{clip_id}"><rect x="{n(x0 - 4)}" y="{n(top)}" width="{n(total_w + 8)}" height="{n(size * 1.22)}"/></clipPath>',
             f'<g clip-path="url(#{clip_id})" font-family="{esc(fam)}" font-size="{n(size)}" font-weight="{weight}" fill="{fill}">']
    cx = x0
    di = 0
    for ch in value:
        cw = char_em(ch, family) * size * (1.06 if weight >= 600 else 1)
        if ch.isdigit():
            d = int(ch)
            seq = [str(k % 10) for k in range(0, 10 * spins + d + 1)]
            final = (len(seq) - 1) * lh
            spans = "".join(f'<tspan x="{n(cx)}" y="{n(y + i * lh)}">{s}</tspan>' for i, s in enumerate(seq))
            parts.append(f'<text class="{prefix}-odo" style="transform:translateY(-{n(final)}px);animation-delay:{int(delay_ms + di * step_ms)}ms">{spans}</text>')
            di += 1
        else:
            parts.append(f'<text x="{n(cx)}" y="{n(y)}">{esc(ch)}</text>')
        cx += cw
    parts.append("</g>")
    return "".join(parts)


def typewriter(prefix, uid, x, y, s, size, fill, family="mono", weight=500, start_ms=0, cps=28,
               caret=True, caret_fill=None) -> tuple[str, str, float]:
    """한 글자씩 타이핑되는 텍스트 + 따라오는 깜빡 커서. (svg, 추가 css, 끝나는 시각 ms).
    uid: 이 텍스트 고유 이름(id 접두사 뒤에 붙음). 기본 상태는 전부 보이는 최종 화면.
    SVG 텍스트에 clip-path:inset 애니메이션은 Chrome 에서 먹지 않아, clipPath 사각형을 scaleX 로 연다."""
    s = str(s)
    steps = max(len(s), 1)
    dur = max(0.6, steps / cps)
    tw = text_width(s, size, family, weight)
    cid = f"{prefix}-{uid}-tc"
    top = y - size * 1.05
    t = f"{dur:.2f}s steps({steps},end) {int(start_ms)}ms both"
    out = (f'<clipPath id="{cid}"><rect x="{n(x - 2)}" y="{n(top)}" width="{n(tw + size * 0.9)}" height="{n(size * 1.45)}" '
           f'class="{prefix}-type" style="animation:{prefix}-k-type {t}"/></clipPath>'
           f'<g clip-path="url(#{cid})">' + text(x, y, s, size, fill, weight, family) + "</g>")
    css = ""
    end_ms = int(start_ms + dur * 1000)
    if caret:
        css = keyframes(prefix, f"k-caret-{uid}", f"from{{transform:translateX(-{n(tw)}px)}}")
        out += (f'<rect x="{n(x + tw + 3)}" y="{n(y - size * 0.82)}" width="{n(size * 0.5)}" height="{n(size)}" rx="1.5" '
                f'fill="{caret_fill or fill}" opacity="0.85" style="animation:{prefix}-k-caret-{uid} {t},'
                f'{prefix}-k-blink 1.1s step-end {end_ms}ms infinite"/>')
    return out, css, end_ms


def sparkle_path(cx, cy, r, waist=0.22) -> str:
    """4갈래 반짝임(✦) path d."""
    w = r * waist
    return (f"M{n(cx)} {n(cy - r)}C{n(cx + w * 0.4)} {n(cy - w)} {n(cx + w)} {n(cy - w * 0.4)} {n(cx + r)} {n(cy)}"
            f"C{n(cx + w)} {n(cy + w * 0.4)} {n(cx + w * 0.4)} {n(cy + w)} {n(cx)} {n(cy + r)}"
            f"C{n(cx - w * 0.4)} {n(cy + w)} {n(cx - w)} {n(cy + w * 0.4)} {n(cx - r)} {n(cy)}"
            f"C{n(cx - w)} {n(cy - w * 0.4)} {n(cx - w * 0.4)} {n(cy - w)} {n(cx)} {n(cy - r)}Z")


def wave_path(width, period, amp, base_y, bottom, phase=0.0, samples_per_period=16) -> str:
    """주기 period 의 사인 물결(채움용 닫힌 path). 폭 width+period 로 그려 translate_loop 로 흘린다."""
    pts = []
    total = width + period
    steps = int(total / period * samples_per_period)
    for i in range(steps + 1):
        x = total * i / steps
        y = base_y + amp * math.sin((x / period) * 2 * math.pi + phase)
        pts.append((x, y))
    d = f"M0 {n(bottom)}L{n(pts[0][0])} {n(pts[0][1])}"
    # 부드럽게: 점 사이를 2차 베지어 중점 보간
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        d += f"Q{n(x1)} {n(y1)} {n((x1 + x2) / 2)} {n((y1 + y2) / 2)}"
    d += f"L{n(total)} {n(pts[-1][1])}L{n(total)} {n(bottom)}Z"
    return d


def wave_line(width, period, amp, base_y, phase=0.0, samples_per_period=16) -> str:
    """wave_path 의 윗선만(네온 테두리용 열린 path)."""
    pts = []
    total = width + period
    steps = int(total / period * samples_per_period)
    for i in range(steps + 1):
        x = total * i / steps
        pts.append((x, base_y + amp * math.sin((x / period) * 2 * math.pi + phase)))
    d = f"M{n(pts[0][0])} {n(pts[0][1])}"
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        d += f"Q{n(x1)} {n(y1)} {n((x1 + x2) / 2)} {n((y1 + y2) / 2)}"
    return d


def constellation(prefix, theme, box, count=30, seed=7, link_dist=160, max_links=2, dim_box=None,
                  dim=0.35, r_range=(1.1, 2.6)) -> str:
    """별자리 파티클 네트워크(노드 반짝임 + 연결선 맥동). box=(x,y,w,h).
    dim_box 영역(글자 자리) 안 노드는 dim 배로 흐리게."""
    T = tokens(theme)
    R = rng(seed)
    bx, by, bw, bh = box
    nodes = []
    tries = 0
    while len(nodes) < count and tries < count * 40:
        tries += 1
        x, y = bx + R.random() * bw, by + R.random() * bh
        if all((x - a) ** 2 + (y - b) ** 2 > 48 ** 2 for a, b, _ in nodes):
            nodes.append((x, y, R.uniform(*r_range)))

    def dimmed(x, y):
        if not dim_box:
            return 1.0
        dx, dy, dw, dh = dim_box
        return dim if (dx <= x <= dx + dw and dy <= y <= dy + dh) else 1.0

    links = set()
    for i, (x, y, _) in enumerate(nodes):
        near = sorted(((math.hypot(x - a, y - b), j) for j, (a, b, _) in enumerate(nodes) if j != i))[:max_links]
        for d, j in near:
            if d < link_dist:
                links.add((min(i, j), max(i, j)))
    line_op = 0.42 if T["dark"] else 0.26
    out = [f'<g stroke="{T["line"]}" stroke-width="1" fill="none">']
    for k, (i, j) in enumerate(sorted(links)):
        (x1, y1, _), (x2, y2, _) = nodes[i], nodes[j]
        op = line_op * min(dimmed(x1, y1), dimmed(x2, y2))
        # 애니메이션이 opacity 를 덮어쓰므로 정적 불투명도는 바깥 <g> 에 둔다
        out.append(f'<g opacity="{n(op, 3)}"><path d="M{n(x1)} {n(y1)}L{n(x2)} {n(y2)}" class="{prefix}-breathe" style="animation-delay:-{(k * 730) % 6000}ms"/></g>')
    out.append("</g>")
    out.append(f'<g fill="{T["particle"]}">')
    for k, (x, y, r) in enumerate(nodes):
        op = (0.95 if T["dark"] else 0.7) * dimmed(x, y)
        out.append(f'<g opacity="{n(op, 3)}"><circle cx="{n(x)}" cy="{n(y)}" r="{n(r)}" class="{prefix}-tw" style="animation-delay:-{(k * 517) % 3600}ms"/></g>')
    out.append("</g>")
    return "".join(out)


# ---------------------------------------------------------------------------
# 루트
# ---------------------------------------------------------------------------


def svg_root(w, h, theme, title, desc, body, style="", prefix="asset", include_base=True) -> str:
    """루트 <svg>. width·height·viewBox·role·aria-label·<title>·<desc> 포함.
    style 에는 이 에셋 전용 CSS(추가 keyframes 등)를 넣는다. base_css 와 reduced-motion 은 자동 포함."""
    css = (base_css(prefix) if include_base else "") + (style or "") + reduced_motion_css(prefix)
    css = "\n".join(line.strip() for line in css.strip().splitlines() if line.strip())
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{n(w)}" height="{n(h)}" viewBox="0 0 {n(w)} {n(h)}" '
            f'fill="none" role="img" aria-label="{esc(title)}" aria-labelledby="{prefix}-title {prefix}-desc">'
            f'<title id="{prefix}-title">{esc(title)}</title><desc id="{prefix}-desc">{esc(desc)}</desc>'
            f"<style>{css}</style>{body}</svg>\n")
