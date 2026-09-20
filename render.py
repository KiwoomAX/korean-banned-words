#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""korean-banned-words.json 에서 소비자가 싣는 마크다운을 만든다.

소비자 둘이 같은 파일을 쓴다. 받아서 자기 저장소에 커밋하고 CLAUDE.md 로
싣는 것까지 절차가 같기 때문이다. 다른 것은 disciplined-coder 만 훅으로
파싱한다는 것인데, 파싱되는 표를 사람이 읽어도 불편하지 않다.

  python render.py            dist/ 에 파일을 쓴다
  python render.py --check    쓰지 않고 지금 dist/ 와 다른지만 본다
"""

import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "korean-banned-words.json"
DIST = HERE / "dist"

OUT = "korean-banned-words.md"


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def live(data):
    return [e for e in data["entries"] if e.get("enabled", True)]


def repl_of(e):
    """대체어가 있으면 그것을, 없으면 지시를 돌려준다."""
    return " · ".join(e.get("replace") or []) or e.get("instruction", "")


# hooks/_banned_words.sh 가 `### 금지 표현` 제목 아래에서 `| ` 로 시작하고
# 백틱이 붙은 행만 읽는다. 첫 칸의 백틱 안을 검색어로, 둘째 칸을 대체어로 쓰고
# 칸이 넷 이상인지만 본다. 그래서 칸을 뒤에 더해도 안전하다.
#
# 제목 아래에 `#` 로 시작하는 줄을 두면 그 파서가 거기서 멈춘다. 분류를 제목이
# 아니라 넷째 칸으로 두는 이유가 이것이다.

def render(data):
    n = data["notice"]
    src = n["source"]
    title = dict((c["id"], c["title"]) for c in data["categories"])
    out = [
        "# 한국어 금지어 목록",
        "",
        n["generated"],
        "",
        "<!-- 원본: %s -->" % src,
        "<!-- 다시 만들기: 원본 저장소의 render.py -->",
        "<!-- 원본 판: schema %s, %s -->" % (data["schema"], data["updated"]),
        "",
        "### 금지 표현",
        "",
        n["usage"],
        "",
        "%s %s" % (n["method"], n["artifact"]),
        "",
        "첫째 칸의 백틱 안이 검색할 글자 그대로다. 셋째 칸이 적용 대상을 정한다. "
        "`답변과 산출물`은 사용자에게 보내는 답과 사용자가 요구한 산출물 문서이고, "
        "`문서와 답변`은 거기에 저장소의 살아 있는 문서까지 더한 것이다. "
        "각 항목의 근거는 %s 에 있다." % src,
        "",
        "| 쓰지 않는 말 | 대신 쓰는 말 | 적용 대상 | 분류 |",
        "|---|---|---|---|",
    ]
    for e in live(data):
        words = " · ".join("`%s`" % w for w in e["banned"])
        where = "문서와 답변" if "living-doc" in e["scope"] else "답변과 산출물"
        out.append("| %s | %s | %s | %s |"
                   % (words, repl_of(e), where, title[e["category"]]))

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


def main():
    check = "--check" in sys.argv
    data = load()
    made = {OUT: render(data)}

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
