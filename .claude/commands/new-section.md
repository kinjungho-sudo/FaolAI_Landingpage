# 새 섹션 추가

다음 요청에 맞는 새 섹션을 index.html에 추가해주세요: $ARGUMENTS

## 실행 순서

1. **index.html을 먼저 읽어** 현재 섹션 순서, 스타일, 패턴을 파악한다
2. **CLAUDE.md를 참고**해 디자인 시스템(색상, 폰트, 간격)을 그대로 따른다
3. 아래 섹션 템플릿과 체크리스트를 기준으로 섹션을 작성한다
4. 작성 후 **git commit & push**한다

---

## 섹션 구조 템플릿

```html
<!-- 섹션명 -->
<section class="[name]-section">
  <div class="[name]-inner">
    <div class="sec-label reveal">레이블 텍스트</div>
    <h2 class="sec-h2 reveal reveal-delay-1">헤딩</h2>
    <p class="sec-desc reveal reveal-delay-2">설명</p>
    <!-- 본문 콘텐츠 -->
  </div>
</section>
```

## CSS 템플릿

```css
/* 밝은 배경 섹션 */
.[name]-section { padding: 80px 32px; background: #fff; }
.[name]-inner { max-width: 1200px; margin: 0 auto; }

/* 어두운 배경 섹션 */
.[name]-section { padding: 80px 32px; background: #0B0D14; color: #fff; }
.[name]-section .sec-h2 { color: #fff; }
.[name]-section .sec-label { color: #A78BFF; }
.[name]-section .sec-desc { color: rgba(255,255,255,0.45); }

/* 카드 그리드 (3열) */
.[name]-cards { display: grid; grid-template-columns: repeat(3,1fr); gap: 22px; margin-top: 48px; }
.[name]-card { border: 1.5px solid #EDEAF8; border-radius: 16px; padding: 28px 24px; }

/* 좌우 분할 */
.[name]-inner { display: grid; grid-template-columns: 1fr 1fr; gap: 64px; align-items: center; }

/* 모바일 필수 */
@media (max-width: 640px) {
  .[name]-section { padding: 60px 20px; }
  .[name]-cards { grid-template-columns: 1fr; }
}
```

## 체크리스트

- [ ] CLAUDE.md의 색상/폰트/간격 사용
- [ ] `max-width` + `margin: 0 auto`로 중앙 정렬
- [ ] `.reveal` 클래스로 스크롤 애니메이션 적용
- [ ] 640px 이하 모바일 CSS 포함
- [ ] 기존 섹션과 자연스럽게 연결되는 배경색 선택
- [ ] git commit & push 완료