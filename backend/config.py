"""
애플리케이션 설정
환경 변수를 우선 사용하며, 없으면 기본값을 사용합니다.
"""

import os
from typing import Optional

# Naver API 설정
# 환경 변수가 설정되어 있으면 우선 사용, 없으면 기본값 사용
NAVER_CLIENT_ID: Optional[str] = os.getenv(
    'NAVER_CLIENT_ID',
    '2bmqIIx_yzk2giL30srA'  # 기본값 (개발용)
)

NAVER_CLIENT_SECRET: Optional[str] = os.getenv(
    'NAVER_CLIENT_SECRET',
    'nUDzJcr8Da'  # 기본값 (개발용)
)

# Google API 설정 (선택사항)
GOOGLE_API_KEY: Optional[str] = os.getenv('GOOGLE_API_KEY', None)
GOOGLE_SEARCH_ENGINE_ID: Optional[str] = os.getenv('GOOGLE_SEARCH_ENGINE_ID', None)

# ElasticSearch 설정
ELASTICSEARCH_HOST: str = os.getenv('ELASTICSEARCH_HOST', 'localhost')
ELASTICSEARCH_PORT: int = int(os.getenv('ELASTICSEARCH_PORT', '9200'))

# LLM 설정
# Gemini API Key (기본값으로 사용)
GEMINI_API_KEY: Optional[str] = os.getenv('GEMINI_API_KEY', None)

# OpenAI API Key (Gemini가 없을 때 사용)
OPENAI_API_KEY: Optional[str] = os.getenv(
    'OPENAI_API_KEY',
    None)

# 서버 설정
SERVER_HOST: str = os.getenv('SERVER_HOST', '0.0.0.0')
SERVER_PORT: int = int(os.getenv('SERVER_PORT', '8000'))

# 로깅 설정
LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

