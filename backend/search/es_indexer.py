import csv
from pathlib import Path

from elasticsearch import Elasticsearch, helpers
from sentence_transformers import SentenceTransformer

# ==== 경로 / 설정 ====
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
CSV_PATH = DATA_DIR / "raw" / "news_scrap.csv"

ES_HOST = "http://127.0.0.1:9200"
ES_INDEX = "rag_news_db"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384  # all-MiniLM-L6-v2 기준

# ==== ES 클라이언트 (8.x 완전 호환 설정) ====
es = Elasticsearch(
    ES_HOST,
    verify_certs=False,
    ssl_show_warn=False,
    request_timeout=60
)

embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def create_index():
    """
    rag_news_db 인덱스를 새로 생성한다.
    기존에 있으면 삭제 후 재생성.
    """
    print("[INFO] 인덱스 존재 여부 확인 중...")

    try:
        exists = es.indices.exists(index=ES_INDEX)
    except Exception as e:
        print(f"[WARN] indices.exists() 오류: {e}")
        exists = False

    if exists:
        es.indices.delete(index=ES_INDEX, ignore=[400, 404])
        print(f"[INFO] 기존 인덱스 '{ES_INDEX}' 삭제 완료.")

    mapping = {
        "properties": {
            "title": {"type": "text"},
            "content": {"type": "text"},
            "text": {"type": "text"},
            "date": {"type": "keyword"},
            "source": {"type": "keyword"},
            "url": {"type": "keyword"},
            "category": {"type": "keyword"},
            "vector": {
                "type": "dense_vector",
                "dims": EMBEDDING_DIMENSION,
                "index": True,
                "similarity": "cosine",
            },
        }
    }

    es.indices.create(index=ES_INDEX, mappings=mapping)
    print(f"[OK] 새 인덱스 '{ES_INDEX}' 생성 완료.")


def load_csv_rows():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {CSV_PATH}")

    rows = []
    with CSV_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"[INFO] CSV에서 {len(rows)}개 기사 로드.")
    return rows


def bulk_index(rows, batch_size: int = 256):
    total = len(rows)
    actions = []
    count = 0

    for i, row in enumerate(rows, start=1):
        title = row.get("title", "") or ""
        content = row.get("content", "") or ""
        date = row.get("date", "") or ""
        source = row.get("source", "") or ""
        url = row.get("url", "") or ""
        category = row.get("category", "") or ""

        text = f"{title}\n\n{content}"
        vec = embedding_model.encode(text, normalize_embeddings=True).tolist()

        doc = {
            "title": title,
            "content": content,
            "text": text,
            "date": date,
            "source": source,
            "url": url,
            "category": category,
            "vector": vec,
        }

        actions.append({"_index": ES_INDEX, "_source": doc})

        if len(actions) >= batch_size:
            helpers.bulk(es, actions, ignore_status=[400, 404])
            count += len(actions)
            print(f"[INFO] {count}/{total}개 인덱싱 완료...")
            actions = []

    if actions:
        helpers.bulk(es, actions, ignore_status=[400, 404])
        count += len(actions)
        print(f"[INFO] {count}/{total}개 인덱싱 완료.")

    print(f"[OK] 최종 {count}개 문서 인덱싱 완료.")


def main():
    print(f"[INFO] Elasticsearch 연결 테스트: {ES_HOST}")

    try:
        alive = es.ping()
        print(f"[INFO] es.ping() 결과: {alive}")
    except Exception as e:
        print(f"[WARN] ping 오류: {e}")
        alive = False

    if not alive:
        print("[WARN] ping 실패 → 하지만 curl로 응답되므로 인덱싱 강행.")

    print(f"[INFO] CSV 경로: {CSV_PATH}")

    create_index()
    rows = load_csv_rows()
    bulk_index(rows)

    try:
        count = es.count(index=ES_INDEX)["count"]
        print(f"[OK] 인덱스 '{ES_INDEX}' 문서 수: {count}")
    except Exception as e:
        print(f"[WARN] 문서 수 조회 오류: {e}")


if __name__ == "__main__":
    main()
