"""
공고 데이터 크롤러 v3
- 소스 1: mss.go.kr       중소벤처기업부 사업공고
- 소스 2: k-startup.go.kr  K-Startup 지원사업 공고
- 소스 3: bizinfo.go.kr    지원사업 통합 목록
- 출력: data/announcements.json
- 스케줄: GitHub Actions (매주 월요일 23:00 KST = 14:00 UTC)
"""

import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "announcements.json"
TODAY = datetime.now().strftime("%Y-%m-%d")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ─────────────────────────────────────────────
# 공통 유틸
# ─────────────────────────────────────────────

def safe_get(session, url, timeout=20):
    try:
        r = session.get(url, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"    [GET 실패] ...{url[-50:]} -> {e}")
        return None


def make_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def infer_category(text: str) -> list:
    cats = []
    if re.search(r"예비\s*창업|창업\s*준비|모두의\s*창업", text):
        cats.append("예비창업")
    if re.search(r"초기\s*창업|업력\s*[1-5]년|창업\s*[1-5]년", text):
        cats.append("초기창업")
    if re.search(r"재도전|재\s*창업", text):
        cats.append("재도전")
    if re.search(r"청년|만\s*3[0-9]세|대학생|졸업", text):
        cats.append("청년")
    if re.search(r"기술창업|딥테크|R&D|기술개발|특허", text):
        cats.append("기술창업")
    if re.search(r"소상공인|자영업", text):
        cats.append("소상공인")
    return cats if cats else ["창업"]


def infer_amount(text: str) -> str:
    m = re.search(r"최대\s*([\d,]+)\s*(억|만)원", text)
    if m:
        return f"최대 {m.group(1)}{m.group(2)}원"
    m = re.search(r"([\d,]+)\s*(억|만)원\s*이내", text)
    if m:
        return f"최대 {m.group(1)}{m.group(2)}원"
    return "공고 확인"


def parse_deadline(text: str):
    """YYYY.MM.DD ~ YYYY.MM.DD 또는 D-N 형식 파싱 -> (표시, ISO)"""
    # 범위에서 종료일 추출
    m = re.search(
        r"\d{4}[-./년]\s*\d{1,2}[-./월]\s*\d{1,2}[일]?\s*[~\-]\s*"
        r"(\d{4})[-./년]\s*(\d{1,2})[-./월]\s*(\d{1,2})",
        text,
    )
    if m:
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return dt.strftime("%Y.%m.%d"), dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # 단일 날짜
    m = re.search(r"(\d{4})[-./년]\s*(\d{1,2})[-./월]\s*(\d{1,2})", text)
    if m:
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return dt.strftime("%Y.%m.%d"), dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return "상시", "9999-12-31"


def deadline_from_dday(dday_str: str):
    """D-N -> 날짜 계산"""
    m = re.search(r"D-(\d+)", dday_str)
    if m:
        dt = datetime.now() + timedelta(days=int(m.group(1)))
        return dt.strftime("%Y.%m.%d"), dt.strftime("%Y-%m-%d")
    return "상시", "9999-12-31"


def is_startup_related(title: str) -> bool:
    keywords = [
        "창업", "스타트업", "벤처", "소상공인", "사업화", "아이디어",
        "예비", "초기", "재도전", "청년", "TIPS", "팁스", "지원사업",
        "공모", "모집", "기술개발", "글로벌", "경진대회",
    ]
    return any(k in title for k in keywords)


def make_id(prefix: str, title: str) -> str:
    return f"{prefix}_{abs(hash(title[:30])) % 999999:06d}"


# ─────────────────────────────────────────────
# 소스 1: 중소벤처기업부 (mss.go.kr)
# 구조: 테이블, onclick="doBbsFView('310','bcIdx','Gbn','parentSeq')"
# ─────────────────────────────────────────────

MSS_BASE = "https://www.mss.go.kr"
MSS_LIST = f"{MSS_BASE}/site/smba/ex/bbs/List.do?cbIdx=310&pageIndex="


