# Deep Ocean Neon — 프로필 에셋 디자인 시스템

이 문서만 읽고 같은 스타일의 에셋 모듈을 만들 수 있게 쓴다. 토큰·헬퍼 구현은 `design.py`, 기준 예시는 `hero.py`(풍부한 예)와 `divider.py`(최소 예).

## 1. 모듈 계약

```python
# scripts/profile_assets/<name>.py
from . import design as D
W, H, P = 1280, 360, "<name>"          # P = 접두사 = 파일 이름

def render(theme, data) -> str:         # theme: 'dark' | 'light'
    T = D.tokens(theme)
    body = D.card(W, H, theme, P) + ...
    return D.svg_root(W, H, theme, "제목", "설명", body, extra_css, P)
```

- 빌드: `python3 scripts/build_assets.py --only <name>` → `assets/<name>-dark.svg`, `assets/<name>-light.svg`.
- `data` = `profile.json` 전체 + `data["commits"]` = `commits_daily.json`(`series[{date,total,by}]`, `total`, `repos`, `monthly`, `max_day`, `by_domain`, `days`, `active_days`).
- 사실(이름·수치·문구)은 전부 `data` 에서 읽는다. 모듈에 하드코딩 금지(개념 라벨 "PLAN", "LIVE" 같은 건 예외). 값은 나중에 확정값으로 바뀌니 **길이·자릿수가 달라져도 깨지지 않게** `fit_size`·`fit_block`·`truncate`·`chips_row` 를 쓴다.
- 빌드가 자동 검사: XML 파싱, 금지 패턴(`<script`, `@import`, `foreignObject`, 외부 http(s) href·url(), `<image>`), 루트 속성(width·height·viewBox·role·aria-label·title·desc), id 중복·접두사, 크기(120KB, skyline 250KB), 애니메이션 요소 400개. 실패하면 `assets/<name>-<theme>.invalid.svg` 로 남는다.

## 2. 렌더 환경(GitHub README)

- `<img>` 로 표시된다(camo). 스크립트·외부 리소스·웹폰트·foreignObject·호버/클릭 없음. **모든 움직임은 자동 재생.**
- 본문 폭 ≈ 830px → viewBox 1280 은 **0.65배**, 모바일 390px 은 0.3배.
- 다크 에셋은 `#0d1117`, 라이트 에셋은 `#ffffff` 위. `D.card()` 로 자체 카드 배경을 깔아 어느 쪽에서도 완결.

## 3. 토큰 (`T = D.tokens(theme)`)

| 키 | dark | light | 용도 |
|---|---|---|---|
| `bg` `bg2` `bg3` | #0B1220 · #0E1E33 · #0A1626 | #F6FBFF · #E9F5FC · #FFFFFF | 카드 채움 그라디언트 |
| `text` | #E8F6FC | #0B1F33 | 본문 |
| `text2` | #A9C1D3 | #4A6178 | 보조 |
| `muted` | #6E879D | #7A90A4 | 캡션·축 |
| `accent` | #00B4D8 | #0077B6 | 주 강조(시안/오션) |
| `accent2` | #2DD4BF | #0D9488 | 보조 강조(틸) |
| `accent3` | #A78BFA | #7C3AED | AI 포인트(바이올렛) — 글자용 |
| `violet` | #7C3AED | #7C3AED | AI 포인트 — 면·선 |
| `coral` | #FF6F61 | #E8574B | 경고·하이라이트(아주 조금) |
| `grad` | 0077B6→00B4D8→14B8A6 | 동일 | 면·선 브랜드 그라디언트 |
| `grad_text` | 90E0EF→00B4D8→2DD4BF | 005F92→0096C7→0D9488 | 큰 글자 그라디언트(대비 확보) |
| `grad_ai` | 00B4D8→7C3AED | 0077B6→7C3AED | AI 관련 요소 |
| `border` `border_hi` | 시안 16%·34% | #D0E7F5 · #9FCBE6 | 테두리 |
| `surface` `surface_hi` | 시안 4.5%·9% | 흰색 72%·92% | 반투명 면 |
| `particle` `line` | #90E0EF · #48CAE4 | #0077B6 · #0096C7 | 점·연결선 |
| `glow_opacity` `blob_opacity` | 0.85 · 0.38 | 0.35 · 0.20 | 라이트는 빛 효과를 약하게 |
| `dark` | True | False | 분기용 |

