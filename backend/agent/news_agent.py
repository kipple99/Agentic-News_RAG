# -*- coding: utf-8 -*-
"""
뉴스 검색 에이전트
API 검색과 LLM 생성을 지능적으로 판단하여 선택합니다.
LangChain 1.0+ 구조 사용
"""

import sys
import os
from typing import List, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from external.naver_client import UnifiedSearchClient, SearchResult
except ImportError:
    UnifiedSearchClient = None
    SearchResult = None

from .llm_factory import LLMFactory


@tool
def search_news_api(query: str) -> str:
    """
    뉴스 검색 API를 사용하여 최신 뉴스를 검색합니다.
    구체적인 키워드, 최신 뉴스, 특정 사건이나 인물에 대한 검색에 사용합니다.
    
    Args:
        query: 검색할 키워드 또는 질문
    
    Returns:
        검색 결과 (제목, 링크, 요약)
    """
    try:
        if UnifiedSearchClient is None:
            return "검색 API 클라이언트를 사용할 수 없습니다."
        
        client = UnifiedSearchClient()
        results = client.search(query, num_results=5)
        
        if not results:
            return "검색 결과가 없습니다."
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(
                f"{i}. 제목: {result.title}\n"
                f"   링크: {result.link}\n"
                f"   요약: {result.snippet[:200]}...\n"
                f"   출처: {result.source}\n"
            )
        
        return "\n".join(formatted_results)
    except Exception as e:
        return f"검색 중 오류 발생: {str(e)}"


def decide_search_method(query: str) -> str:
    """
    사용자 쿼리를 분석하여 API 검색이 적합한지 LLM 생성이 적합한지 판단합니다.
    
    판단 기준:
    - API 검색이 적합한 경우: 구체적인 키워드, 최신 뉴스, 특정 사건/인물, 날짜 포함
    - LLM 생성이 적합한 경우: 일반적인 질문, 개념 설명, 추상적 질문
    
    Args:
        query: 사용자 쿼리
    
    Returns:
        "api_search" 또는 "llm_generate"
    """
    api_keywords = [
        "최신", "오늘", "어제", "이번 주", "최근", "뉴스", "기사",
        "검색", "찾아", "알려줘", "보여줘", "어떤", "누구", "언제", "어디서"
    ]
    
    llm_keywords = [
        "무엇", "어떻게", "왜", "설명", "요약", "분석", "의미", "개념",
        "차이", "비교", "관계", "영향"
    ]
    
    query_lower = query.lower()
    
    api_score = sum(1 for keyword in api_keywords if keyword in query_lower)
    llm_score = sum(1 for keyword in llm_keywords if keyword in query_lower)
    
    if api_score > llm_score:
        return "api_search"
    elif llm_score > api_score:
        return "llm_generate"
    else:
        return "api_search"


class NewsAgent:
    """뉴스 검색 에이전트 클래스 (LangChain 1.0+ 구조)"""
    
    def __init__(
        self,
        llm: Optional[object] = None,
        model_type: str = "openai",
        use_memory: bool = True
    ):
        """
        Args:
            llm: LangChain LLM 인스턴스 (None이면 자동 생성)
            model_type: LLM 모델 타입 ("openai", "ollama", "huggingface", "gemini")
            use_memory: 대화 기록 사용 여부
        """
        # LLM 초기화
        if llm is None:
            try:
                self.llm = LLMFactory.create_llm(model_type)
            except:
                self.llm = LLMFactory.get_default_llm()
        else:
            self.llm = llm
        
        # 도구 정의 (search_news_api만 tool로 사용, decide_search_method는 일반 함수)
        self.tools = [search_news_api]
        
        # 메모리
        self.memory = [] if use_memory else None
        
        print("✓ NewsAgent initialized (simplified version)")
    
    def run(self, query: str, chat_history: Optional[List] = None) -> str:
        """
        에이전트 실행 - 간단한 판단 로직 사용
        
        Args:
            query: 사용자 쿼리
            chat_history: 대화 기록 (선택사항)
        
        Returns:
            에이전트 응답
        """
        try:
            # 판단: API 검색 vs LLM 생성
            method = decide_search_method(query)
            
            if method == "api_search":
                # API 검색 실행 (tool은 invoke로 호출)
                try:
                    result = search_news_api.invoke({"query": query})
                except Exception as e:
                    # invoke 실패 시 직접 함수 호출 시도
                    if hasattr(search_news_api, 'func'):
                        result = search_news_api.func(query)
                    else:
                        raise e
                
                # LLM으로 결과 포맷팅
                prompt = f"""다음 뉴스 검색 결과를 사용자에게 친절하게 정리해서 알려주세요:

검색어: {query}

검색 결과:
{result}

사용자에게 검색 결과를 명확하고 읽기 쉽게 정리해서 답변해주세요."""
                
                messages = []
                if chat_history:
                    messages.extend(chat_history)
                messages.append(HumanMessage(content=prompt))
                
                response = self.llm.invoke(messages)
                answer = response.content if hasattr(response, 'content') else str(response)
                
            else:
                # LLM 생성
                prompt = f"""사용자의 질문에 대해 도움이 되는 답변을 제공해주세요:

질문: {query}

친절하고 정확한 답변을 작성해주세요."""
                
                messages = []
                if chat_history:
                    messages.extend(chat_history)
                messages.append(HumanMessage(content=prompt))
                
                response = self.llm.invoke(messages)
                answer = response.content if hasattr(response, 'content') else str(response)
            
            # 메모리에 추가
            if self.memory is not None:
                self.memory.append(HumanMessage(content=query))
                self.memory.append(AIMessage(content=answer))
            
            return answer
            
        except Exception as e:
            import traceback
            error_msg = f"오류 발생: {str(e)}\n{traceback.format_exc()}"
            print(f"Error in agent.run: {error_msg}")
            return f"오류 발생: {str(e)}"
    
    def clear_memory(self):
        """대화 기록 초기화"""
        if self.memory is not None:
            self.memory = []


def create_news_agent(
    model_type: str = "openai",
    model_name: Optional[str] = None,
    use_memory: bool = True,
    **kwargs
) -> NewsAgent:
    """
    뉴스 에이전트 생성 편의 함수
    
    Args:
        model_type: LLM 모델 타입 ("openai", "ollama", "huggingface", "gemini")
        model_name: 모델 이름 (선택사항)
        use_memory: 대화 기록 사용 여부
        **kwargs: 추가 LLM 파라미터
    
    Returns:
        NewsAgent 인스턴스
    """
    llm = None
    if model_name:
        kwargs['model_name'] = model_name
    
    try:
        llm = LLMFactory.create_llm(model_type, **kwargs)
    except Exception as e:
        print(f"LLM 생성 실패: {e}, 기본 LLM 사용 시도...")
        llm = None
    
    return NewsAgent(llm=llm, model_type=model_type, use_memory=use_memory)