def fetch_mss(pages: int = 2) -> list:
    print("  [1/3] mss.go.kr 크롤링 중...")
    s = make_session()
    items = []

    for page in range(1, pages + 1):
        r = safe_get(s, MSS_LIST + str(page))
        if not r:
            continue
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "lxml")

        # onclick="doBbsFView('310','1066726','16010100','1066726')"
        onclick_els = soup.find_all(onclick=re.compile(r"doBbsFView"))

        for el in onclick_els:
            oc = el.get("onclick", "")
            # 단일/이중 따옴표 모두 처리
            m = re.search(
                r"doBbsFView\(\s*['\"]?(\d+)['\"]?\s*,\s*['\"]?(\d+)['\"]?\s*,"
                r"\s*['\"]?(\w+)['\"]?\s*,\s*['\"]?(\d+)['\"]?\s*\)",
                oc,
            )
            if not m:
                continue

            bc_idx, parent_seq = m.group(2), m.group(4)
            detail_url = (
                f"{MSS_BASE}/site/smba/ex/bbs/View.do"
                f"?cbIdx=310&bcIdx={bc_idx}&parentSeq={parent_seq}"
            )

            # 제목: onclick 엘리먼트 텍스트에서 숫자/메타 제거
            raw_text = el.get_text(" ", strip=True)
            # "2037올해의 K-스타트업 2026 ... 담당부서신산업기술창업과공고번호..."
            title = re.split(r"담당부서|공고번호|신청기간|첨부파일", raw_text)[0]
            title = re.sub(r"^\d+", "", title).strip()  # 앞 숫자 제거
            if not title or not is_startup_related(title):
                continue

            # 날짜: 텍스트 전체에서 파싱
            deadline_str, deadline_date = parse_deadline(raw_text)

            # 담당부서
            org_m = re.search(r"담당부서(.{2,12}?)(공고번호|신청기간|$)", raw_text)
            org = org_m.group(1).strip() if org_m else "중소벤처기업부"

            items.append({
                "id": make_id("mss", title),
                "title": title,
                "org": f"중소벤처기업부 · {org}" if org != "중소벤처기업부" else org,
                "category": infer_category(title),
                "amount": infer_amount(title),
                "deadline": deadline_str,
                "deadlineDate": deadline_date,
                "description": f"중소벤처기업부 사업공고입니다. 자세한 내용은 공식 사이트에서 확인하세요.",
                "url": detail_url,
            })

        time.sleep(1)

    print(f"      -> {len(items)}건 수집")
    return items


# ─────────────────────────────────────────────
# 소스 2: K-Startup (k-startup.go.kr)
# 구조: li 카드, onclick="javascript:go_view_blank(pbancSn)"
# ─────────────────────────────────────────────

KST_BASE = "https://www.k-startup.go.kr"
KST_LIST = f"{KST_BASE}/web/contents/bizpbanc-ongoing.do?schM=list&page="


def fetch_kstartup(pages: int = 3) -> list:
    print("  [2/3] k-startup.go.kr 크롤링 중...")
    s = make_session()
    items = []
    seen_sns = set()

    for page in range(1, pages + 1):
        r = safe_get(s, KST_LIST + str(page))
        if not r:
            continue
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "lxml")

        # onclick="javascript:go_view_blank(176910)"
        els = soup.find_all(onclick=re.compile(r"go_view"))

        for el in els:
            oc = el.get("onclick", "")
            sn_m = re.search(r"go_view\w*\((\d+)\)", oc)
            if not sn_m:
                continue
            pbanc_sn = sn_m.group(1)
            if pbanc_sn in seen_sns:
                continue
            seen_sns.add(pbanc_sn)

            # 부모 li에서 전체 텍스트 추출
            container = el.find_parent("li") or el.find_parent("div") or el
            container_text = container.get_text(" ", strip=True)

            # 제목: "행사ㆍ네트워크 D-157 [제목] 새로운게시글 [기관명]..." 패턴
            # 분야 태그와 D-N 이후가 제목
            title_m = re.search(
                r"D-\d+\s+(.+?)(?:새로운게시글|$)",
                container_text,
            )
            if title_m:
                title = title_m.group(1).strip()
            else:
                # 분야 태그 없는 경우 el 텍스트 사용
                title = el.get_text(strip=True)

            if not title or len(title) < 4:
                continue

            # D-day로 마감일 계산
            dday_m = re.search(r"D-(\d+)", container_text)
            if dday_m:
                deadline_str, deadline_date = deadline_from_dday(f"D-{dday_m.group(1)}")
            else:
                deadline_str, deadline_date = parse_deadline(container_text)

            # 기관명 (제목 다음 텍스트)
            org = "창업진흥원"
            after_new = re.split(r"새로운게시글", container_text)
            if len(after_new) > 1:
                org_text = after_new[1].strip()
                org = re.split(r"\s{2,}|등록일자|\d{4}-\d{2}", org_text)[0].strip()
                if not org or len(org) < 2:
                    org = "창업진흥원"

            items.append({
                "id": make_id("kst", title),
                "title": title,
                "org": org,
                "category": infer_category(container_text),
                "amount": infer_amount(container_text),
                "deadline": deadline_str,
                "deadlineDate": deadline_date,
                "description": f"K-Startup 공고입니다. 자세한 내용은 k-startup.go.kr에서 확인하세요.",
                "url": (
                    f"{KST_BASE}/web/contents/bizpbanc-ongoing.do"
                    f"?schM=view&pbancSn={pbanc_sn}"
                ),
            })

        time.sleep(1)

    print(f"      -> {len(items)}건 수집")
    return items


