"""
Generation 노드
구축된 컨텍스트를 기반으로 최종 답변을 생성합니다.
"""

import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.agent_state import AgentState
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage
from rag.prompts import get_generation_prompt
from rag.utils.source_extractor import format_sources_for_answer


def generate_answer(state: AgentState, llm: BaseChatModel) -> AgentState:
    """
    답변 생성 노드
    
    - 구축된 컨텍스트로 LLM 호출
    - 최종 답변 생성
    
    Args:
        state: 현재 상태
        llm: LLM 객체
    
    Returns:
        answer가 추가된 상태
    """
    import time
    start_time = time.time()
    
    print("\n" + "="*80)
    print("[6단계] GENERATION - 최종 답변 생성 시작")
    print("="*80)
    
    user_query = state["user_query"]
    context = state.get("context", "")
    chat_history = state.get("chat_history", [])
    
    print(f"사용자 질문: {user_query}")
    print(f"컨텍스트 길이: {len(context):,}자")
    print(f"대화 기록 수: {len(chat_history)}개")
    print(f"LLM 모델: {type(llm).__name__}")
    print(f"[INFO] LLM 호출 중...")
    
    # 웹 검색 결과 우선 사용 여부 확인
    web_results = state.get("web_results", {})
    has_web_results = len(web_results) > 0
    
    # ES 결과 존재 여부 확인
    es_results = state.get("es_results", {})
    has_es_results = es_results.get("total", 0) > 0
    
    # 강화된 프롬프트 템플릿 사용
    prompt = get_generation_prompt(
        user_query=user_query,
        context=context,
        has_web_results=has_web_results,
        has_es_results=has_es_results,
        chat_history=chat_history
    )
    
    try:
        # 대화 기록이 있으면 포함
        messages = []
        
        # 이전 대화 기록 추가
        for msg in chat_history:
            if msg.get("role") == "user":
                messages.append(HumanMessage(content=msg.get("content", "")))
            elif msg.get("role") == "assistant":
                messages.append(AIMessage(content=msg.get("content", "")))
        
        # 현재 질문 추가
        messages.append(HumanMessage(content=prompt))
        
        # LLM 호출
        response = llm.invoke(messages)
        answer = response.content if hasattr(response, 'content') else str(response)
        
        # 소스 정보를 답변에 추가
        sources = state.get("sources", [])
        if sources:
            from rag.utils.source_extractor import Source
            source_objects = [Source(**s) for s in sources]
            sources_text = format_sources_for_answer(source_objects)
            
            # 답변에 이미 출처가 포함되어 있지 않으면 추가
            if "참고 자료" not in answer and "출처" not in answer:
                answer += sources_text
            state["sources"] = sources
        
        print(f"[OK] 답변 생성 완료")
        print(f"   답변 길이: {len(answer):,}자")
        print(f"   포함된 소스 수: {len(sources)}개")
        print(f"   답변 미리보기 (처음 200자):")
        print(f"      {answer[:200]}...")
        
    except Exception as e:
        print(f"[ERROR] 답변 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        answer = f"답변 생성 중 오류가 발생했습니다: {str(e)}"
    
    elapsed_time = time.time() - start_time
    print(f"소요 시간: {elapsed_time:.2f}초")
    print("="*80 + "\n")
    
    state["answer"] = answer
    return state

