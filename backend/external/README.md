# 외부 검색 API 클라이언트

Google, DuckDuckGo, Naver Search API를 지원하는 통합 검색 클라이언트입니다.

## 기능

- **Naver Search API**: 한국 뉴스 검색에 최적화
- **Google Custom Search API**: 전 세계 뉴스 검색
- **DuckDuckGo**: API 키 없이 사용 가능한 무료 검색
- **자동 Fallback**: 한 검색 엔진 실패 시 자동으로 다른 엔진 시도
- **통합 인터페이스**: 모든 검색 엔진을 동일한 방식으로 사용

## 설치

```bash
pip install requests duckduckgo-search
```

## 환경 변수 설정

`.env` 파일에 다음 환경 변수를 설정하세요:

```env
# Naver Search API
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# Google Custom Search API
GOOGLE_API_KEY=your_google_api_key
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id
```

### API 키 발급 방법

#### Naver Search API
1. [Naver Developers](https://developers.naver.com/) 접속
2. 애플리케이션 등록
3. Client ID와 Client Secret 발급

#### Google Custom Search API
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. Custom Search API 활성화
3. API 키 생성
4. [Custom Search Engine](https://programmablesearchengine.google.com/)에서 검색 엔진 생성
5. 검색 엔진 ID 확인

#### DuckDuckGo
- API 키 불필요 (무료 사용 가능)

## 사용법

### 1. 특정 검색 제공자 사용

```python
from naver_client import SearchClientFactory, SearchProvider

# Naver 검색
client = SearchClientFactory.get_client(SearchProvider.NAVER)
results = client.search("경제 뉴스", num_results=10)

for result in results:
    print(result.title)
    print(result.link)
    print(result.snippet)
```

### 2. 통합 클라이언트 사용 (자동 Fallback)

```python
from naver_client import UnifiedSearchClient

# 사용 가능한 모든 검색 엔진을 자동으로 시도
client = UnifiedSearchClient()
results = client.search("주식 시장", num_results=10)

for result in results:
    print(f"[{result.source}] {result.title}")
```

### 3. 우선순위 지정

```python
from naver_client import UnifiedSearchClient, SearchProvider

# DuckDuckGo를 우선 사용, 실패 시 Google 시도
client = UnifiedSearchClient(
    preferred_providers=[SearchProvider.DUCKDUCKGO, SearchProvider.GOOGLE]
)
results = client.search("부동산 뉴스", num_results=5)
```

### 4. 편의 함수 사용

```python
from naver_client import search_news

# 가장 간단한 사용법
results = search_news("금리 인상", provider="naver", num_results=5)

for result in results:
    print(result.title)
```

### 5. 사용 가능한 제공자 확인

```python
from naver_client import SearchClientFactory

available = SearchClientFactory.get_available_providers()
print(f"사용 가능한 제공자: {[p.value for p in available]}")
```

## SearchResult 객체

검색 결과는 `SearchResult` 객체로 반환됩니다:

```python
@dataclass
class SearchResult:
    title: str              # 제목
    link: str               # 링크
    snippet: str            # 요약/설명
    source: str             # 검색 엔진 이름 ("Naver", "Google", "DuckDuckGo")
    published_date: Optional[str]  # 발행일 (있는 경우)
```

## 고급 사용법

### 특정 제공자만 사용 (Fallback 비활성화)

```python
client = UnifiedSearchClient()
results = client.search(
    "검색어",
    provider=SearchProvider.NAVER,
    fallback=False  # 실패 시 다른 엔진으로 전환하지 않음
)
```

### Naver 검색 정렬 옵션

```python
client = SearchClientFactory.get_client(SearchProvider.NAVER)
# sort: "date" (날짜순) 또는 "sim" (관련도순)
results = client.search("경제 뉴스", num_results=10, sort="date")
```

### Google 뉴스 전용 검색

```python
client = SearchClientFactory.get_client(SearchProvider.GOOGLE)
results = client.search("경제 뉴스", num_results=10, news_only=True)
```

## 오류 처리

```python
from naver_client import SearchClientFactory, SearchProvider

try:
    client = SearchClientFactory.get_client(SearchProvider.NAVER)
    if client.is_available():
        results = client.search("검색어")
    else:
        print("Naver API 키가 설정되지 않았습니다.")
except Exception as e:
    print(f"검색 실패: {e}")
```

## 예제

자세한 사용 예제는 `example_usage.py` 파일을 참고하세요:

```bash
python backend/external/example_usage.py
```

## 주의사항

1. **API 제한**: 각 검색 엔진마다 요청 제한이 있습니다.
   - Naver: 초당 10회
   - Google: 일일 100회 (무료 플랜)
   - DuckDuckGo: 과도한 요청 시 일시 차단 가능

2. **DuckDuckGo**: 공식 API가 없어 라이브러리를 사용하며, 안정성이 상대적으로 낮을 수 있습니다.

3. **환경 변수**: 프로덕션 환경에서는 `.env` 파일을 사용하고, Git에 커밋하지 마세요.

## 라이선스

이 프로젝트의 라이선스를 따릅니다.

