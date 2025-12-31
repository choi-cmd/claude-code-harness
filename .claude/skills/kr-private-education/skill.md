---
name: kr-private-education
description: 대한민국 사교육(학원/과외) 도메인 지식. 학원 운영, 수강 관리, 학생/학부모 관리, 출결, 성적, 상담, 결제/환불 등 사교육 비즈니스 전반의 개념, 규칙, 패턴을 제공합니다.
---

# 대한민국 사교육 도메인 가이드

## Purpose

대한민국 사교육(학원, 교습소, 과외) 시스템 개발을 위한 도메인 지식 가이드입니다.
비즈니스 규칙, 법적 요구사항, 엔티티 모델, 워크플로우, 코드 패턴을 제공합니다.

## When to Use This Skill

- 학원 관리 시스템(LMS/CRM) 개발
- 수강 등록/결제/환불 로직 구현
- 학생/학부모 관리 기능 개발
- 출결 관리 시스템 구현
- 성적/성취도 관리 기능 개발
- 상담 관리 시스템 구현
- 학원 운영 관련 API 개발

---

## Quick Reference

### 핵심 엔티티

| 엔티티 | 설명 | 주요 속성 |
|--------|------|-----------|
| Academy | 학원/교습소 | 등록번호, 운영시간, 심야제한시간 |
| Student | 학생(수강생) | 학교, 학년, 레벨, 수강목록 |
| Parent | 학부모 | 연락처, 결제수단, 자녀목록 |
| Instructor | 강사 | 담당과목, 시급, 스케줄 |
| Class | 수업/반 | 과목, 정원, 시간표, 수강료 |
| Enrollment | 수강등록 | 시작일, 종료일, 결제상태 |
| Attendance | 출결 | 출석/결석/지각/조퇴 |
| Payment | 결제 | 금액, 수단, 환불정보 |
| Consultation | 상담 | 유형, 내용, 후속조치 |

### 핵심 워크플로우

```
상담문의 → 레벨테스트 → 반편성 → 수강등록 → 결제
    → 수업진행 → 출결관리 → 성적관리 → 정기상담
```

### 주요 비즈니스 규칙

| ID | 규칙 | 근거 |
|----|------|------|
| EDU-001 | 심야학습 제한시간 준수 (지역별 22시~24시) | 학원법 |
| EDU-002 | 환불은 수강료 환불기준표 적용 | 학원법 시행령 |
| EDU-003 | 학생 개인정보 별도 동의 필수 (만14세 미만) | 개인정보보호법 |
| EDU-004 | 수강계약서 필수 작성/보관 | 학원법 |

---

## Topic Guides

### 엔티티 모델

학원 시스템의 핵심 엔티티와 관계를 정의합니다.

**[📖 Complete Guide: resources/entities.md](resources/entities.md)**

---

### 비즈니스 규칙 & 법규

학원법, 환불규정, 운영시간 제한 등 필수 준수사항을 설명합니다.

**[📖 Complete Guide: resources/business-rules.md](resources/business-rules.md)**

---

### 주요 워크플로우

상담→등록→수업→관리까지 주요 업무 흐름을 정의합니다.

**[📖 Complete Guide: resources/workflows.md](resources/workflows.md)**

---

### 코드 패턴

사교육 도메인에 맞는 코드 패턴과 예시를 제공합니다.

**[📖 Complete Guide: resources/code-patterns.md](resources/code-patterns.md)**

---

### 용어 사전

사교육 업계 용어와 시스템 용어 매핑을 제공합니다.

**[📖 Complete Guide: resources/terminology.md](resources/terminology.md)**

---

## Navigation Guide

| 필요한 것 | 참조 리소스 |
|-----------|-------------|
| 엔티티/모델 설계 | [entities.md](resources/entities.md) |
| 법규/규칙 확인 | [business-rules.md](resources/business-rules.md) |
| 업무 흐름 이해 | [workflows.md](resources/workflows.md) |
| 코드 작성 | [code-patterns.md](resources/code-patterns.md) |
| 용어 확인 | [terminology.md](resources/terminology.md) |

---

## Core Principles

1. **학원법 준수**: 모든 기능은 학원법 및 시행령 준수
2. **개인정보 보호**: 학생/학부모 정보는 철저한 보호
3. **환불규정 명확화**: 환불 계산 로직 투명하게 구현
4. **출결 정확성**: 출결 데이터는 법적 증빙 가능해야 함
5. **학부모 소통**: 알림/상담 기능 필수
6. **성적 추적**: 학습 성취도 추적 및 리포팅

---

## 도메인 키워드

학원, 교습소, 과외, 수강, 등록, 환불, 원비, 수강료, 교재비,
학생, 수강생, 학부모, 강사, 원장, 상담사,
출결, 출석, 결석, 지각, 조퇴,
내신, 수능, 모의고사, 정시, 수시, 학생부,
반편성, 레벨테스트, 정규반, 특강, 캠프,
상담, 입학상담, 정기상담, 성적상담,
SMS, 알림톡, 학부모앱

---

## Related Skills

- **fastapi-backend-guidelines**: 백엔드 API 구현 시 참조
- **nextjs-frontend-guidelines**: 프론트엔드 구현 시 참조
- **error-tracking**: 에러 추적 설정 시 참조

---

**Skill Status**: Active - 대한민국 사교육 도메인 전문 지식