`D.PALETTE` 에 원색(abyss, ocean, cyan, aqua, teal, mint, violet, coral)이 있다. 라이트에서 #14B8A6·#90E0EF 를 **글자색**으로 쓰지 말 것(흰 바탕 대비 부족) — `accent2`·`grad_text` 사용.

## 4. 글자 규칙

- 폰트: `D.FONT_KO`(Pretendard → Apple SD Gothic Neo → Noto Sans KR → Malgun Gothic), `D.FONT_LATIN`(Inter → Segoe UI → Helvetica Neue → Arial), `D.FONT_MONO`(JetBrains Mono → SFMono → Menlo → Consolas). `D.text(..., family='auto')` 는 한글이 섞이면 KO 스택을 쓴다.
- 크기(SVG 단위, 폭 1280 기준): 헤드라인 40~80, 섹션 제목 34~48, 카드 제목 24~28, **본문 최소 18, 캡션 최소 16**. `D.SIZE` 참고.
- 폭 추정 `D.text_width(s, size, family, weight)`: 한글 1.0em, 라틴 0.6em(대문자 0.7), 숫자 0.62em, mono 0.6em, weight≥600 은 +6%. 일부러 넉넉하다(대체 폰트 대비). 실제 글자는 추정보다 약간 짧게 그려진다.
- 넘침 처리: 한 줄 → `fit_size`(min 까지 축소) 후에도 넘치면 `truncate`. 여러 줄 → `fit_block(s, max_w, size, min_size, max_lines)` → `(size, lines)` 을 `text_lines` 로.
- 글자 바로 뒤에 붙는 요소는 추정 대신 **같은 `<text>` 안 tspan 으로 이어 붙인다**(hero 의 한글 이름: 투명한 영문 이름 tspan 뒤에 붙여 실제 폭을 따라감).
- 숫자는 `D.fmt_int(12439)` → "12,439", `D.fmt_compact` → "12.4k", 날짜 `D.fmt_date('2026-06-22')` → "2026.06.22". data 값이 이미 문자열이면 그대로 둔다.

## 5. 표면 · 장식 헬퍼

| 헬퍼 | 설명 |
|---|---|
| `card(w, h, theme, P, r=20)` | 에셋 배경 카드(그라디언트 채움 + 그라디언트 테두리 1.5 + 위쪽 안쪽 하이라이트). 맨 먼저 그린다. |
| `card_clip(id, w, h)` | 카드 모양 clipPath — 배경 장식을 모서리 안에 가둔다. |
| `glass_defs(theme, P)` + `glass(x, y, w, h, theme, P)` | 글래스모피즘 패널(반투명 + 그라디언트 테두리 + 하이라이트 + 그림자). defs 는 에셋당 한 번. |
| `chip(x, y, label, theme, size, variant)` → `(svg, w)` | 알약 칩. variant: accent·teal·violet·neutral·coral. `dot=True` 상태 점. |
| `eyebrow(P, x, y, label, theme, variant, icon, max_w=, anchor=)` → `(svg, w)` | 섹션 머리 위 모노 라벨 칩(높이 32, 맥동 점 또는 ✦). 제목 있는 섹션(hero·skyline·domains·orchestra)은 전부 이걸 쓴다. 자간 포함 폭으로 말줄임. |
| `chips_row(x, y, labels, theme, max_w, size, cls_fn=)` | 한 줄 칩 배치. 넘치면 16까지 축소 → `+N` 접기. `cls_fn(i)->(class, style)` 로 순차 팝. |
| `linear_gradient` · `radial_gradient` | stops: `['#hex', ...]` 균등 또는 `[(offset, '#hex', opacity), ...]`. |
| `glow_filter(id, std, strength)` | 네온 글로우(원본 + 흐린 사본). 작은 점·선·글자에. |
| `blur_filter(id, std)` · `shadow_filter(id, theme)` | 번짐 · 카드 그림자. |
| `dot_grid_pattern(id, theme)` | 점 격자 패턴(배경 질감). |
| `fade_mask(id, w, h, axis)` | 양 끝이 사라지는 마스크(선·띠). |
| `constellation(P, theme, box, count, seed, dim_box=)` | 별자리 네트워크(노드 반짝임 + 연결선 숨쉬기). 글자 자리는 `dim_box` 로 흐리게. |
| `wave_path` · `wave_line` | 주기 물결(채움/윗선). `translate_loop_css` 로 한 주기만큼 흘린다. |
| `sparkle_path(cx, cy, r)` | 4갈래 반짝임(✦) — AI 포인트 아이콘. |
| `odometer(P, x, y, "12,439", size, fill, clip_id=)` | 슬롯머신처럼 굴러 멈추는 숫자. 숫자마다 70ms 엇갈림. |
| `typewriter(P, uid, x, y, s, size, fill)` → `(svg, css, end_ms)` | 한 글자씩 타이핑 + 따라오는 깜빡 커서. |
| `rng(seed)` | 결정적 난수(빌드마다 같은 그림). |

