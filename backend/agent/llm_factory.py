"""
무료 LLM 모델 팩토리
Ollama, Hugging Face 등 무료 LLM 모델을 지원합니다.
"""

import os
from typing import Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.messages import BaseMessage


class LLMFactory:
    """무료 LLM 모델 팩토리 클래스"""
    
    @staticmethod
    def create_llm(model_type: str = "ollama", **kwargs) -> BaseChatModel:
        """
        LLM 모델 생성
        
        Args:
            model_type: 모델 타입 ("ollama", "huggingface", "gemini")
            **kwargs: 모델별 추가 파라미터
        
        Returns:
            BaseChatModel 인스턴스
        """
        model_type = model_type.lower()
        
        if model_type == "ollama":
            return LLMFactory._create_ollama_llm(**kwargs)
        elif model_type == "huggingface":
            return LLMFactory._create_huggingface_llm(**kwargs)
        elif model_type == "gemini":
            return LLMFactory._create_gemini_llm(**kwargs)
        elif model_type == "openai":
            return LLMFactory._create_openai_llm(**kwargs)
        else:
            raise ValueError(f"지원하지 않는 모델 타입: {model_type}")
    
    @staticmethod
    def _create_ollama_llm(model_name: str = "llama3.2", **kwargs) -> BaseChatModel:
        """Ollama LLM 생성 (로컬 실행, 완전 무료)"""
        try:
            from langchain_community.llms import Ollama
            from langchain_community.chat_models import ChatOllama
            
            base_url = kwargs.get('base_url', 'http://localhost:11434')
            return ChatOllama(
                model=model_name,
                base_url=base_url,
                temperature=kwargs.get('temperature', 0.7),
            )
        except ImportError:
            raise ImportError(
                "langchain_community이 설치되지 않았습니다. "
                "설치: pip install langchain-community"
            )
    
    @staticmethod
    def _create_huggingface_llm(model_name: str = "mistralai/Mistral-7B-Instruct-v0.2", **kwargs) -> BaseChatModel:
        """Hugging Face LLM 생성 (무료, API 키 필요 없음)"""
        try:
            from langchain_community.llms import HuggingFacePipeline
            from langchain_community.chat_models import ChatHuggingFace
            from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
            
            # 모델 로드
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype="auto"
            )
            
            # 파이프라인 생성
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=kwargs.get('max_new_tokens', 512),
                temperature=kwargs.get('temperature', 0.7),
            )
            
            llm = HuggingFacePipeline(pipeline=pipe)
            return ChatHuggingFace(llm=llm)
        except ImportError:
            raise ImportError(
                "필요한 라이브러리가 설치되지 않았습니다. "
                "설치: pip install transformers torch langchain-community"
            )
    
    @staticmethod
    def _create_gemini_llm(api_key: Optional[str] = None, **kwargs) -> BaseChatModel:
        """Google Gemini LLM 생성 (무료 티어 있음)"""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            # config.py에서 가져오기 (우선순위: 인자 > 환경변수 > config.py)
            try:
                import sys
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from config import GEMINI_API_KEY as config_key
                api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY') or config_key
            except:
                api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
            
            if not api_key:
                raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
            
            return ChatGoogleGenerativeAI(
                model=kwargs.get('model_name', 'gemini-pro'),
                google_api_key=api_key,
                temperature=kwargs.get('temperature', 0.7),
            )
        except ImportError:
            raise ImportError(
                "langchain_google_genai가 설치되지 않았습니다. "
                "설치: pip install langchain-google-genai"
            )
    
    @staticmethod
    def _create_openai_llm(api_key: Optional[str] = None, **kwargs) -> BaseChatModel:
        """OpenAI LLM 생성"""
        try:
            from langchain_openai import ChatOpenAI
            
            # config.py에서 가져오기
            try:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from config import OPENAI_API_KEY as config_key
                api_key = api_key or os.getenv('OPENAI_API_KEY') or config_key
            except:
                api_key = api_key or os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
            
            return ChatOpenAI(
                model=kwargs.get('model_name', 'gpt-3.5-turbo'),
                api_key=api_key,
                temperature=kwargs.get('temperature', 0.7),
            )
        except ImportError:
            raise ImportError(
                "langchain_openai가 설치되지 않았습니다. "
                "설치: pip install langchain-openai"
            )
    
    @staticmethod
    def get_default_llm() -> BaseChatModel:
        """기본 LLM 반환 (Gemini 우선, 없으면 OpenAI, 그 다음 Ollama, Hugging Face)"""
        # Gemini 시도 (기본값)
        try:
            return LLMFactory._create_gemini_llm()
        except Exception as e:
            print(f"Gemini LLM 생성 실패: {e}, OpenAI 시도...")
            pass
        
        # OpenAI 시도 (Gemini가 없을 때)
        try:
            return LLMFactory._create_openai_llm()
        except Exception as e:
            print(f"OpenAI LLM 생성 실패: {e}, Ollama 시도...")
            pass
        
        # Ollama 시도
        try:
            return LLMFactory._create_ollama_llm()
        except:
            pass
        
        # Hugging Face 시도
        try:
            return LLMFactory._create_huggingface_llm()
        except:
            pass
        
        raise RuntimeError(
            "사용 가능한 LLM 모델을 찾을 수 없습니다. "
            "GEMINI_API_KEY 또는 OPENAI_API_KEY를 설정하거나 Ollama를 설치해주세요."
        )

