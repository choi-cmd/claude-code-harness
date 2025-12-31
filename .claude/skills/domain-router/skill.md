---
name: domain-router
description: 도메인 지식 자동 라우팅 및 주입. 사용자 요청을 분석하여 관련 도메인 스킬을 자동으로 활성화합니다.
---

# Domain Router

도메인 지식을 자동으로 라우팅하고 주입하는 메타 스킬입니다.

## Purpose

사용자가 특정 도메인 관련 작업을 요청할 때, 해당 도메인의 지식(개념, 규칙, 패턴)을 자동으로 컨텍스트에 주입합니다.

## How It Works

1. **키워드 감지**: 사용자 프롬프트에서 도메인 관련 키워드 탐지
2. **도메인 매칭**: 등록된 도메인 스킬과 매칭
3. **지식 주입**: 매칭된 도메인의 규칙/패턴을 컨텍스트에 로드
4. **작업 수행**: 도메인 지식을 적용하여 작업 완료

## Registered Domains

| 도메인 | 스킬 | 트리거 키워드 |
|--------|------|---------------|
| 사교육 | kr-private-education | 학원, 수강, 학생, 출결, 환불... |
| FastAPI 백엔드 | fastapi-backend-guidelines | backend, route, service... |
| Next.js 프론트엔드 | nextjs-frontend-guidelines | component, page, MUI... |

## Usage

### 자동 활성화

```
사용자: "학원 수강등록 API를 만들어줘"
       │
       ▼
  키워드 감지: "학원", "수강등록"
       │
       ▼
  도메인 매칭: kr-private-education
       │
       ▼
  지식 주입:
  - 엔티티: Student, Enrollment, Class
  - 규칙: EDU-002 (환불규정), EDU-004 (수강계약서)
  - 패턴: EnrollmentService 코드 패턴
       │
       ▼
  작업 수행: 도메인 규칙을 준수하는 API 생성
```

### 수동 활성화

```bash
# 특정 도메인 강제 활성화
/domain:use kr-private-education

# 도메인 목록 확인
/domain:list

# 현재 활성 도메인 확인
/domain:active
```

## Domain Registration

새 도메인을 등록하려면:

1. `.claude/skills/{domain-name}/` 디렉토리 생성
2. `skill.md` 작성 (메인 스킬 파일)
3. `resources/` 폴더에 지식 파일 작성
   - `entities.md`: 엔티티 모델
   - `business-rules.md`: 비즈니스 규칙
   - `workflows.md`: 워크플로우
   - `code-patterns.md`: 코드 패턴
   - `terminology.md`: 용어 사전
4. `skill-rules.json`에 트리거 등록

## Domain Matching Algorithm

```python
def match_domain(prompt: str, domains: List[Domain]) -> List[Domain]:
    """프롬프트에서 관련 도메인 매칭"""

    matched = []

    for domain in domains:
        score = 0

        # 키워드 매칭
        for keyword in domain.keywords:
            if keyword in prompt:
                score += 1

        # 의도 패턴 매칭
        for pattern in domain.intent_patterns:
            if re.match(pattern, prompt):
                score += 2

        # 임계값 초과 시 매칭
        if score >= domain.threshold:
            matched.append((domain, score))

    # 점수순 정렬
    return sorted(matched, key=lambda x: x[1], reverse=True)
```

## Best Practices

### 도메인 지식 작성 시

1. **구체적인 예시 포함**: 추상적 설명보다 실제 코드/데이터 예시
2. **비즈니스 규칙 명확화**: ID 부여, 근거 명시 (법률, 정책 등)
3. **용어 일관성**: terminology.md에 용어 매핑 정의
4. **패턴 재사용성**: 복사-붙여넣기 가능한 코드 패턴

### 트리거 설정 시

1. **핵심 키워드 우선**: 도메인 특화 용어 우선 등록
2. **의도 패턴 활용**: 정규식으로 다양한 표현 커버
3. **파일 트리거 활용**: 관련 파일 수정 시 자동 활성화
4. **우선순위 설정**: 도메인 간 충돌 방지

## Integration with Other Skills

Domain Router는 다른 스킬과 함께 동작합니다:

```
[Domain Router]
     ↓
도메인 지식 주입 (kr-private-education)
     ↓
[fastapi-backend-guidelines]
     ↓
도메인 규칙 + 백엔드 패턴 결합
     ↓
최종 코드 생성
```

## Examples

### 학원 수강등록 API 요청

**입력**: "학원 수강등록 API를 만들어줘"

**Domain Router 동작**:
1. 키워드 감지: `학원`, `수강등록`
2. 도메인 매칭: `kr-private-education` (score: 2)
3. 지식 로드:
   - `entities.md` → Enrollment, Student, Class 모델
   - `business-rules.md` → EDU-002 (환불규정), EDU-004 (계약서)
   - `workflows.md` → WF-002 (수강등록 플로우)
   - `code-patterns.md` → EnrollmentService 패턴

**출력**: 환불규정 준수, 수강계약서 생성이 포함된 API

### 출결 체크 기능 요청

**입력**: "학생 출결 체크 기능 구현해줘"

**Domain Router 동작**:
1. 키워드 감지: `학생`, `출결`
2. 도메인 매칭: `kr-private-education` (score: 2)
3. 지식 로드:
   - `entities.md` → Attendance 모델
   - `business-rules.md` → EDU-005 (출결 관리)
   - `workflows.md` → WF-003 (출결 관리 플로우)

**출력**: 출석/지각/결석 판정, 학부모 알림이 포함된 기능

---

## Related Skills

- **skill-developer**: 새 도메인 스킬 생성 시 참조
- **kr-private-education**: 사교육 도메인 지식
- **fastapi-backend-guidelines**: 백엔드 구현 패턴
