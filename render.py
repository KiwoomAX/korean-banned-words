#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""korean-banned-words.json 에서 소비자가 싣는 마크다운을 만든다.

소비자마다 모양이 다르다. disciplined-coder 는 훅이 파싱하는 표가 필요하고,
사내 kw-control-tower 는 사람이 읽는 분류별 화살표 형식이 필요하다. 모양이
둘이어도 결정은 한 곳에서 내린다. 생성기가 둘이면 분류 제목과 안내 문구와
항목 차례가 두 벌이 되고, 실제로 그렇게 갈라진 적이 있다.

  python render.py            dist/ 에 두 파일을 쓴다
  python render.py --check    쓰지 않고 지금 dist/ 와 다른지만 본다
"""

import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "korean-banned-words.json"
DIST = HERE / "dist"

DC = "korean-banned-words-dc.md"   # disciplined-coder — 훅이 파싱한다
AX = "korean-banned-words-ax.md"   # 사내 kw-control-tower — 사람이 읽는다


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def live(data):
    return [e for e in data["entries"] if e.get("enabled", True)]


def repl_of(e):
    """대체어가 있으면 그것을, 없으면 지시를 돌려준다."""
    return " · ".join(e.get("replace") or []) or e.get("instruction", "")


# ── disciplined-coder 형식 ────────────────────────────────────────────
# hooks/_banned_words.sh 가 `### 금지 표현` 제목 아래에서 `| ` 로 시작하고
# 백틱이 붙은 행만 읽는다. 첫 칸의 백틱 안을 검색어로, 둘째 칸을 대체어로 쓴다.
# 제목 아래에 `#` 로 시작하는 줄을 두면 그 파서가 거기서 멈춘다.

def render_dc(data):
    n = data["notice"]
    src = n["source"]
    out = [
        "<!-- %s -->" % n["generated"],
        "<!-- 원본: %s -->" % src,
        "<!-- 다시 만들기: 원본 저장소의 render.py -->",
        "<!-- 원본 판: schema %s, %s -->" % (data["schema"], data["updated"]),
        "",
        "### 금지 표현",
        "",
        "%s 각 항목의 근거는 %s 에 있다." % (n["method"], src),
        "",
        "첫째 칸의 백틱 안이 검색할 글자 그대로다. 셋째 칸이 적용 대상을 정한다. "
        "`답변과 산출물`은 사용자에게 보내는 답과 사용자가 요구한 산출물 문서이고, "
        "`문서와 답변`은 거기에 이 저장소의 살아 있는 문서까지 더한 것이다.",
        "",
        "| 쓰지 않는 말 | 대신 쓰는 말 | 적용 대상 |",
        "|---|---|---|",
    ]
    for e in live(data):
        words = " · ".join("`%s`" % w for w in e["banned"])
        where = "문서와 답변" if "living-doc" in e["scope"] else "답변과 산출물"
        out.append("| %s | %s | %s |" % (words, repl_of(e), where))

    rules = [r for r in data.get("rules", []) if r.get("enabled", True)]
    if rules:
        out += ["",
                "단어 쌍으로 적을 수 없는 것이 아래에 있다. 문자열 검색으로는 "
                "안 잡히므로 이 지시가 맡는다.",
                ""]
        out += ["- %s" % r["text"] for r in rules]

    off = [e["banned"][0] for e in data["entries"] if not e.get("enabled", True)]
    if off:
        out += ["",
                "꺼 둔 항목은 %s 이고, 왜 껐는지는 원본이 적는다. 이 목록에서 뺀 것이 "
                "아니라 끈 것이다." % " · ".join("`%s`" % w for w in off)]
    return "\n".join(out) + "\n"


# ── 사내 kw-control-tower 형식 ────────────────────────────────────────
# 사람과 Claude 가 읽는다. 분류 제목과 화살표 줄만 담는다. 분류마다 붙던
# 설명 문단은 사용자가 빼기로 정했다.

# 화살표를 세로로 맞춘다. 한글은 글자 하나가 두 칸을 차지하므로 글자 수로
# 맞추면 화면에서 들쭉날쭉해진다. 가운뎃점(U+00B7)은 한 칸이다.
WIDE = ((0x1100, 0x115F), (0x2E80, 0xA4CF), (0xAC00, 0xD7A3),
        (0xF900, 0xFAFF), (0xFE30, 0xFE6F), (0xFF00, 0xFF60), (0xFFE0, 0xFFE6))

# 맞추는 폭의 상한. `걸다` 는 조사까지 적은 구가 스물셋이라 표시 너비가 230칸을
# 넘는다. 그것에 맞추면 그 분류의 모든 줄이 이백 칸 넘게 벌어져 안 읽힌다.
ALIGN_CAP = 44


def width(s):
    n = 0
    for ch in s:
        o = ord(ch)
        n += 2 if any(lo <= o <= hi for lo, hi in WIDE) else 1
    return n


def render_ax(data):
    n = data["notice"]
    out = [
        "# 한국어 금지어 목록",
        "",
        n["generated"],
        "",
        n["usage"],
        "",
        "%s %s" % (n["method"], n["artifact"]),
    ]
    for c in data["categories"]:
        rows = [e for e in live(data) if e["category"] == c["id"]]
        if not rows:
            continue
        pairs = [(" · ".join(e["banned"]), repl_of(e)) for e in rows]
        fits = [width(a) for a, _ in pairs if width(a) <= ALIGN_CAP]
        pad = max(fits) if fits else 0
        out += ["", "## %s" % c["title"], "", "```"]
        for a, b in pairs:
            w = width(a)
            gap = (pad - w + 3) if w <= pad else 3
            out.append("%s%s→   %s" % (a, " " * gap, b))
        out.append("```")

    rules = [r for r in data.get("rules", []) if r.get("enabled", True)]
    if rules:
        out += ["", "## 단어가 아닌 규칙", ""]
        for r in rules:
            out += [r["text"], ""]
        out.pop()
    return "\n".join(out) + "\n"


def main():
    check = "--check" in sys.argv
    data = load()
    made = {DC: render_dc(data), AX: render_ax(data)}

    if check:
        bad = []
        for name, body in made.items():
            f = DIST / name
            if not f.exists():
                bad.append("%s 가 없습니다" % name)
            elif f.read_text(encoding="utf-8") != body:
                bad.append("%s 가 데이터와 다릅니다" % name)
        if bad:
            print("다시 만들어야 합니다.")
            for b in bad:
                print("  - %s" % b)
            print("  python render.py 를 실행하고 그 결과를 커밋하십시오.")
            return 1
        print("dist/ 가 데이터와 같습니다.")
        return 0

    DIST.mkdir(exist_ok=True)
    for name, body in made.items():
        io.open(DIST / name, "w", encoding="utf-8", newline="\n").write(body)
        print("%s  %d줄" % (name, body.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