## 6. 모션 규칙

**공통 class**(svg_root 가 `base_css(P)` 를 자동 포함, 이름은 `P-xxx`):

| 등장(1회, 최종 상태로 멈춤) | 루프(배경) |
|---|---|
| `fu` 떠오름 0.9s · `fd` 내려옴 · `fi` 페이드 1s | `glow` 불투명도 맥동 4s · `tw` 반짝임 3.6s |
| `pop` 확대 팝 0.7s(fill-box 중심) | `breathe` 숨쉬기 6s · `pulse` 크기 맥동 3.2s |
| `draw` 선 그리기 1.6s(**path 에 `pathLength="1"`**) | `float` 둥실 7s · `floats` 큰 표류 14s · `sway` 9s |
| `type` 타이핑(typewriter 가 씀) · `odo` 롤링 숫자 | `spin` 36s · `spinr` 28s(로컬 원점 기준 회전) · `blink` 1.1s |

- 지연: `style="animation-delay:300ms"` = `D.delay(300)`, 순차 `D.stagger(i, base, step)`. 길이 변경: `style="animation-duration:60s"`.
- 사용자 keyframes: `D.keyframes(P, "k-name", "from{...}to{...}")` 를 extra_css 에, 요소엔 `style=D.anim(P, "k-name", dur, delay_ms, ease)`. 이음매 없는 흐름: `translate_loop_css`, 흐르는 그라디언트: `flow_gradient` + `flow_rect` + `flow_css`, 빛 스침: `shimmer_css`.
- 이징: 등장 `D.EASE_OUT`, 루프 `D.EASE_IN_OUT`, 팝 `D.EASE_BACK`.

**반드시 지킬 것**

