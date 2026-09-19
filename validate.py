#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""korean-banned-words.json 의 형식을 검사한다.

이 저장소는 데이터만 담는다. 생성 스크립트는 소비자 저장소가 갖는다.
그래서 여기서 확인하는 것은 "소비자가 읽을 수 있는 형태인가" 하나뿐이고,
어떤 단어를 넣을지 말지는 확인하지 않는다.

실행:  python validate.py
종료 코드 0 이면 통과, 1 이면 위반을 출력하고 실패한다.
"""

import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).parent / "korean-banned-words.json"

SCHEMA_VERSION = 1
EVIDENCE_KINDS = {"user", "measured", "reasoned", "none"}
MATCH_MODES = {"forms", "fragment"}
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def check(data):
    """위반을 문자열 목록으로 돌려준다. 빈 목록이면 통과다."""
    problems = []

    def fail(msg):
        problems.append(msg)

    if data.get("schema") != SCHEMA_VERSION:
        fail("schema 가 %d 이 아닙니다: %r" % (SCHEMA_VERSION, data.get("schema")))

    updated = data.get("updated")
    if not isinstance(updated, str) or not DATE_PATTERN.match(updated):
        fail("updated 가 YYYY-MM-DD 형식이 아닙니다: %r" % (updated,))

    scopes = data.get("scopes")
    if not isinstance(scopes, dict) or not scopes:
        fail("scopes 가 비어 있거나 객체가 아닙니다")
        scopes = {}

    categories = data.get("categories")
    if not isinstance(categories, list) or not categories:
        fail("categories 가 비어 있거나 목록이 아닙니다")
        categories = []

    category_ids = set()
    for i, cat in enumerate(categories):
        if not isinstance(cat, dict):
            fail("categories[%d] 가 객체가 아닙니다" % i)
            continue
        cid = cat.get("id")
        if not isinstance(cid, str) or not ID_PATTERN.match(cid):
            fail("categories[%d].id 가 소문자 영숫자와 붙임표가 아닙니다: %r" % (i, cid))
        elif cid in category_ids:
            fail("categories[%d].id 가 겹칩니다: %s" % (i, cid))
        else:
            category_ids.add(cid)
        if not isinstance(cat.get("title"), str) or not cat.get("title").strip():
            fail("categories[%d].title 이 비어 있습니다" % i)

    # 단어 쌍으로 표현되지 않는 규칙. entries 와 달리 banned 도 replace 도 없다.
    rules = data.get("rules")
    if rules is None:
        rules = []
    if not isinstance(rules, list):
        fail("rules 가 목록이 아닙니다")
        rules = []
    rule_ids = set()
    for i, r in enumerate(rules):
        if not isinstance(r, dict):
            fail("rules[%d] 가 객체가 아닙니다" % i)
            continue
        rid = r.get("id")
        if not isinstance(rid, str) or not ID_PATTERN.match(rid):
            fail("rules[%d].id 가 소문자 영숫자와 붙임표가 아닙니다: %r" % (i, rid))
        elif rid in rule_ids:
            fail("rules[%d].id 가 겹칩니다: %s" % (i, rid))
        else:
            rule_ids.add(rid)
        if not isinstance(r.get("text"), str) or not r.get("text").strip():
            fail("rules[%d].text 가 비어 있습니다" % i)
        scope = r.get("scope")
        if not isinstance(scope, list) or not scope:
            fail("rules[%d].scope 가 비어 있습니다" % i)
        else:
            for s in scope:
                if s not in scopes:
                    fail("rules[%d].scope 의 '%s' 가 scopes 에 없습니다" % (i, s))
        if not isinstance(r.get("enabled"), bool):
            fail("rules[%d].enabled 가 참거짓이 아닙니다: %r" % (i, r.get("enabled")))
        elif r.get("enabled") is False:
            if not isinstance(r.get("disabled_reason"), str) or not r["disabled_reason"].strip():
                fail("rules[%d] 가 enabled=false 인데 disabled_reason 이 없습니다" % i)
        ev = r.get("evidence")
        if not isinstance(ev, dict) or ev.get("kind") not in EVIDENCE_KINDS:
            fail("rules[%d].evidence.kind 가 %s 가운데 하나가 아닙니다"
                 % (i, " 또는 ".join(sorted(EVIDENCE_KINDS))))

    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        fail("entries 가 비어 있거나 목록이 아닙니다")
        return problems

    entry_ids = set()
    seen_banned = {}
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            fail("entries[%d] 가 객체가 아닙니다" % i)
            continue
        where = "entries[%d]" % i

        eid = e.get("id")
        if not isinstance(eid, str) or not ID_PATTERN.match(eid):
            fail("%s.id 가 소문자 영숫자와 붙임표가 아닙니다: %r" % (where, eid))
        elif eid in entry_ids:
            fail("%s.id 가 겹칩니다: %s" % (where, eid))
        else:
            entry_ids.add(eid)
            where = "entries[%d](%s)" % (i, eid)

        cat = e.get("category")
        if cat not in category_ids:
            fail("%s.category 가 categories 에 없습니다: %r" % (where, cat))

        match = e.get("match")
        if match not in MATCH_MODES:
            fail("%s.match 가 %s 가운데 하나가 아닙니다: %r"
                 % (where, " 또는 ".join(sorted(MATCH_MODES)), match))

        banned = e.get("banned")
        if not isinstance(banned, list) or not banned:
            fail("%s.banned 가 비어 있습니다" % where)
        else:
            for w in banned:
                if not isinstance(w, str) or not w.strip():
                    fail("%s.banned 에 빈 문자열이 있습니다" % where)
                    continue
                if w in seen_banned and seen_banned[w] != eid:
                    fail("%s.banned 의 '%s' 가 %s 에도 있습니다"
                         % (where, w, seen_banned[w]))
                seen_banned[w] = eid

        # 대체어가 없으면 지시가 있어야 한다. '자리' 처럼 바꿔 쓸 단어가 아니라
        # "가리키는 대상의 이름을 쓰라"는 지시인 항목이 있기 때문이다.
        replace = e.get("replace")
        instruction = e.get("instruction")
        if replace is not None and not isinstance(replace, list):
            fail("%s.replace 가 목록이 아닙니다" % where)
            replace = None
        if not replace and not (isinstance(instruction, str) and instruction.strip()):
            fail("%s 에 replace 도 instruction 도 없습니다" % where)
        if replace:
            for w in replace:
                if not isinstance(w, str) or not w.strip():
                    fail("%s.replace 에 빈 문자열이 있습니다" % where)

        scope = e.get("scope")
        if not isinstance(scope, list) or not scope:
            fail("%s.scope 가 비어 있습니다" % where)
        else:
            for s in scope:
                if s not in scopes:
                    fail("%s.scope 의 '%s' 가 scopes 에 없습니다" % (where, s))

        enabled = e.get("enabled")
        if not isinstance(enabled, bool):
            fail("%s.enabled 가 참거짓이 아닙니다: %r" % (where, enabled))
        elif enabled is False:
            reason = e.get("disabled_reason")
            if not isinstance(reason, str) or not reason.strip():
                fail("%s 가 enabled=false 인데 disabled_reason 이 없습니다" % where)

        ev = e.get("evidence")
        if not isinstance(ev, dict):
            fail("%s.evidence 가 객체가 아닙니다" % where)
            continue
        kind = ev.get("kind")
        if kind not in EVIDENCE_KINDS:
            fail("%s.evidence.kind 가 %s 가운데 하나가 아닙니다: %r"
                 % (where, " 또는 ".join(sorted(EVIDENCE_KINDS)), kind))
        if kind in ("user", "measured"):
            date = ev.get("date")
            if not isinstance(date, str) or not DATE_PATTERN.match(date):
                fail("%s.evidence.date 가 YYYY-MM-DD 형식이 아닙니다: %r" % (where, date))
            if not isinstance(ev.get("quote"), str) or not ev.get("quote").strip():
                fail("%s.evidence.quote 가 비어 있습니다 (kind=%s)" % (where, kind))

    return problems


def main():
    if not DATA.exists():
        print("데이터 파일이 없습니다: %s" % DATA)
        return 1
    try:
        data = json.loads(DATA.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print("JSON 을 읽지 못했습니다: %s" % exc)
        return 1

    problems = check(data)
    if problems:
        print("위반 %d 건" % len(problems))
        for p in problems:
            print("  - %s" % p)
        return 1

    total = len(data["entries"])
    live = sum(1 for e in data["entries"] if e.get("enabled"))
    print("통과했습니다. 항목 %d 개 가운데 %d 개가 켜져 있습니다." % (total, live))
    return 0


if __name__ == "__main__":
    sys.exit(main())
