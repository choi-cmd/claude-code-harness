# 서블리원 아크릴 주문제작 프로그램 - 최신 컨텍스트

> 마지막 업데이트: 2026-02-15

## 프로젝트 개요

서블리원 아크릴 레이저 커팅 주문제작 웹 앱. FastAPI + Jinja2 + HTMX 기반.
JSON 파일 저장소 (DB 없음). Render 배포 완료.

## 배포 정보

- **URL (고객)**: https://sublione-custom.onrender.com
- **URL (관리자)**: https://sublione-custom.onrender.com/admin/login
- **관리자 비밀번호**: admin1234
- **GitHub**: https://github.com/choi-cmd/claude-code-harness.git
- **호스팅**: Render (무료 플랜, GitHub 연동 자동 배포)
- **PWA**: 고객용 "Custom Order" + 관리자용 "Custom Order" (관리 배지 아이콘)

## 주요 기능

### 고객 페이지 (/)
1. **이미지 비율 계산** - PNG 투명배경 감지, 자동/수동 크기 계산
2. **자동 크기 계산** - 체크박스로 이미지 픽셀→mm 변환
3. **단가 계산** - 가로/세로/수량 입력 → 단가, 최소수량, 샘플비 계산
4. **주문 신청** - 별도 페이지로 분리 (계산기 → 주문폼 전환)
5. **작업틀 옵션** - +10,000원 (VAT별도)
6. **제작 불가 검증** - 406mm × 609mm 초과 시 에러
7. **비율 계산 후 크기 readOnly** - 임의 변경 불가

### 관리자 페이지 (/admin)
1. **주문 목록** - 필터(전체/대기중/완료), 체크박스 선택
2. **일괄 처리** - 완료/대기 상태 변경
3. **다운로드** - CSV + 첨부파일 ZIP 묶음
4. **파일 미리보기** - 모달로 이미지 미리보기
5. **개별 파일 다운로드**

## 파일 구조 (핵심)

```
src/
├── main.py                          # FastAPI 앱 엔트리
├── api/v1/endpoints/
│   ├── admin.py                     # 관리자 API (로그인, 주문관리, CSV/ZIP 다운로드)
│   ├── image.py                     # 이미지 업로드 + 비율 계산
│   └── order.py                     # 주문 접수
├── domain/
│   ├── calculator/                  # 단가 계산 로직
│   └── order/                       # 주문 스키마/서비스/레포지토리
├── templates/
│   ├── base.html                    # 기본 레이아웃 (PWA 블록 분리)
│   ├── calculator.html              # 메인 페이지 (계산기 + 주문폼)
│   ├── admin/                       # 관리자 페이지들
│   └── partials/                    # HTMX 파셜 (result, image_ratio, order_success)
├── static/
│   ├── manifest.json                # 고객 PWA
│   ├── manifest-admin.json          # 관리자 PWA
│   ├── sw.js                        # 서비스워커 (v2)
│   └── images/                      # 로고, 아이콘 (일반/관리자)
data/
└── orders.json                      # 주문 데이터 저장소
```

## 최근 작업 이력

1. 주문폼 별도 페이지 분리 (계산기 ↔ 주문 전환)
2. 주문 완료 후 폼 숨김 (중복 제출 방지)
3. VAT 포함 최종 금액 표시 (작업틀 비용 포함)
4. 관리자 CSV + 첨부파일 ZIP 다운로드
5. 모바일 반응형 전면 개선 (요약바, 힌트, 섹션헤더, 관리자 테이블)
6. PWA 고객/관리자 분리 (별도 manifest, 관리자 배지 아이콘)
7. 주문 완료 화면 리디자인 (SVG 체크 아이콘, flex 레이아웃)
8. 앱 이름 "Custom Order" 통일
9. 제작 불가 크기 검증 + readOnly 필드

## 알려진 이슈 / TODO

- Render 무료 플랜: 15분 미접속 시 sleep (첫 접속 30초 지연)
- data/orders.json: Render 재배포 시 초기화됨 (영구 저장 필요시 Render Disk 추가)
- 서버 프로세스 관리: Windows에서 uv 경로 = `C:\Users\LKN\AppData\Local\Python\pythoncore-3.14-64\Scripts\uv.exe`
