"""
공고 데이터 크롤러
- 소스: bizinfo.go.kr (RSS), k-startup.go.kr (웹 스크래핑)
- 출력: data/announcements.json
- 실행: GitHub Actions (매주 월요일 23:00 KST)
"""

import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "announcements.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ─────────────────────────────────────────────
# 공통 유틸
# ─────────────────────────────────────────────

def safe_get(url, timeout=15, **kwargs):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, **kwargs)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"  [오류] GET {url} → {e}")
        return None


def infer_category(title, desc=""):
    text = title + " " + desc
    cats = []
    if any(k in text for k in ["예비창업", "예비 창업", "창업 준비"]):
        cats.append("예비창업")
    if any(k in text for k in ["초기창업", "초기 창업", "창업 3년", "창업3년", "창업 후"]):
        cats.append("초기창업")
    if any(k in text for k in ["재도전", "재창업", "실패"]):
        cats.append("재도전")
    if any(k in text for k in ["청년", "만 39세", "만39세", "20대", "30대"]):
        cats.append("청년")
    if any(k in text for k in ["기술창업", "딥테크", "R&D", "기술개발"]):
        cats.append("기술창업")
    return cats if cats else ["창업"]


def infer_amount(desc):
    patterns = [
        r"최대\s*([\d,]+)\s*억원",
        r"최대\s*([\d,]+)\s*만원",
        r"([\d,]+)\s*억원\s*이내",
        r"([\d,]+)\s*만원\s*이내",
        r"1인당\s*([\d,]+)\s*만원",
    ]
    for p in patterns:
        m = re.search(p, desc)
        if m:
            num = m.group(1)
            unit = "억원" if "억원" in p else "만원"
            return f"최대 {num}{unit}"
    return "공고 확인"


def infer_deadline(desc, pub_date=None):
    """마감일 추출 — 텍스트 우선, 없으면 pubDate+30일"""
    patterns = [
        r"(\d{4})[.\-년]\s*(\d{1,2})[.\-월]\s*(\d{1,2})\s*일?\s*(까지|마감|접수마감|모집마감)",
        r"모집기간[^\d]*(\d{4})[.\-년]\s*(\d{1,2})[.\-월]\s*(\d{1,2})",
        r"접수기간[^\d]*(\d{4})[.\-년]\s*(\d{1,2})[.\-월]\s*(\d{1,2})",
        r"(\d{4})\s*[.\-]\s*(\d{1,2})\s*[.\-]\s*(\d{1,2})\s*\(?(월|화|수|목|금|토|일)?\)?",
    ]
    for p in patterns:
        m = re.search(p, desc)
        if m:
            try:
                y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                dt = datetime(y, mo, d)
                return dt.strftime("%Y.%m.%d"), dt.strftime("%Y-%m-%d")
            except Exception:
                continue

    if pub_date:
        try:
            base = dateparser.parse(pub_date, ignoretz=True)
            deadline = base + timedelta(days=30)
            return deadline.strftime("%Y.%m.%d"), deadline.strftime("%Y-%m-%d")
        except Exception:
            pass

    return "상시", "9999-12-31"


def is_startup_related(title, desc=""):
    keywords = ["창업", "스타트업", "벤처", "소상공인", "사업화", "아이디어", "기술창업",
                 "청년", "예비창업", "초기창업", "재도전", "사업계획", "지원사업"]
    text = title + " " + desc
    return any(k in text for k in keywords)


# ─────────────────────────────────────────────
# 소스 1: bizinfo.go.kr RSS
# ─────────────────────────────────────────────

BIZINFO_FEEDS = [
    # 창업 관련 카테고리
    ("https://www.bizinfo.go.kr/uss/rss/bizSupportInfo.do?feedsId=PMAS0040", "창업지원"),
    ("https://www.bizinfo.go.kr/uss/rss/bizSupportInfo.do?feedsId=PMAS0010", "소상공인"),
]


def fetch_bizinfo():
    items = []
    for url, label in BIZINFO_FEEDS:
        print(f"  bizinfo.go.kr 페치 중: {label}")
        r = safe_get(url)
        if not r:
            continue
        try:
            root = ET.fromstring(r.content)
            ns = ""
            channel = root.find("channel")
            if channel is None:
                continue
            for item in channel.findall("item"):
                def t(tag):
                    el = item.find(tag)
                    return el.text.strip() if el is not None and el.text else ""

                title = t("title")
                link = t("link")
                desc = t("description")
                pub_date = t("pubDate")

                if not title:
                    continue
                if not is_startup_related(title, desc):
                    continue

                deadline_str, deadline_date = infer_deadline(desc, pub_date)
                items.append({
                    "id": f"biz_{hash(title) % 999999:06d}",
                    "title": title,
                    "org": "bizinfo.go.kr",
                    "category": infer_category(title, desc),
                    "amount": infer_amount(desc),
                    "deadline": deadline_str,
                    "deadlineDate": deadline_date,
                    "description": desc[:400] if desc else title,
                    "url": link or "https://www.bizinfo.go.kr",
                })
        except ET.ParseError as e:
            print(f"    XML 파싱 오류: {e}")

    print(f"  bizinfo: {len(items)}건 수집")
    return items


