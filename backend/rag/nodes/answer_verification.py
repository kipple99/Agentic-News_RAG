"""
답변 검증 노드
생성된 답변의 정확성과 품질을 검증합니다.
"""

import sys
import os
import json

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.agent_state import AgentState
from langchain_core.language_models import BaseChatModel


def verify_answer(state: AgentState, llm: BaseChatModel) -> AgentState:
    """
    답변 검증 노드
    
    생성된 답변의 정확성, 컨텍스트 일치도, 환각 여부를 검증합니다.
    
    Args:
        state: 현재 상태
        llm: LLM 객체
    
    Returns:
        검증 결과가 추가된 상태
    """
    import time
    start_time = time.time()
    
    print("\n" + "="*80)
    print("[7단계] ANSWER VERIFICATION - 답변 검증 시작")
    print("="*80)
    
    user_query = state["user_query"]
    answer = state.get("answer", "")
    context = state.get("context", "")
    
    if not answer:
        print("[WARN] 검증할 답변이 없습니다.")
        print("="*80 + "\n")
        state["answer_verified"] = False
        state["verification_issues"] = ["답변이 없습니다."]
        return state
    
    print(f"사용자 질문: {user_query[:50]}...")
    print(f"답변 길이: {len(answer):,}자")
    print(f"컨텍스트 길이: {len(context):,}자")
    
    # 검증 프롬프트
    prompt = f"""당신은 답변 검증 전문가입니다. 다음 답변이 제공된 컨텍스트와 일치하는지, 정확한지 검증하세요.

## 사용자 질문
"{user_query}"

## 제공된 컨텍스트
{context[:3000]}

## 생성된 답변
{answer}

## 검증 항목

1. **정확성 (Accuracy)**
   - 답변이 컨텍스트에 기반하고 있는가?
   - 사실 오류가 없는가?
   - 숫자, 날짜, 이름 등이 정확한가?

2. **일치도 (Consistency)**
   - 답변이 컨텍스트의 정보와 일치하는가?
   - 컨텍스트에 없는 정보를 만들어내지 않았는가? (환각)

3. **완전성 (Completeness)**
   - 질문에 충분히 답하고 있는가?
   - 중요한 정보가 누락되지 않았는가?

4. **관련성 (Relevance)**
   - 답변이 질문과 관련이 있는가?
   - 불필요한 정보가 포함되지 않았는가?

## 출력 형식

다음 JSON 형식으로 응답하세요:

{{
    "is_accurate": true/false,
    "is_consistent": true/false,
    "is_complete": true/false,
    "is_relevant": true/false,
    "overall_score": 0.0-1.0,
    "confidence": 0.0-1.0,
    "issues": ["문제점1", "문제점2"],
    "suggested_corrections": "수정 제안 (있는 경우)",
    "verification_summary": "검증 요약"
}}

마크다운 코드 블록 없이 순수 JSON만 출력하세요."""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # JSON 파싱
        import re
        match = re.search(r"```json\s*([\s\S]*?)\s*```", content)
        if match:
            json_string = match.group(1).strip()
        else:
            json_string = content
        
        verification = json.loads(json_string)
        
        # 검증 결과 저장
        state["answer_verified"] = verification.get("is_accurate", True) and \
                                   verification.get("is_consistent", True)
        state["verification_score"] = verification.get("overall_score", 1.0)
        state["verification_issues"] = verification.get("issues", [])
        state["verification_details"] = verification
        
        print(f"[OK] 답변 검증 완료")
        print(f"   정확성: {'[OK]' if verification.get('is_accurate') else '[WARN]'}")
        print(f"   일치도: {'[OK]' if verification.get('is_consistent') else '[WARN]'}")
        print(f"   완전성: {'[OK]' if verification.get('is_complete') else '[WARN]'}")
        print(f"   관련성: {'[OK]' if verification.get('is_relevant') else '[WARN]'}")
        print(f"   전체 점수: {verification.get('overall_score', 0.0):.2f}")
        
        if verification.get("issues"):
            print(f"   발견된 문제점:")
            for issue in verification.get("issues", [])[:3]:
                print(f"      - {issue}")
        
        # 검증 실패 시 경고
        if not state["answer_verified"]:
            print(f"   [WARN] 답변 검증 실패: 일부 문제가 발견되었습니다.")
    
    except Exception as e:
        print(f"[ERROR] 답변 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        
        # 기본값 설정
        state["answer_verified"] = True  # 검증 실패 시 기본적으로 통과
        state["verification_score"] = 0.5
        state["verification_issues"] = [f"검증 과정 오류: {str(e)}"]
        state["verification_details"] = {}
    
    elapsed_time = time.time() - start_time
    print(f"소요 시간: {elapsed_time:.2f}초")
    print("="*80 + "\n")
    
    return state