# ─────────────────────────────────────────────
# 소스 3: BizInfo (bizinfo.go.kr)
# 구조: 테이블, href에 pblancId=PBLN_* 포함
# ─────────────────────────────────────────────

BIZ_BASE = "https://www.bizinfo.go.kr"
BIZ_LIST = (
    f"{BIZ_BASE}/web/lay1/bbs/S1T122C128/AS/74/list.do"
    "?schEndAt=N&pageUnit=20&pageIndex="
)


def fetch_bizinfo(pages: int = 3) -> list:
    print("  [3/3] bizinfo.go.kr 크롤링 중...")
    s = make_session()
    # 세션 쿠키 획득
    safe_get(s, BIZ_BASE + "/", timeout=10)
    items = []

    for page in range(1, pages + 1):
        r = safe_get(s, BIZ_LIST + str(page))
        if not r:
            continue
        r.encoding = "utf-8"

        # href에서 pblancId=PBLN_* 직접 정규식 추출
        # 패턴: pblancId=PBLN_000000000120020" title="[제목]">[제목]
        row_pattern = re.compile(
            r'href="[^"]*pblancId=(PBLN_\d+)[^"]*"\s+title="([^"]+)"'
        )

        soup = BeautifulSoup(r.text, "lxml")
        html = r.text

        # pblancId=(PBLN_*)...>[제목]</a> 패턴
        row_pattern = re.compile(r'pblancId=(PBLN_\d+)[^>]*>\s*([^<]{5,120}?)\s*</a>')
        matches = row_pattern.findall(html)

        # 방법2: BeautifulSoup 보조 (신청기간, 기관명)
        rows = soup.select("table tbody tr")

        for idx_m, (pblancId, title) in enumerate(matches):
            title = title.strip()
            if not title:
                continue

            detail_url = f"{BIZ_BASE}/sii/siia/selectSIIA200Detail.do?pblancId={pblancId}"

            # 해당 tr에서 날짜, 기관명 추출
            deadline_str, deadline_date = "상시", "9999-12-31"
            org = "중소벤처기업부"

            if idx_m < len(rows):
                row_text = rows[idx_m].get_text(" ", strip=True)
                # 신청기간: YYYY-MM-DD ~ YYYY-MM-DD
                period_m = re.search(r"(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})", row_text)
                if period_m:
                    deadline_str, deadline_date = parse_deadline(period_m.group(2))

                # 기관명 (소관부처 or 사업수행기관)
                cells = rows[idx_m].find_all("td")
                # 보통 4~5번째 셀이 기관명
                for cell in cells[3:]:
                    t = cell.get_text(strip=True)
                    if t and len(t) >= 3 and not re.match(r"^\d", t):
                        org = t
                        break

            items.append({
                "id": make_id("biz", title),
                "title": title,
                "org": org,
                "category": infer_category(title),
                "amount": infer_amount(title),
                "deadline": deadline_str,
                "deadlineDate": deadline_date,
                "description": f"bizinfo.go.kr 공고입니다. 자세한 내용은 공식 사이트에서 확인하세요.",
                "url": detail_url,
            })

        time.sleep(1)

    print(f"      -> {len(items)}건 수집")
    return items


# ─────────────────────────────────────────────
# 중복 제거 & 정렬
# ─────────────────────────────────────────────

def deduplicate(items: list) -> list:
    seen = set()
    result = []
    for item in items:
        key = re.sub(r"\s+", "", item["title"])[:30]
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def sort_items(items: list) -> list:
    def key(item):
        d = item.get("deadlineDate", "9999-12-31")
        if d < TODAY:
            return "z_" + d      # 마감된 건 맨 뒤
        if d == "9999-12-31":
            return "y_상시"      # 상시는 마감 임박 다음
        return d                 # 마감 임박순
    return sorted(items, key=key)


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────

def main():
    print()
    print("=" * 55)
    print(f"  공고 크롤링 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    all_items: list = []
    all_items += fetch_mss(pages=2)
    all_items += fetch_kstartup(pages=3)
    all_items += fetch_bizinfo(pages=3)

    all_items = deduplicate(all_items)
    all_items = sort_items(all_items)

    print()
    print(f"  최종: {len(all_items)}건 (중복 제거 후)")
    print("  소스: mss.go.kr / k-startup.go.kr / bizinfo.go.kr")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now().__format__("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M KST"),
        "count": len(all_items),
        "sources": ["mss.go.kr", "k-startup.go.kr", "bizinfo.go.kr"],
        "items": all_items,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"  저장 완료: {OUTPUT_PATH}")
    print("=" * 55)


if __name__ == "__main__":
    main()
