"""
Configuration loader with environment variable override support
"""

import os
from typing import Optional, Any
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load configuration from files and environment variables"""
    
    @staticmethod
    def load_config(config_path: Optional[str] = None) -> dict:
        """Load configuration with proper precedence"""
        config = {}
        
        # 1. Load from YAML file if exists
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load config from {config_path}: {e}")
        
        # 2. Override with environment variables
        env_overrides = {
            # LLM Configuration
            'LLM_PROVIDER': os.getenv('LLM_PROVIDER', config.get('llm', {}).get('provider', 'mock')),
            'LLM_API_KEY': os.getenv('LLM_API_KEY', os.getenv('OPENAI_API_KEY', 'mock_key_for_testing')),
            'LLM_MODEL': os.getenv('LLM_MODEL', config.get('llm', {}).get('model', 'gpt-4o-mini')),
            'LLM_BASE_URL': os.getenv('LLM_BASE_URL', config.get('llm', {}).get('base_url')),
            'ENABLE_MOCK_LLM': os.getenv('ENABLE_MOCK_LLM', 'false').lower() == 'true',
            
            # OpenAI specific (for compatibility)
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', os.getenv('LLM_API_KEY', 'mock_key_for_testing')),
            'OPENAI_MODEL': os.getenv('OPENAI_MODEL', os.getenv('LLM_MODEL', 'gpt-4o-mini')),
            
            # Application
            'ENVIRONMENT': os.getenv('ENVIRONMENT', 'development'),
            'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true',
            'TESTING': os.getenv('TESTING', 'false').lower() == 'true',
        }
        
        # Apply overrides
        for key, value in env_overrides.items():
            if value is not None:
                config[key] = value
        
        # 3. Handle mock mode logic
        if config.get('ENABLE_MOCK_LLM') or config.get('LLM_PROVIDER') == 'mock':
            config['ENABLE_MOCK_LLM'] = True
            config['LLM_PROVIDER'] = 'mock'
            logger.info("Mock LLM mode enabled")
        
        # Check if API key is actually valid
        api_key = config.get('LLM_API_KEY') or config.get('OPENAI_API_KEY')
        if not api_key or api_key in ['mock_key_for_testing', 'dummy_key', '']:
            config['ENABLE_MOCK_LLM'] = True
            logger.info("No valid API key found - enabling mock mode")
        
        return config
    
    @staticmethod
    def is_mock_mode(config: dict) -> bool:
        """Check if system should run in mock mode"""
        return (
            config.get('ENABLE_MOCK_LLM', False) or
            config.get('LLM_PROVIDER') == 'mock' or
            config.get('TESTING', False) or
            not ConfigLoader._has_valid_api_key(config)
        )
    
    @staticmethod
    def _has_valid_api_key(config: dict) -> bool:
        """Check if a valid API key is configured"""
        api_key = config.get('LLM_API_KEY') or config.get('OPENAI_API_KEY')
        return api_key and api_key not in ['mock_key_for_testing', 'dummy_key', '', None]