1. **등장 keyframes 는 `from` 만.** 끝 상태 = 요소 기본 상태. 그래서 축소 모드·애니메이션 미지원에서도 최종 화면이 남는다. 숫자·글자의 "기본 상태"가 항상 읽을 수 있는 최종값이어야 한다.
2. **애니메이션은 속성을 덮어쓴다.** `opacity` 를 애니메이션하는 요소에 `opacity="0.3"` 을 주면 무시된다 → 정적 값은 바깥 `<g opacity>` 에. `transform` 애니메이션 요소에 `transform` 속성 금지 → 위치는 바깥 `<g transform="translate(..)">`.
3. CSS `transform` 의 px = SVG 단위. 퍼센트 translate 는 쓰지 말 것(기준 상자가 브라우저마다 다름).
4. `clip-path: inset()` 애니메이션은 SVG `<text>` 에서 Chrome 이 무시한다 → `typewriter` 처럼 clipPath 안 사각형을 `scaleX` 로.
5. 축소 모드: `reduced_motion_css` 가 모든 CSS 애니메이션을 끄고, `motion_only(P, ...)` 로 감싼 부분(`P-m`)을 숨긴다. **SMIL(`<animate>`, `<animateMotion>`)은 CSS 로 못 끄니 반드시 `motion_only` 안에.** 기본 위치에 남으면 어색한 장식(유성·흐르는 입자)도 `motion_only` 로. 축소 모드 전용 대체물은 `static_only`.
6. 루프 4~12초(배경 표류·회전은 더 길어도 됨), 번쩍임 초당 3회 이하. 등장은 2.5초 안에 끝나게(미리보기 2500ms 프레임에서 모두 보여야 함).
7. 애니메이션 요소 ≤ 400. 같은 움직임은 class 재사용, 반복 요소는 음수 delay(`animation-delay:-1200ms`)로 위상만 흩뜨린다.
8. id·class·keyframes 전부 `P-` 접두사. 다른 에셋과 겹치지 않는다.

## 7. 레이아웃 관례

- **모든 에셋 viewBox 폭 1280**(README 에서 같은 0.65배로 줄어 반경·선·글자 배율이 맞는다). 카드 반경 20, 선 1.5.
- 바깥 여백: 그리드형(stats·domains·terminal)은 56, 텍스트 블록은 x=72(hero·timeline·orchestra). 칩과 제목은 같은 x 에서 시작.
- 제목 있는 섹션의 머리 = `eyebrow` 칩(y≈34) + 그라디언트 제목(`grad_text`, 800, 44~46, 다크는 블러 글로우 0.45) + 빛 스침 8s.
- 배경 장식은 `<g clip-path="url(#P-clip)">` 안(`card_clip`), 글자는 그 밖(위)에.
- 순서: card → 배경(오로라 덩어리·격자·별자리) → 주 시각 요소 → 글자 → 칩.
- 라이트 테마는 다크를 밝게 뒤집은 게 아니라 **빛 효과를 줄이고 대비를 올린다**: 글로우 약하게(`glow_opacity`), 글자색은 진한 토큰.

## 8. 검수 절차(필수)

```bash
python3 scripts/build_assets.py --only <name>
node <scratchpad>/profile/tools/preview.mjs --t 300,2500,6000 --out <scratchpad>/profile/preview/<name> assets/<name>-dark.svg assets/<name>-light.svg
node <scratchpad>/profile/tools/preview.mjs --t 6000 --width 830 --out ... (README 실제 폭)
node <scratchpad>/profile/tools/reduced-motion.mjs --out ... assets/<name>-dark.svg   # 축소 모드 최종 화면
```

PNG 를 Read 로 직접 열어 본다. 2500ms 에 모든 글자가 보이는지, 830 폭에서 본문이 읽히는지, 긴 값(이름·문구 2배)을 넣어도 넘치지 않는지 확인한다.

## 9. 최소 예시

```python
from . import design as D
W, H, P = 1280, 240, "example"

def render(theme, data):
    T = D.tokens(theme)
    title = data.get("role_en", "")
    size = D.fit_size(title, W - 144, 40, 26, "latin", 700)
    chips, _ = D.chips_row(72, 150, data.get("chips", []), theme, W - 144,
                           cls_fn=lambda i: (f"{P}-pop", D.stagger(i, 600, 90)))
    body = (D.card(W, H, theme, P)
            + D.defs(D.card_clip(f"{P}-clip", W, H))
            + f'<g clip-path="url(#{P}-clip)">'
            + D.constellation(P, theme, (0, 0, W, H), count=18, seed=3) + "</g>"
            + f'<g class="{P}-fu">' + D.text(72, 110, D.truncate(title, W - 144, size), size, T["text"], 700) + "</g>"
            + chips)
    return D.svg_root(W, H, theme, title, "예시", body, "", P)
```