# ─────────────────────────────────────────────
# 소스 2: K-Startup (k-startup.go.kr)
# ─────────────────────────────────────────────

KSTARTUP_LIST = "https://www.k-startup.go.kr/web/contents/bizpbanc-ongoing.do?schM=list&page=1&schStr=&pbancSn="


def fetch_kstartup():
    print("  k-startup.go.kr 페치 중...")
    items = []
    r = safe_get(KSTARTUP_LIST, timeout=20)
    if not r:
        return items

    try:
        soup = BeautifulSoup(r.text, "lxml")
        rows = soup.select("ul.list-type1 li") or soup.select(".board-list li") or soup.select("table tbody tr")

        for row in rows[:30]:
            title_el = row.select_one("a, .tit, .title, td:nth-child(2)")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title or not is_startup_related(title):
                continue

            link_el = row.select_one("a[href]")
            link = ""
            if link_el:
                href = link_el.get("href", "")
                link = href if href.startswith("http") else f"https://www.k-startup.go.kr{href}"

            # 마감일 파싱
            date_el = row.select_one(".date, .period, td:last-child, .dday")
            raw_date = date_el.get_text(strip=True) if date_el else ""
            deadline_str, deadline_date = infer_deadline(raw_date or title)

            # 기관명
            org_el = row.select_one(".org, .institution, td:nth-child(3)")
            org = org_el.get_text(strip=True) if org_el else "창업진흥원"

            items.append({
                "id": f"kst_{hash(title) % 999999:06d}",
                "title": title,
                "org": org,
                "category": infer_category(title),
                "amount": infer_amount(title),
                "deadline": deadline_str,
                "deadlineDate": deadline_date,
                "description": f"K-Startup 공고입니다. 자세한 내용은 공식 사이트를 확인하세요.",
                "url": link or "https://www.k-startup.go.kr",
            })
    except Exception as e:
        print(f"    K-Startup 파싱 오류: {e}")

    print(f"  k-startup: {len(items)}건 수집")
    return items


# ─────────────────────────────────────────────
# 소스 3: 중소기업진흥공단 (sbc.or.kr)
# ─────────────────────────────────────────────

SBC_LIST = "https://www.sbc.or.kr/web/kor/business_support/index.do"


def fetch_sbc():
    print("  sbc.or.kr 페치 중...")
    items = []
    r = safe_get(SBC_LIST, timeout=20)
    if not r:
        return items

    try:
        soup = BeautifulSoup(r.text, "lxml")
        rows = soup.select(".board-list tr, .list-type tr, .biz-list li")

        for row in rows[:20]:
            title_el = row.select_one("a, .subject, .tit")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title or not is_startup_related(title):
                continue

            link_el = row.select_one("a[href]")
            link = ""
            if link_el:
                href = link_el.get("href", "")
                link = href if href.startswith("http") else f"https://www.sbc.or.kr{href}"

            date_el = row.select_one(".date, td:last-child")
            raw_date = date_el.get_text(strip=True) if date_el else ""
            deadline_str, deadline_date = infer_deadline(raw_date)

            items.append({
                "id": f"sbc_{hash(title) % 999999:06d}",
                "title": title,
                "org": "중소기업진흥공단",
                "category": infer_category(title),
                "amount": infer_amount(title),
                "deadline": deadline_str,
                "deadlineDate": deadline_date,
                "description": "중소기업진흥공단 지원사업입니다. 자세한 내용은 공식 사이트를 확인하세요.",
                "url": link or "https://www.sbc.or.kr",
            })
    except Exception as e:
        print(f"    SBC 파싱 오류: {e}")

    print(f"  sbc: {len(items)}건 수집")
    return items


# ─────────────────────────────────────────────
# 중복 제거 & 정렬
# ─────────────────────────────────────────────

def deduplicate(items):
    seen = set()
    result = []
    for item in items:
        key = item["title"].strip()[:40]
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def sort_items(items):
    """마감 임박 순 정렬 (상시/예정은 뒤로)"""
    today = datetime.now().strftime("%Y-%m-%d")

    def sort_key(item):
        d = item.get("deadlineDate", "9999-12-31")
        if d == "9999-12-31":
            return "9998-12-31"  # 상시는 뒤에서 두 번째
        if d < today:
            return "9999-12-31"  # 마감된 건 맨 뒤
        return d

    return sorted(items, key=sort_key)


# ─────────────────────────────────────────────
# 메인 실행
# ─────────────────────────────────────────────

def main():
    print("\n공고 크롤링 시작...")
    print("=" * 50)

    all_items = []

    # 각 소스 수집
    all_items += fetch_bizinfo()
    time.sleep(1)
    all_items += fetch_kstartup()
    time.sleep(1)
    all_items += fetch_sbc()

    # 중복 제거 & 정렬
    all_items = deduplicate(all_items)
    all_items = sort_items(all_items)

    print(f"\n최종 수집: {len(all_items)}건")

    # JSON 저장
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at_kst": datetime.now().strftime("%Y-%m-%d %H:%M KST"),
        "count": len(all_items),
        "items": all_items,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"저장 완료: {OUTPUT_PATH}")
    print("=" * 50)


if __name__ == "__main__":
    main()
