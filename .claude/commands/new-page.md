# 새 페이지 생성

다음 요청에 맞는 새 HTML 페이지를 생성해주세요: $ARGUMENTS

## 실행 순서

1. **index.html의 nav, footer, 공통 CSS 패턴**을 읽어 파악한다
2. **CLAUDE.md**를 참고해 디자인 시스템을 그대로 따른다
3. 아래 템플릿을 기반으로 새 페이지를 작성한다
4. **index.html nav**에 새 페이지 링크를 추가한다 (필요 시)
5. **git commit & push**한다

---

## 페이지 전체 템플릿

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>[페이지명] — Foal AI</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800;900&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Noto Sans KR', sans-serif; background: #fff; color: #111; -webkit-font-smoothing: antialiased; }

    /* ── NAV (공통) ── */
    .nav {
      position: sticky; top: 0; z-index: 50;
      background: rgba(255,255,255,0.96); backdrop-filter: blur(12px);
      border-bottom: 1px solid #F0EFF8; height: 64px;
      display: flex; align-items: center; padding: 0 32px;
    }
    .nav-inner { max-width: 1200px; width: 100%; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; }
    .logo { font-size: 22px; font-weight: 900; letter-spacing: -0.05em; display: flex; align-items: center; gap: 8px; text-decoration: none; color: #111; }
    .logo-img { height: 32px; width: auto; }
    .logo span { color: #6B3CF7; }
    .nav-links { display: flex; gap: 20px; }
    .nav-link { font-size: 14px; font-weight: 700; color: #555; text-decoration: none; transition: color 0.2s; }
    .nav-link:hover { color: #6B3CF7; }
    .nav-link.active { color: #6B3CF7; }
    .nav-btn { padding: 9px 22px; background: #6B3CF7; color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 700; font-family: inherit; cursor: pointer; text-decoration: none; transition: background 0.2s; }
    .nav-btn:hover { background: #5428E0; }
    /* Hamburger */
    .nav-hamburger { display: none; flex-direction: column; gap: 5px; cursor: pointer; background: none; border: none; padding: 6px 4px; }
    .nav-hamburger span { display: block; width: 22px; height: 2px; background: #333; border-radius: 2px; transition: transform 0.25s, opacity 0.25s; }
    .nav-hamburger.open span:nth-child(1) { transform: translateY(7px) rotate(45deg); }
    .nav-hamburger.open span:nth-child(2) { opacity: 0; }
    .nav-hamburger.open span:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }
    .nav-mobile-menu { display: none; position: absolute; top: 64px; left: 0; right: 0; background: rgba(255,255,255,0.98); backdrop-filter: blur(12px); border-bottom: 1px solid #F0EFF8; flex-direction: column; padding: 8px 20px 16px; z-index: 49; box-shadow: 0 8px 24px rgba(0,0,0,0.08); }
    .nav-mobile-menu.open { display: flex; }
    .nav-mobile-menu .nav-link { padding: 13px 0; font-size: 15px; border-bottom: 1px solid #F5F4F8; display: block; }
    .nav-mobile-menu .nav-link:last-child { border-bottom: none; }
    @media (max-width: 768px) {
      .nav-links { display: none; }
      .nav-hamburger { display: flex; }
      .nav-btn { font-size: 13px; padding: 8px 16px; }
      .nav { padding: 0 20px; }
    }

    /* ── PAGE HERO ── */
    .page-hero {
      background: linear-gradient(155deg, #0C0A1E 0%, #170F3A 40%, #0E1628 100%);
      padding: 72px 32px 64px; color: #fff;
    }
    .hero-inner { max-width: 1200px; margin: 0 auto; }
    .hero-label {
      display: inline-block; background: rgba(107,60,247,0.15); color: #A78BFF;
      font-size: 11px; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase;
      padding: 5px 12px; border-radius: 20px; margin-bottom: 16px;
    }
    .hero-h1 { font-size: clamp(28px, 4vw, 48px); font-weight: 900; letter-spacing: -0.04em; line-height: 1.2; margin-bottom: 12px; }
    .hero-sub { font-size: 16px; color: rgba(255,255,255,0.55); line-height: 1.7; }

    /* ── MAIN CONTENT ── */
    .main { max-width: 1200px; margin: 0 auto; padding: 60px 32px 100px; }

    /* ── FOOTER ── */
    footer { background: #0A0A14; color: rgba(255,255,255,0.35); padding: 28px 32px; text-align: center; font-size: 12px; }

    /* ── MOBILE ── */
    @media (max-width: 640px) {
      .page-hero { padding: 48px 20px 40px; }
      .main { padding: 40px 20px 80px; }
    }

    /* ── 페이지 고유 스타일 ── */
    /* TODO: 여기에 페이지별 CSS 추가 */

  </style>
</head>
<body>

<nav class="nav">
  <div class="nav-inner">
    <a href="index.html" class="logo">
      <img src="images/Logo.png" alt="Foal AI" class="logo-img" onerror="this.style.display='none'">
      Foal<span>AI</span>
    </a>
    <div class="nav-links">
      <a href="index.html" class="nav-link">홈</a>
      <a href="announcements.html" class="nav-link">공고마당</a>
      <a href="guide.html" class="nav-link">사업계획서 작성가이드</a>
      <a href="inquiry.html" class="nav-link">문의하기</a>
    </div>
    <button class="nav-hamburger" id="nav-hamburger" onclick="toggleNav()" aria-label="메뉴">
      <span></span><span></span><span></span>
    </button>
    <a href="index.html" class="nav-btn">관심 등록하기</a>
  </div>
  <div class="nav-mobile-menu" id="nav-mobile-menu">
    <a href="index.html" class="nav-link">홈</a>
    <a href="announcements.html" class="nav-link">공고마당</a>
    <a href="guide.html" class="nav-link">사업계획서 작성가이드</a>
    <a href="inquiry.html" class="nav-link">문의하기</a>
  </div>
</nav>

<div class="page-hero">
  <div class="hero-inner">
    <div class="hero-label">레이블</div>
    <h1 class="hero-h1">페이지 제목</h1>
    <p class="hero-sub">페이지 설명</p>
  </div>
</div>

<div class="main">
  <!-- TODO: 본문 내용 -->
</div>

<footer>
  <p>© 2026 Foal AI. All rights reserved.</p>
</footer>

<script>
function toggleNav(){
  var btn = document.getElementById('nav-hamburger');
  var menu = document.getElementById('nav-mobile-menu');
  btn.classList.toggle('open');
  menu.classList.toggle('open');
}
document.querySelectorAll('#nav-mobile-menu .nav-link').forEach(function(a){
  a.addEventListener('click', function(){
    document.getElementById('nav-hamburger').classList.remove('open');
    document.getElementById('nav-mobile-menu').classList.remove('open');
  });
});
document.addEventListener('click', function(e){
  var menu = document.getElementById('nav-mobile-menu');
  var btn = document.getElementById('nav-hamburger');
  if(menu && menu.classList.contains('open') && !menu.contains(e.target) && !btn.contains(e.target)){
    menu.classList.remove('open');
    btn.classList.remove('open');
  }
});
</script>
</body>
</html>
```

## 체크리스트

- [ ] 파일명은 영어 소문자 + 하이픈 (예: `my-page.html`)
- [ ] `<title>`, `hero-label`, `hero-h1`, `hero-sub` 내용 채우기
- [ ] `nav-link.active` 현재 페이지에 적용
- [ ] index.html nav의 `.nav-links`, `.nav-mobile-menu` 양쪽에 링크 추가
- [ ] 모바일 CSS 포함 확인
- [ ] git commit & push 완료