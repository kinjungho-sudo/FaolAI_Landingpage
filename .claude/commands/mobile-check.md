# 모바일 반응형 점검 및 수정

$ARGUMENTS

점검 대상 파일이 명시되지 않은 경우 `index.html`을 기준으로 점검합니다.

## 실행 순서

1. 대상 파일을 읽어 CSS 전체 파악
2. 아래 체크리스트 기준으로 문제 항목 식별
3. 문제 항목 수정
4. git commit & push

---

## 점검 체크리스트

### 레이아웃
- [ ] 모든 그리드(`grid-template-columns: repeat(N, 1fr)`)에 640px 이하 1열 처리 있는가
- [ ] 좌우 분할 레이아웃(`1fr 1fr`)에 800-900px 이하 단일 열 처리 있는가
- [ ] 고정 너비(`width: 300px` 등)가 뷰포트보다 넓어질 수 있는 곳은 없는가
- [ ] `min-width`가 모바일에서 overflow를 일으키지 않는가

### 네비게이션
- [ ] 768px 이하에서 nav-links 숨김 처리 있는가
- [ ] hamburger 버튼 존재하는가
- [ ] 모바일 메뉴 드롭다운 동작하는가

### 섹션 패딩
- [ ] 모든 섹션이 640px 이하에서 `padding-left/right: 20px` 적용되는가
- [ ] `padding: 80px 32px` 패턴에 모바일 오버라이드 있는가

### 폰트
- [ ] 고정 폰트 크기(px)가 모바일에서 너무 크지 않은가 (`clamp()` 또는 미디어쿼리 사용)
- [ ] 큰 헤딩(38px+)에 모바일 축소 처리 있는가

### 이미지/미디어
- [ ] `aspect-ratio`가 모바일에서 적절한가 (너무 납작하면 인물 잘림)
- [ ] `object-fit: cover` 이미지의 `object-position`이 주요 피사체를 보여주는가
- [ ] 이미지가 컨테이너를 벗어나지 않는가 (`max-width: 100%`)

### 버튼/폼
- [ ] 나란히 놓인 버튼이 작은 화면에서 줄바꿈되거나 세로 스택되는가
- [ ] 입력 폼 행(`display:flex`)이 640px 이하에서 `flex-direction: column`으로 전환되는가
- [ ] 버튼 텍스트가 잘리지 않는가 (`white-space: nowrap` + 여백 확인)

### 텍스트 오버플로
- [ ] `white-space: nowrap` 사용 시 컨테이너 너비 내에서 처리되는가
- [ ] 긴 한국어 텍스트에 `word-break: keep-all` 적용 고려

### 스크롤/카루셀
- [ ] 가로 스크롤 카드에 `-webkit-overflow-scrolling: touch` 있는가
- [ ] `scroll-snap-type` 적용 시 모바일에서 자연스러운가

---

## 주요 브레이크포인트 기준 (이 프로젝트)

```
900px : 2열 → 1열, 히어로 섹션 스택
800px : BPCO 등 좌우 분할 → 1열
768px : nav hamburger 표시
760px : 데모/출력/카드 → 1열
640px : 섹션 padding → 20px, 리뷰카드 85vw
600px : CTA 폼 세로, sticky-left 숨김
480px : stats 1열, 작은 이미지 비율 조정
```

## 자주 나오는 수정 패턴

```css
/* 섹션 패딩 */
@media (max-width: 640px) {
  .section-name { padding: 60px 20px; }
}

/* 그리드 → 1열 */
@media (max-width: 640px) {
  .cards { grid-template-columns: 1fr; }
}

/* 좌우 분할 → 세로 */
@media (max-width: 900px) {
  .split { grid-template-columns: 1fr; }
}

/* 큰 헤딩 축소 */
@media (max-width: 600px) {
  .big-h2 { font-size: 26px; }
}

/* 버튼 줄바꿈 */
@media (max-width: 640px) {
  .btn-row { flex-wrap: wrap; }
}

/* 이미지 비율 조정 */
@media (max-width: 640px) {
  .panel { aspect-ratio: 4/3; object-position: center 20%; }
}
```