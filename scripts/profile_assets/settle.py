"""무한 반복 애니메이션을 정해진 시간 뒤 멈추게 바꾸는 후처리.

GitHub 프로필은 SVG 8장을 한 화면에 띄운다. 무한 루프 수백 개가 블러 필터 위에서 쉬지 않고 다시
그려지면 탭 하나가 CPU 코어 4개가량을 계속 쓴다(실측 10초당 CPU 38초). 루프를 LOOP_S 초 남짓만
돌리고 멈추면 그 뒤로는 정지 화면이라 다시 그릴 일이 없다.
모듈마다 고치지 않고 빌드 끝에서 한 번에 바꾸는 이유: 새 모듈이 infinite 를 써도 자동으로 적용되게.
"""

from __future__ import annotations

import math
import re

LOOP_S = 15.0

_DECL = re.compile(r"(animation\s*:\s*)([^;}\"]+)")
_TIME = re.compile(r"(?<![\w.-])(\d*\.?\d+)(ms|s)\b")
_SMIL = re.compile(r"<(animate|animateMotion|animateTransform|animateColor)\b[^>]*>")


def _split_top(value: str) -> list[str]:
    """쉼표로 나누되 cubic-bezier(...) 괄호 안 쉼표는 건너뛴다."""
    parts, depth, cur = [], 0, ""
    for ch in value:
        depth += ch == "("
        depth -= ch == ")"
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return parts


def _count(dur_s: float, loop_s: float = LOOP_S) -> str:
    """짧은 루프는 정수 바퀴(쉼 상태에서 끝남), 한 바퀴가 LOOP_S 보다 긴 루프는 소수 바퀴로 LOOP_S 에 맞춰 끊는다."""
    if dur_s <= 0 or loop_s <= 0:  # loop_s 0 = 길이와 상관없이 딱 한 바퀴
        return "1"
    if dur_s <= loop_s:
        return str(math.floor(loop_s / dur_s))
    return f"{loop_s / dur_s:.3f}".rstrip("0").rstrip(".")


def _css_part(part: str, loop_s: float) -> str:
    if "infinite" not in part:
        return part
    m = _TIME.search(part)  # 단축 표기에서 처음 나오는 시간이 재생 시간
    dur = float(m.group(1)) / (1000 if m.group(2) == "ms" else 1) if m else loop_s
    return re.sub(r"\binfinite\b", _count(dur, loop_s), part)


def _smil_tag(tag: str, loop_s: float) -> str:
    if 'repeatCount="indefinite"' not in tag:
        return tag
    m = re.search(r'\bdur="(\d*\.?\d+)(ms|s)?"', tag)
    dur = float(m.group(1)) / (1000 if m.group(2) == "ms" else 1) if m else loop_s
    cnt = _count(dur, loop_s)
    tag = tag.replace('repeatCount="indefinite"', f'repeatCount="{cnt}"')
    # 끝나면 기본값(remove)은 원래 속성으로 튀어 돌아간다 — 마지막 프레임에 멈춰 두기
    if not re.search(r'\sfill="', tag):
        tag = tag.replace(f'repeatCount="{cnt}"', f'repeatCount="{cnt}" fill="freeze"', 1)
    return tag


_LOOP_CLASS = re.compile(r"\.([\w-]+)\{animation:[^}]*\binfinite\b")
_TAG = re.compile(r"<[a-zA-Z][^>]*>")


def _override_tag(tag: str, loop_classes: set[str], loop_s: float) -> str:
    """클래스 루프의 재생 시간을 style 의 animation-duration 으로 덮어쓴 요소 — 클래스에서 계산한 횟수는
    원래 시간 기준이라 90s 로 늘린 회전은 몇십 초를 더 돈다. 덮어쓴 시간으로 횟수를 다시 박는다."""
    cm = re.search(r'\bclass="([^"]*)"', tag)
    sm = re.search(r'\bstyle="([^"]*)"', tag)
    if not cm or not sm or not loop_classes.intersection(cm.group(1).split()):
        return tag
    style = sm.group(1)
    dm = re.search(r"animation-duration\s*:\s*(\d*\.?\d+)(ms|s)", style)
    if not dm or re.search(r"animation\s*:|animation-iteration-count", style):
        return tag
    dur = float(dm.group(1)) / (1000 if dm.group(2) == "ms" else 1)
    new_style = style.rstrip("; ") + f";animation-iteration-count:{_count(dur, loop_s)}"
    return tag[:sm.start(1)] + new_style + tag[sm.end(1):]


def settle(svg: str, loop_s: float = LOOP_S) -> str:
    loop_classes = set(_LOOP_CLASS.findall(svg))
    svg = _TAG.sub(lambda m: _override_tag(m.group(0), loop_classes, loop_s), svg)
    svg = _DECL.sub(lambda m: m.group(1) + ",".join(_css_part(p, loop_s) for p in _split_top(m.group(2))), svg)
    svg = re.sub(r"(animation-iteration-count\s*:\s*)infinite", lambda m: m.group(1) + _count(loop_s, loop_s), svg)
    return _SMIL.sub(lambda m: _smil_tag(m.group(0), loop_s), svg)


def leftover_loops(svg: str) -> int:
    """남은 무한 루프 수(빌드 검사용)."""
    return len(re.findall(r"\binfinite\b|repeatCount=\"indefinite\"", svg))


if __name__ == "__main__":
    # 워크플로용: python3 settle.py [--loop 초] 파일... — 외부 생성기(3D 잔디·뱀) 출력을 제자리에서 바꾼다
    import argparse
    from pathlib import Path

    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", type=float, default=LOOP_S, help="루프를 이 초 남짓 돌리고 멈춘다(0 = 한 바퀴만)")
    ap.add_argument("files", nargs="+")
    a = ap.parse_args()
    for f in map(Path, a.files):
        src = f.read_text(encoding="utf-8")
        out = settle(src, a.loop)
        f.write_text(out, encoding="utf-8")
        print(f"{f}: 무한 루프 {leftover_loops(src)} → {leftover_loops(out)}")
