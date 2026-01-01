# 표기 규칙 (Notation Rules)

구문분석 시 사용하는 괄호, 밑줄, 라벨, 화살표 등의 표기 규칙입니다.

---

## 1. 괄호 체계 (Bracket System)

### 1.1 소괄호 ( )

**용도**: 수식어구, 전치사구

```
I met a girl (with blue eyes).
             ───────────────
               전치사구(수식)
```

**사용 대상**:
- 전치사구: *(in the park)*, *(with a smile)*
- 현재분사구: *(running fast)*
- 과거분사구: *(written by him)*
- 형용사구: *(very tall)*
- 부사구: *(very quickly)*
- to부정사구(형/부): *(to study English)*

### 1.2 대괄호 [ ]

**용도**: 절 (Clause)

```
I know [that he is honest].
       ────────────────────
            명사절(목적어)
```

**사용 대상**:
- 명사절: *[that S+V]*, *[what S+V]*, *[whether S+V]*
- 형용사절(관계절): *[who/which/that S+V]*
- 부사절: *[when/if/because S+V]*

### 1.3 중괄호 { }

**용도**: 삽입구, 동격

```
Tom, {my best friend}, is a doctor.
     ─────────────────
          동격(삽입)
```

**사용 대상**:
- 동격 명사구: *{my friend}*
- 삽입절: *{I think}*, *{as you know}*
- 부연 설명: *{that is}*, *{for example}*

### 1.4 괄호 중첩 규칙

바깥에서 안쪽으로: `[ ] → ( ) → { }`

```
[The man (who lives {next door}) is kind].
```

---

## 2. 밑줄 체계 (Underline System)

### 2.1 마크다운 표현

| 스타일 | 마크다운 | 용도 |
|--------|----------|------|
| **굵게** | `**text**` | 핵심 성분 (S, V) |
| *기울임* | `*text*` | 보조 성분 (O, C) |
| `코드` | `` `text` `` | 문법 포인트/오류 |
| ~~취소선~~ | `~~text~~` | 생략 가능 요소 |

### 2.2 코드블록 밑줄

구조도에서는 유니코드 밑줄 문자 사용:

```
The boy   runs   fast.
───────   ────   ─────
   S        V      M
```

**밑줄 문자**:
- `─` (Box Drawing): 일반 밑줄
- `═` (Double Line): 강조 밑줄
- `~` (Tilde): 물결 밑줄 (수식어)

### 2.3 성분별 밑줄 길이

- 단어 단위: 해당 단어 길이만큼
- 구/절 단위: 전체 범위 표시

```
[The tall boy (in the room)] likes music.
 ─────────────────────────── ───── ──────
           S(주어부)           V      O
```

---

## 3. 라벨 체계 (Label System)

### 3.1 문장 성분 라벨

| 라벨 | 영문 | 한글 | 설명 |
|:----:|------|------|------|
| **S** | Subject | 주어 | 동작/상태의 주체 |
| **V** | Verb | 동사 | 서술어 |
| **O** | Object | 목적어 | 동작의 대상 |
| **IO** | Indirect Object | 간접목적어 | ~에게 |
| **DO** | Direct Object | 직접목적어 | ~을/를 |
| **C** | Complement | 보어 | 주어/목적어 보충 |
| **SC** | Subject Complement | 주격보어 | S = C |
| **OC** | Object Complement | 목적격보어 | O = OC |
| **M** | Modifier | 수식어 | 부가 설명 |

### 3.2 품사 라벨

| 라벨 | 영문 | 한글 |
|:----:|------|------|
| n. | noun | 명사 |
| v. | verb | 동사 |
| adj. | adjective | 형용사 |
| adv. | adverb | 부사 |
| prep. | preposition | 전치사 |
| conj. | conjunction | 접속사 |
| pron. | pronoun | 대명사 |

### 3.3 절 종류 라벨

| 라벨 | 영문 | 한글 |
|:----:|------|------|
| NC | Noun Clause | 명사절 |
| AC | Adjective Clause | 형용사절 |
| AVC | Adverb Clause | 부사절 |
| RC | Relative Clause | 관계절 |

### 3.4 준동사 라벨

| 라벨 | 형태 | 기능 |
|:----:|------|------|
| to-v | to부정사 | 명/형/부 |
| v-ing | 현재분사/동명사 | 형용사/명사 |
| p.p. | 과거분사 | 형용사/수동 |

---

## 4. 화살표 체계 (Arrow System)

### 4.1 수식 관계

```
↳  아래 방향 수식
↓  직접 수식
```

**예시**:
```
The book (which I bought)
              ↳ book 수식
```

### 4.2 변환/수정

```
→  원본 → 수정
```

**예시**:
```
knows → know (수일치 오류)
```

### 4.3 참조 관계

```
⟵  역참조 (선행사)
⟶  순참조
```

**예시**:
```
the book which I bought
    ↑         ↓
  선행사 ⟵── 관계대명사
```

### 4.4 생략 표시

```
Ø  생략된 요소
△  생략 가능
```

**예시**:
```
The book [Ø I bought] is good.
          ↳ 목적격 관계대명사 생략
```

---

## 5. 특수 표기 (Special Notations)

### 5.1 오류 표시

```
❌  틀린 부분
✓   올바른 형태
```

**예시**:
```
He `play` → plays ❌ 수일치 오류
```

### 5.2 문법 포인트 강조

```
★  핵심 포인트
⚠️  주의 사항
💡  팁/참고
```

### 5.3 형식 표시

```
[1형식] S + V
[2형식] S + V + C
[3형식] S + V + O
[4형식] S + V + IO + DO
[5형식] S + V + O + OC
```

---

## 6. 색상 코딩 (선택)

디지털 환경에서 색상 사용 시:

| 색상 | 용도 | HTML |
|------|------|------|
| 🔵 파랑 | 주어 | `<span style="color:blue">` |
| 🔴 빨강 | 동사 | `<span style="color:red">` |
| 🟢 초록 | 목적어 | `<span style="color:green">` |
| 🟡 노랑 | 보어 | `<span style="color:orange">` |
| ⚫ 회색 | 수식어 | `<span style="color:gray">` |

---

## 7. 호환성 참고

### 마크다운 호환

| 플랫폼 | 호환성 |
|--------|--------|
| GitHub | ✅ 완전 지원 |
| Notion | ✅ 완전 지원 |
| Obsidian | ✅ 완전 지원 |
| Typora | ✅ 완전 지원 |
| VS Code | ✅ 완전 지원 |

### Word 변환

마크다운 → Word 변환 시:
- 코드블록 → 고정폭 글꼴 유지
- 표 → Word 표로 변환
- 굵게/기울임 → 서식 유지
