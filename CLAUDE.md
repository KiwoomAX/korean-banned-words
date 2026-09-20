# korean-banned-words 작업 규칙

## 데이터를 고쳤으면 반드시 `render.py` 를 실행한다

```
python render.py
```

`korean-banned-words.json` 을 고치고 이것을 실행하지 않으면 `dist/` 가 옛 내용으로 남습니다. 소비자 두 곳이 받아 가는 것은 `dist/` 이므로, 실행하지 않으면 **데이터만 바뀌고 실제로 적용되는 목록은 그대로입니다.**

CI 가 `render.py --check` 로 잡아 실패시키지만, 그때는 이미 올린 뒤입니다. 올리기 전에 실행하십시오.

## 올리기 전에 치는 것

```
python render.py
python validate.py
python render.py --check
```

셋이 통과하면 `korean-banned-words.json` 과 `dist/` 를 **같은 커밋에** 포함합니다. 데이터만 올리면 CI 가 실패합니다.

## 이 저장소의 구조

`korean-banned-words.json` 이 원본입니다. `render.py` 가 그것으로 `dist/korean-banned-words.md` 를 만들고, 소비자 둘이 그 파일을 받아 각자 저장소에 커밋합니다.

| 소비자 | 쓰는 방법 |
|---|---|
| disciplined-coder | `hooks/_banned_words.sh` 가 표를 파싱해 산출물 문서의 쓰기를 거부합니다 |
| 사내 kw-control-tower | `CLAUDE.md` 로 실어 지시로 적용합니다 |

생성물은 한 파일입니다. 두 소비자의 절차가 같고, 파싱되는 표를 사람이 읽어도 불편하지 않기 때문입니다.

## 생성물을 고칠 때 깨뜨리면 안 되는 것

`hooks/_banned_words.sh` 의 awk 가 이렇게 읽습니다.

- `### 금지 표현` 제목 아래에서만 읽습니다.
- 그 아래에 `#` 로 시작하는 줄이 오면 **거기서 멈춥니다.** 분류를 제목이 아니라 표의 칸으로 둔 이유가 이것입니다.
- `| ` 로 시작하고 백틱이 붙은 행만 읽습니다. 첫 칸의 백틱 안이 검색어이고 둘째 칸이 대체어입니다.
- 칸이 넷 이상인지만 봅니다. 그래서 칸을 뒤에 추가하는 것은 안전하고, 앞의 두 칸 위치를 바꾸는 것은 안전하지 않습니다.

앞의 둘은 `render.py` 의 `check_contract` 가 만들 때 확인해 막습니다. 판 표시가 머리 20줄 안에 있는지도 함께 봅니다. disciplined-coder 가 `head -20` 으로 그 줄만 읽어 어느 쪽 목록이 최신인지 가리므로, 그 줄이 20줄 밖으로 밀리면 그쪽 알림이 소리 없이 죽습니다.

## `schema` 를 올릴 때

`schema` 는 데이터의 구조가 바뀔 때만 올립니다. 항목을 넣고 빼거나 대체어를 고치는 것은 `updated` 날짜만 바꿉니다.

생성물의 앞 두 칸 순서를 바꾸지 않고 칸을 뒤에 추가하는 것만 허용하므로, `schema` 가 올라가도 옛 소비자가 그대로 읽습니다. 소비자는 `schema` 를 정수로 `updated` 를 문자열로 견주어 최신을 가립니다. 둘이 같은데 판 표시의 셋째 값(내용 지문)이 다르면 어느 쪽이 새것인지 알 수 없으므로 건드리지 말고 알려야 합니다. `updated` 가 날짜뿐이라 하루에 여러 번 고치면 값이 같기 때문입니다.

형식을 고쳤으면 실제 파서에 넣어 확인하십시오.

```
cd <disciplined-coder 저장소>
. hooks/_banned_words.sh
W=$(mktemp -d); banned_parse <생성물 경로> "$W/pairs" "$W/toks"
wc -l "$W/toks" "$W/pairs"
```

## 항목을 넣고 뺄 때

`evidence` 를 반드시 채웁니다. 근거를 찾지 못했으면 `none` 으로 적습니다. 근거 없이 넣으면 몇 달 뒤 같은 논의를 처음부터 다시 하게 됩니다.

어간을 적을 때 한글은 음절이 한 글자입니다. `맞대` 가 `맞대고` 는 포함하지만 `맞댄` 은 포함하지 않습니다. 그리고 다른 단어에 나타나는 어간은 뺍니다. `가르다` 에 `가르` 를 넣으면 `가르치다` 까지 검출됩니다.

넣기 전에 실제 빈도와 거짓 검출을 세어 보십시오. 오늘 여섯 항목이 나열로는 실제 활용형의 절반도 검출하지 못하고 있었습니다.

## 이 저장소의 문서에도 목록이 적용된다

`README.md` 와 이 파일도 금지어 검사 대상입니다. 고친 뒤 확인하십시오.

```
python - <<'PY'
import json, io, re
d = json.loads(io.open("korean-banned-words.json", encoding="utf-8").read())
words = [w for e in d["entries"] if e["enabled"] for w in e["banned"]]
fence = re.compile(r"```.*?```", re.S); tick = re.compile(r"`[^`\n]*`")
for path in ("README.md", "CLAUDE.md"):
    t = tick.sub("", fence.sub("", io.open(path, encoding="utf-8").read()))
    hits = sorted(((t.count(w), w) for w in words if w in t), reverse=True)
    print(path, ":", ", ".join("%s %d" % (w, n) for n, w in hits) or "금지어 없음")
PY
```

백틱 안과 코드 블록은 대상이 아닙니다. 금지어 자체를 문서에 적어야 할 때는 백틱으로 감싸십시오.
