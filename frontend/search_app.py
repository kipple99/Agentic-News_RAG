"""
Agentic News RAG - Frontend
에이전트가 자동으로 뉴스 검색 vs LLM 생성 판단
기존 UI 스타일과 기능 활용
"""

import streamlit as st
import requests
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

# Backend API URL
API_URL = "http://localhost:8000"

@dataclass
class SearchResult:
    """검색 결과 데이터 클래스 (기존 구조 활용)"""
    title: str
    link: str
    snippet: str
    source: str
    published_date: Optional[str] = None

@dataclass
class InternalDBResult:
    """내부 DB 검색 결과 데이터 클래스"""
    title: str
    text: str
    url: str
    date: str
    score: float
    es_score: float
    source_type: str = "internal_db"

st.set_page_config(
    page_title="Agentic News RAG - News Search",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 기존 UI 스타일 활용
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .result-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .method-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .api-search {
        background-color: #4CAF50;
        color: white;
    }
    .llm-generate {
        background-color: #2196F3;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_url" not in st.session_state:
    st.session_state.api_url = API_URL

# 기존 함수들 활용
def format_date(date_str):
    """날짜 포맷팅 (기존 함수 활용)"""
    if not date_str:
        return "No date"
    try:
        dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return date_str

def display_result(result: SearchResult, index: int):
    """검색 결과 카드 표시"""
    # 제목 표시
    st.markdown(f"### {index}. {result.title}")
    
    # 링크 표시 (항상 클릭 가능한 링크로)
    if result.link:
        # URL이 올바른 형식인지 확인
        link_url = result.link
        if not link_url.startswith('http'):
            # 마크다운 링크 형식에서 URL 추출
            import re
            url_match = re.search(r'https?://[^\s\)]+', link_url)
            if url_match:
                link_url = url_match.group(0)
        
        if link_url.startswith('http'):
            st.markdown(f"🔗 [기사 링크]({link_url})")
        else:
            st.markdown(f"🔗 링크: {result.link}")
    else:
        st.markdown("🔗 링크 없음")
    
    # 요약 표시
    if result.snippet:
        st.markdown(f"**요약:** {result.snippet}")
    
    # 날짜와 출처 표시
    date_str = format_date(result.published_date)
    st.caption(f"📅 {date_str} | 출처: {result.source}")
    
    st.markdown("---")

def check_backend_health():
    """Backend 서버 상태 확인"""
    try:
        response = requests.get(f"{st.session_state.api_url}/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def send_query(query: str) -> Dict:
    """Backend API에 쿼리 전송"""
    try:
        response = requests.post(
            f"{st.session_state.api_url}/query",
            json={
                "query": query,
                "chat_history": st.session_state.chat_history
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def clear_history():
    """대화 기록 초기화"""
    try:
        requests.post(f"{st.session_state.api_url}/clear-history", timeout=2)
    except:
        pass
    st.session_state.chat_history = []

def parse_internal_db_results(internal_db_results: Optional[List[Dict]]) -> List[InternalDBResult]:
    """백엔드에서 받은 내부 DB 결과 파싱"""
    if not internal_db_results:
        return []
    
    results = []
    for item in internal_db_results:
        results.append(InternalDBResult(
            title=item.get("title", "제목 없음"),
            text=item.get("text", ""),
            url=item.get("url", ""),
            date=item.get("date", ""),
            score=item.get("score", 0.0),
            es_score=item.get("es_score", 0.0),
            source_type=item.get("source_type", "internal_db")
        ))
    
    return results

def display_internal_db_result(result: InternalDBResult, index: int):
    """내부 DB 결과 카드 표시 (클릭 시 expander로 상세 정보 표시)"""
    # 카드 형태로 제목과 요약 표시
    st.markdown(f"### {index}. {result.title}")
    
    # 요약 (텍스트의 처음 200자)
    snippet = result.text[:200] + "..." if len(result.text) > 200 else result.text
    if snippet:
        st.markdown(f"**요약:** {snippet}")
    
    # 메타데이터 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        if result.date:
            st.caption(f"📅 {result.date}")
        else:
            st.caption("📅 날짜 없음")
    with col2:
        st.caption(f"📊 관련성 점수: {result.score:.4f}")
    with col3:
        st.caption("📚 출처: 내부DB정보")
    
    # 클릭 시 상세 정보를 보여주는 expander
    with st.expander("📖 전체 내용 및 상세 정보 보기", expanded=False):
        st.markdown("#### 📋 메타데이터")
        metadata_col1, metadata_col2 = st.columns(2)
        with metadata_col1:
            st.write(f"**제목:** {result.title}")
            st.write(f"**날짜:** {result.date if result.date else '날짜 없음'}")
            if result.url:
                st.write(f"**원본 URL:** {result.url}")
        with metadata_col2:
            st.write(f"**관련성 점수 (RRF):** {result.score:.4f}")
            st.write(f"**Elasticsearch 점수:** {result.es_score:.4f}")
            st.write(f"**출처 타입:** {result.source_type}")
        
        st.markdown("---")
        st.markdown("#### 📄 전체 내용")
        st.text_area("", value=result.text, height=300, disabled=True, key=f"internal_db_text_{index}")
    
    st.markdown("---")

def parse_search_results(answer: str) -> List[SearchResult]:
    """에이전트 응답에서 검색 결과 파싱"""
    results = []
    lines = answer.split('\n')
    current_result = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 번호로 시작하는 줄 찾기 (1., 2., 3. 등)
        if line and line[0].isdigit() and '.' in line[:3]:
            if current_result:
                results.append(current_result)
            # 제목 추출
            if '제목:' in line:
                title = line.split('제목:', 1)[-1].strip()
            else:
                # 번호 제거 (예: "1. 제목" -> "제목")
                parts = line.split('.', 1)
                if len(parts) > 1:
                    title = parts[1].strip()
                else:
                    title = line
            # 제목에서 불필요한 부분 제거
            title = title.replace('제목:', '').strip()
            # 출처를 동적으로 판단 (기본값은 Naver)
            source = "Naver"
            current_result = SearchResult(
                title=title,
                link="",
                snippet="",
                source=source,
                published_date=None
            )
        elif current_result:
            if '링크:' in line:
                link = line.split('링크:', 1)[-1].strip()
                # 링크 정리 (공백 제거, URL만 추출)
                import re
                # 마크다운 링크 형식 [텍스트](URL)에서 URL 추출
                markdown_link_match = re.search(r'\[.*?\]\((https?://[^\)]+)\)', link)
                if markdown_link_match:
                    current_result.link = markdown_link_match.group(1)
                elif link.startswith('http'):
                    current_result.link = link
                else:
                    # 일반 텍스트에서 URL 추출
                    url_match = re.search(r'https?://[^\s\)]+', link)
                    if url_match:
                        current_result.link = url_match.group(0)
                    else:
                        current_result.link = link
            elif '요약:' in line:
                snippet = line.split('요약:', 1)[-1].strip()
                # "..." 제거 및 정리
                snippet = snippet.replace('...', '').strip()
                if snippet:
                    current_result.snippet = snippet
            elif '출처:' in line:
                source = line.split('출처:', 1)[-1].strip()
                # 괄호 제거
                source = source.replace(')', '').replace('(', '').strip()
                if source:
                    current_result.source = source
            elif line and not any(keyword in line for keyword in ['검색어:', '검색 결과:', '사용자에게', '다음 뉴스']):
                # 제목이나 링크가 없는 경우, 줄이 내용이면 스니펫으로 추가
                if not current_result.snippet and len(line) > 10:
                    current_result.snippet = line
    
    if current_result:
        results.append(current_result)
    
    return results

def main():
    st.markdown('<div class="main-header">🔍 Agentic News RAG - News Search</div>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # API URL 설정
        api_url = st.text_input("Backend API URL", value=st.session_state.api_url, key="api_url_input")
        if api_url != st.session_state.api_url:
            st.session_state.api_url = api_url
        
        # Backend 상태 확인
        if check_backend_health():
            st.success("✅ Backend Connected")
        else:
            st.error("❌ Backend Not Connected")
            st.info("Backend 서버를 먼저 실행해주세요:\n```bash\ncd backend\npython app.py\n```")
        
        st.markdown("---")
        st.header("ℹ️ Info")
        st.info("에이전트가 자동으로 뉴스 검색 또는 LLM 생성 선택")
        
        # 대화 기록 초기화
        if st.button("🗑️ Clear History", use_container_width=True):
            clear_history()
            st.rerun()
    
    # 검색창 (기존 스타일 유지)
    search_query = st.text_input(
        "🔍 Enter search query",
        placeholder="e.g., 오늘 경제 뉴스, 뉴스란 무엇인가요?",
        key="search_input"
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_button = st.button("Search", type="primary", use_container_width=True)
    
    if search_button and search_query:
        with st.spinner("🤔 에이전트가 판단 중..."):
            result = send_query(search_query)
        
        if "error" in result:
            st.error(f"❌ Error occurred: {result['error']}")
        else:
            answer = result.get("answer", "")
            method = result.get("method", "unknown")
            
            # 방법 배지 표시
            if method == "integrated_rag":
                method_class = "api-search"
                method_text = "🤖 통합 RAG 시스템 사용"
            elif method == "api_search":
                method_class = "api-search"
                method_text = "🔍 API 검색 사용"
            else:
                method_class = "llm-generate"
                method_text = "💡 LLM 생성 사용"
            
            st.markdown(f'<span class="method-badge {method_class}">{method_text}</span>', unsafe_allow_html=True)
            
            # 통합 RAG 시스템 추가 정보 표시
            if method == "integrated_rag":
                with st.expander("🔍 검색 상세 정보", expanded=False):
                    sub_queries = result.get("sub_queries", [])
                    if sub_queries:
                        st.write("**생성된 서브쿼리:**")
                        for i, sq in enumerate(sub_queries, 1):
                            st.write(f"{i}. {sq}")
                    
                    is_relevant = result.get("is_relevant_enough", None)
                    relevance_score = result.get("relevance_score", None)
                    es_count = result.get("es_results_count", 0)
                    naver_count = result.get("naver_results_count", 0)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("ES 검색 결과", f"{es_count}개")
                        st.metric("Naver 검색 결과", f"{naver_count}개")
                    with col2:
                        if relevance_score is not None:
                            st.metric("관련성 점수", f"{relevance_score:.2f}")
                        if is_relevant is not None:
                            status = "✅ 충분" if is_relevant else "⚠️ 부족"
                            st.metric("관련성 판단", status)
            
            st.markdown("---")
            
            # 답변은 항상 표시
            st.markdown("### 💬 답변")
            st.markdown(answer)
            st.markdown("---")
            
            # 내부 DB 결과 파싱 및 표시 (내부 DB에서 정보를 가져올 때만)
            internal_db_results = parse_internal_db_results(result.get("internal_db_results"))
            if internal_db_results and len(internal_db_results) > 0:
                st.markdown("### 📚 내부 DB 검색 결과")
                st.success(f"✅ {len(internal_db_results)}개의 내부 DB 검색 결과를 찾았습니다")
                st.markdown("---")
                
                for i, db_result in enumerate(internal_db_results, 1):
                    display_internal_db_result(db_result, i)
                
                st.markdown("---")
            
            # Naver 검색 결과 표시 (백엔드에서 직접 받은 결과 우선, 없으면 answer에서 파싱)
            naver_results_from_backend = result.get("naver_results", [])
            search_results = []
            
            if naver_results_from_backend and len(naver_results_from_backend) > 0:
                # 백엔드에서 직접 받은 Naver 결과 사용
                for item in naver_results_from_backend:
                    search_results.append(SearchResult(
                        title=item.get("title", "제목 없음"),
                        link=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        source=item.get("source", "Naver"),
                        published_date=item.get("published_date")
                    ))
            else:
                # 백엔드에서 결과가 없으면 answer에서 파싱 시도
                search_results = parse_search_results(answer)
            
            if search_results and len(search_results) > 0:
                # Naver 검색 결과가 있으면 카드 형태로 표시 (기존 요약 기능 유지)
                st.markdown("### 🔍 웹 검색 결과 (Naver)")
                st.success(f"✅ {len(search_results)}개의 웹 검색 결과를 찾았습니다")
                st.markdown("---")
                
                for i, result_item in enumerate(search_results, 1):
                    display_result(result_item, i)  # 기존 함수 사용 (요약 기능 포함, 클릭 시 네이버로 이동)
            
            # 대화 기록에 추가
            st.session_state.chat_history.append({"role": "user", "content": search_query})
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
    
    elif search_button and not search_query:
        st.warning("⚠️ Please enter a search query.")

if __name__ == "__main__":
    main()
