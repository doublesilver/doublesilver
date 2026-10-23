#!/usr/bin/env python3
"""프로필 README 애니메이션 SVG 빌드.

사용: python3 scripts/build_assets.py [--only NAME[,NAME...]]
출력: assets/<name>-dark.svg, assets/<name>-light.svg
데이터: scripts/data/profile.json + scripts/data/commits_daily.json
        → data = {**profile, "commits": commits_daily}
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
DATA_DIR = SCRIPTS / "data"
OUT_DIR = ROOT / "assets"
sys.path.insert(0, str(SCRIPTS))

from profile_assets import MODULES  # noqa: E402
from profile_assets.design import ANIM_CLASSES  # noqa: E402

THEMES = ("dark", "light")
SIZE_LIMIT_KB = {"skyline": 250}
DEFAULT_LIMIT_KB = 120
MAX_ANIMATED = 400
SVG_NS = "{http://www.w3.org/2000/svg}"

FORBIDDEN = [
    (re.compile(r"<script", re.I), "<script"),
    (re.compile(r"@import", re.I), "@import"),
    (re.compile(r"foreignObject", re.I), "foreignObject"),
    (re.compile(r"""(?:xlink:)?href\s*=\s*["']\s*(?:https?:)?//""", re.I), "외부 href"),
    (re.compile(r"""url\(\s*["']?\s*(?:https?:)?//""", re.I), "외부 url()"),
    (re.compile(r"<image\b", re.I), "<image>(외부·임베드 이미지)"),
]


def load_data() -> dict:
    profile = json.loads((DATA_DIR / "profile.json").read_text(encoding="utf-8"))
    commits_path = DATA_DIR / "commits_daily.json"
    commits = json.loads(commits_path.read_text(encoding="utf-8")) if commits_path.exists() else {}
    data = dict(profile)
    data["commits"] = commits
    return data


def count_animated(root: ET.Element, prefix: str) -> int:
    """CSS 애니메이션(class·style) 또는 SMIL 이 걸린 요소 수."""
    anim_cls = {f"{prefix}-{c}" for c in ANIM_CLASSES}
    cnt = 0
    for el in root.iter():
        tag = el.tag.replace(SVG_NS, "")
        if tag in ("animate", "animateMotion", "animateTransform", "set"):
            cnt += 1
            continue
        style = el.get("style", "")
        cls = set(el.get("class", "").split())
        if "animation" in style.replace("animation-delay", "") or cls & anim_cls:
            cnt += 1
    return cnt


def check_svg(name: str, theme: str, svg: str) -> tuple[list[str], list[str], dict]:
    errors, warns = [], []
    info = {}
    for rx, label in FORBIDDEN:
        if rx.search(svg):
            errors.append(f"금지 패턴: {label}")
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as e:
        errors.append(f"XML 파싱 실패: {e}")
        return errors, warns, info
    if root.tag != SVG_NS + "svg":
        errors.append("루트가 <svg> 가 아님(xmlns 확인)")
    for a in ("width", "height", "viewBox", "role", "aria-label"):
        if not root.get(a):
            errors.append(f"루트 속성 누락: {a}")
    if root.find(SVG_NS + "title") is None:
        errors.append("<title> 누락")
    if root.find(SVG_NS + "desc") is None:
        errors.append("<desc> 누락")
    ids = [el.get("id") for el in root.iter() if el.get("id")]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        errors.append(f"id 중복: {', '.join(dup[:8])}")
    bad = [i for i in ids if not i.startswith(name + "-")]
    if bad:
        errors.append(f"접두사 없는 id: {', '.join(bad[:8])}")
    kb = len(svg.encode("utf-8")) / 1024
    limit = SIZE_LIMIT_KB.get(name, DEFAULT_LIMIT_KB)
    if kb > limit:
        errors.append(f"크기 초과 {kb:.1f}KB > {limit}KB")
    animated = count_animated(root, name)
    if animated > MAX_ANIMATED:
        errors.append(f"애니메이션 요소 {animated}개 > {MAX_ANIMATED}")
    if "prefers-reduced-motion" not in svg:
        warns.append("prefers-reduced-motion 규칙 없음")
    info.update(kb=kb, limit=limit, animated=animated, elements=sum(1 for _ in root.iter()))
    return errors, warns, info


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="프로필 애니메이션 SVG 빌드")
    ap.add_argument("--only", help="쉼표로 구분한 에셋 이름(예: hero,divider)")
    args = ap.parse_args(argv)

    names = MODULES
    if args.only:
        wanted = [s.strip() for s in args.only.split(",") if s.strip()]
        unknown = [w for w in wanted if w not in MODULES]
        if unknown:
            print(f"[경고] 등록되지 않은 이름: {', '.join(unknown)} (등록: {', '.join(MODULES)})")
        names = [w for w in wanted if w in MODULES]

    data = load_data()
    if data.get("_provisional"):
        print("[경고] profile.json 이 _provisional=true — 임시값으로 빌드합니다. 확정값으로 교체 후 다시 빌드하세요.")

    OUT_DIR.mkdir(exist_ok=True)
    ok, failed, skipped = [], [], []
    for name in names:
        try:
            mod = importlib.import_module(f"profile_assets.{name}")
        except ModuleNotFoundError as e:
            if e.name == f"profile_assets.{name}":
                print(f"[건너뜀] {name}: 모듈 없음")
                skipped.append(name)
                continue
            print(f"[실패] {name}: import 오류 — {e}")
            traceback.print_exc()
            failed.append(name)
            continue
        except Exception as e:  # 모듈 하나가 깨져도 나머지는 계속
            print(f"[실패] {name}: import 오류 — {e}")
            traceback.print_exc()
            failed.append(name)
            continue
        if not hasattr(mod, "render"):
            print(f"[실패] {name}: render(theme, data) 없음")
            failed.append(name)
            continue
        for theme in THEMES:
            label = f"{name}-{theme}"
            try:
                svg = mod.render(theme, data)
            except Exception as e:
                print(f"[실패] {label}: render 예외 — {e}")
                traceback.print_exc()
                failed.append(label)
                continue
            errors, warns, info = check_svg(name, theme, svg)
            out = OUT_DIR / f"{label}.svg"
            if errors:
                bad = OUT_DIR / f"{label}.invalid.svg"
                bad.write_text(svg, encoding="utf-8")
                print(f"[실패] {label}: " + " / ".join(errors) + f"  (검사용 사본: {bad.relative_to(ROOT)})")
                failed.append(label)
                continue
            stale = OUT_DIR / f"{label}.invalid.svg"
            if stale.exists():
                stale.unlink()
            out.write_text(svg, encoding="utf-8")
            w = ("  경고: " + " / ".join(warns)) if warns else ""
            print(f"[완료] {out.relative_to(ROOT)}  {info['kb']:.1f}KB/{info['limit']}KB  "
                  f"요소 {info['elements']}개 · 애니메이션 {info['animated']}개{w}")
            ok.append(label)

    print(f"\n요약: 완료 {len(ok)} · 실패 {len(failed)} · 건너뜀 {len(skipped)}")
    if failed:
        print("실패 목록: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
