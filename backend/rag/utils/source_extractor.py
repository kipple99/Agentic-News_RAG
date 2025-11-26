"""
소스 추출 유틸리티
검색 결과에서 출처 정보를 추출합니다.
"""

from typing import List, Dict, Any, Optional


class Source:
    """출처 정보를 담는 클래스"""
    
    def __init__(
        self,
        title: str,
        url: str = "",
        source_type: str = "unknown",
        snippet: str = "",
        date: str = "",
        score: float = 0.0
    ):
        self.title = title
        self.url = url
        self.source_type = source_type  # "internal_db", "naver", "web"
        self.snippet = snippet
        self.date = date
        self.score = score
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "title": self.title,
            "url": self.url,
            "source_type": self.source_type,
            "snippet": self.snippet,
            "date": self.date,
            "score": self.score
        }
    
    def __repr__(self):
        return f"Source(title='{self.title[:50]}...', url='{self.url[:50]}...', type='{self.source_type}')"


def extract_sources_from_state(state: Dict[str, Any], max_sources: int = 10) -> List[Source]:
    """
    AgentState에서 사용된 소스 추출
    
    Args:
        state: AgentState 딕셔너리
        max_sources: 최대 소스 개수
    
    Returns:
        Source 객체 리스트
    """
    sources = []
    
    # 1. ES 결과에서 소스 추출
    es_results = state.get("es_results", {})
    queries_results = es_results.get("queries", {})
    
    for query, result in queries_results.items():
        hits = result.get("hits", {}).get("hits", [])
        for hit in hits[:3]:  # 쿼리당 상위 3개
            source_dict = hit.get("_source", {})
            title = source_dict.get("title", source_dict.get("source", "제목 없음"))
            url = source_dict.get("url", "")
            text = source_dict.get("text", source_dict.get("content", ""))
            date = source_dict.get("date", "")
            score = hit.get("_score", 0.0)
            
            sources.append(Source(
                title=title,
                url=url,
                source_type="internal_db",
                snippet=text[:200] if text else "",
                date=date,
                score=score
            ))
    
    # 2. Naver 결과에서 소스 추출
    naver_results = state.get("naver_results", [])
    for result in naver_results[:max_sources]:
        title = getattr(result, "title", "제목 없음")
        link = getattr(result, "link", "")
        snippet = getattr(result, "snippet", "")
        
        sources.append(Source(
            title=title,
            url=link,
            source_type="naver",
            snippet=snippet,
            date="",
            score=1.0  # 웹 검색 결과는 기본 점수 1.0
        ))
    
    # 3. web_results에서 소스 추출 (DuckDuckGo 등)
    web_results = state.get("web_results", {})
    for query, result_text in web_results.items():
        if result_text and result_text != "웹 검색 실패":
            # 텍스트에서 제목과 링크 추출 시도
            lines = result_text.split("\n")
            title = lines[0] if lines else query
            url = ""
            for line in lines:
                if "http" in line or "www" in line:
                    url = line.strip()
                    break
            
            sources.append(Source(
                title=title[:100],
                url=url,
                source_type="web",
                snippet=result_text[:200],
                date="",
                score=0.9
            ))
    
    # 중복 제거 (URL 기준)
    seen_urls = set()
    unique_sources = []
    for source in sources:
        if source.url and source.url in seen_urls:
            continue
        if source.url:
            seen_urls.add(source.url)
        unique_sources.append(source)
    
    # 점수 기준 정렬 (높은 순)
    unique_sources.sort(key=lambda x: x.score, reverse=True)
    
    return unique_sources[:max_sources]


def format_sources_for_answer(sources: List[Source]) -> str:
    """
    소스 리스트를 답변에 포함할 형식으로 포맷팅
    
    Args:
        sources: Source 객체 리스트
    
    Returns:
        포맷팅된 문자열
    """
    if not sources:
        return ""
    
    formatted = "\n\n---\n**참고 자료:**\n"
    
    for i, source in enumerate(sources, 1):
        if source.url:
            formatted += f"{i}. [{source.title}]({source.url})\n"
        else:
            formatted += f"{i}. {source.title}\n"
        
        if source.snippet:
            formatted += f"   요약: {source.snippet[:100]}...\n"
    
    return formatted


def format_sources_for_context(sources: List[Source]) -> str:
    """
    소스 리스트를 컨텍스트에 포함할 형식으로 포맷팅
    
    Args:
        sources: Source 객체 리스트
    
    Returns:
        포맷팅된 문자열
    """
    if not sources:
        return ""
    
    formatted = "\n=== 출처 정보 ===\n"
    
    for i, source in enumerate(sources, 1):
        formatted += f"\n[{i}] {source.title}\n"
        if source.url:
            formatted += f"   링크: {source.url}\n"
        if source.date:
            formatted += f"   날짜: {source.date}\n"
        if source.snippet:
            formatted += f"   요약: {source.snippet[:150]}...\n"
        formatted += f"   출처: {source.source_type}\n"
    
    return formatted


