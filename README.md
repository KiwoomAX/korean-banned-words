# korean-banned-words

한국어 문서와 답변에서 쓰지 않을 단어의 목록입니다.

같은 목록이 여러 저장소에서 따로 관리되면 한쪽만 고쳤을 때 내용에 불일치가 생깁니다. 목록을 고치는 곳을 여기 하나로 두고, 다른 저장소는 여기서 만들어 낸 사본을 씁니다.

## 파일

`korean-banned-words.json` 이 목록이고, `render.py` 가 소비자가 싣는 `dist/korean-banned-words.md` 를 만들며, `validate.py` 가 형식 검사입니다.

소비자 둘이 같은 파일을 씁니다. 받아서 자기 저장소에 커밋하고 `CLAUDE.md` 로 싣는 것까지 절차가 같기 때문입니다. 다른 것은 disciplined-coder 만 훅으로 파싱한다는 것인데, 파싱되는 표를 사람이 읽어도 불편하지 않습니다. 소비자는 파이썬을 실행하지 않습니다.

## 데이터

```json
{
  "id": "jaeda",
  "category": "native-verb",
  "match": "fragment",
  "banned": ["재다", "재어", "잰", "쟀", "잴"],
  "replace": ["측정", "확인", "관측", "계산"],
  "scope": ["answer", "artifact", "living-doc"],
  "enabled": true,
  "evidence": { "kind": "user", "date": "2026-08-30",
                "quote": "재다 -> 측정하다 오히려 더 편한 말이야" }
}
```

| 칸 | 뜻 |
|---|---|
| `banned` | 찾을 글자. 소비자는 이 글자가 들어 있는 문장을 찾습니다 |
| `match` | `fragment` 는 어간만 적으면 되고, `forms` 는 활용형을 모두 적을 책임이 있습니다. 찾는 방식은 같습니다 |
| `replace` | 바꿔 쓸 말. 한자어 명사형으로 적습니다 |
| `instruction` | 바꿔 쓸 말이 없고 지시로만 표현되는 항목에 `replace` 대신 씁니다 |
| `scope` | 적용 대상. `answer` 는 답, `artifact` 는 산출물 문서, `living-doc` 은 저장소의 살아 있는 문서입니다 |
| `enabled` | `false` 면 검사 대상이 아닙니다. 지우지 않고 `disabled_reason` 과 함께 남깁니다 |
| `evidence` | `user`·`measured`·`reasoned`·`none` 넷. 앞의 둘에는 날짜와 원문이 따라붙습니다 |
| `rules` | 금지어와 대체어 쌍으로 표현되지 않는 규칙. 단어를 찾는 소비자는 건너뜁니다 |
| `notice` | 목록을 어떻게 쓰는지 알리는 문구. 두 생성물의 머리에 그대로 들어갑니다 |

어간을 적을 때 한글은 음절이 한 글자입니다. `맞대` 가 `맞대고` 는 품지만 `맞댄` 은 품지 않으므로 어간을 여럿 적습니다. 반대로 다른 단어에 나타나는 어간은 뺍니다. `가르다` 에 `가르` 를 넣으면 `가르치다` 까지 검출됩니다.

## 공용 import 규약

목록을 싣는 플러그인이 둘 이상일 때 `~/.claude/CLAUDE.md` 에 목록이 한 번만 실리게 하는 규약을 이 저장소가 소유합니다. [import-protocol.md](import-protocol.md) 에 있고 아직 채택 전입니다.

## 고치는 방법

```
python render.py
python validate.py
python render.py --check
```

`korean-banned-words.json` 과 `updated` 날짜를 고친 뒤 `render.py` 를 돌려 `dist/` 를 다시 만들고, 두 검사가 통과하면 데이터와 `dist/` 를 함께 커밋해 PR 을 엽니다. `dist/` 를 빼고 올리면 CI 의 `--check` 가 실패합니다.

항목을 새로 넣을 때는 `evidence` 를 채우고, 근거를 찾지 못했으면 `none` 으로 적습니다.

소비자 저장소는 GitHub Actions 로 하루 한 번 `dist/` 의 자기 파일을 받아 자기 저장소에 PR 을 엽니다. 이 저장소가 밀어 넣으면 접근 토큰을 보관해야 하므로 받아 가는 쪽으로 두었습니다.

```
https://raw.githubusercontent.com/KiwoomAX/korean-banned-words/main/dist/korean-banned-words.md
```
