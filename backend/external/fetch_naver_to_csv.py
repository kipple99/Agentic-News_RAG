import os
import csv
import time
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
RAW_CSV = DATA_DIR / "raw" / "news_scrap.csv"

load_dotenv(BASE_DIR / ".env")

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

API_URL = "https://openapi.naver.com/v1/search/news.json"


def fetch_news_from_naver(query: str, display: int = 50, start: int = 1):
    # 네이버 뉴스 api로 데이터 가져오기
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {
        "query": query,
        "display": display,  # 한 번에 최대 100
        "start": start,      # 페이지 시작 번호 (1, 51, 101 ...)
        "sort": "date",      # 최신순
    }

    resp = requests.get(API_URL, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("items", [])


def normalize_item(item, category: str):
    title = item.get("title", "").replace("<b>", "").replace("</b>", "")
    desc = item.get("description", "").replace("<b>", "").replace("</b>", "")
    link = item.get("link", "")
    pubdate = item.get("pubDate", "")

    
    try:
        dt = datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S %z")
        date_str = dt.strftime("%Y-%m-%d")
    except Exception:
        date_str = ""

    content = desc

    return {
        "title": title,
        "content": content,
        "date": date_str,
        "source": "Naver",
        "url": link,
        "category": category,
    }


def load_existing_rows():
    if not RAW_CSV.exists():
        return [], set()

    with RAW_CSV.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    existing_urls = {row["url"] for row in rows}
    return rows, existing_urls


def save_rows_to_csv(all_rows):
    os.makedirs(RAW_CSV.parent, exist_ok=True)

    with RAW_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["id", "title", "content", "date", "source", "url", "category"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for idx, row in enumerate(all_rows, start=1):
            writer.writerow(
                {
                    "id": idx,
                    "title": row["title"],
                    "content": row["content"],
                    "date": row["date"],
                    "source": row["source"],
                    "url": row["url"],
                    "category": row["category"],
                }
            )


def main():
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        raise RuntimeError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 이 설정되지 않았습니다.")

    # 1) 기존 데이터
    base_rows, existing_urls = load_existing_rows()
    print(f"[INFO] 기존 기사 수: {len(base_rows)}")

    # 2) 수집할 키워드 정의
    queries = [
        ("전기차", "전기차"),
        ("전기차 배터리", "배터리"),
        ("2차전지", "2차전지"),
        ("전기차 충전", "전기차"),
        ("LG에너지솔루션", "배터리"),
        ("삼성SDI", "배터리"),
        ("테슬라 전기차", "전기차"),
    ]

    new_rows = []

    for query, category in queries:
        print(f"\n[INFO] 네이버 뉴스 수집: '{query}'")
        items = fetch_news_from_naver(query, display=50, start=1)
        print(f"  - {len(items)}개 수신")

        for item in items:
            norm = normalize_item(item, category)
            if not norm["url"] or norm["url"] in existing_urls:
                continue
            new_rows.append(norm)
            existing_urls.add(norm["url"])

        time.sleep(0.2) 

    print(f"\n[INFO] 새로 수집된 기사 수: {len(new_rows)}")

    # 3) 기존 + 신규 합쳐서 저장
    all_rows = base_rows + new_rows
    save_rows_to_csv(all_rows)
    print(f"[OK] 총 {len(all_rows)}개 기사를 CSV에 저장 완료: {RAW_CSV}")


if __name__ == "__main__":
    main()
