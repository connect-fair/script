import openai
from openai import RateLimitError, APIError
from typing import List, Dict, Any, Optional
import logging


class AIModelRouter:
    def __init__(self, model_configs: List[Dict[str, Any]]):
        """
        Initialize with a list of model configurations.

        Each config should contain:
        - model_name: str (e.g., "gpt-4", "gpt-3.5-turbo")
        - api_key: str
        - organization: Optional[str]
        - priority: int (lower number = higher priority)
        """
        self.models = sorted(model_configs, key=lambda x: x['priority'])
        self.current_model_index = 0
        self.logger = logging.getLogger(__name__)

    def _get_current_client(self) -> openai.OpenAI:
        """Get configured client for current model"""
        config = self.models[self.current_model_index]
        return openai.OpenAI(
            base_url="https://models.github.ai/inference",
            api_key=config['api_key'],
            organization=config.get('organization')
        )

    def _rotate_model(self) -> bool:
        """Move to next available model, return True if successful"""
        self.logger.info(f"Rotate model from {self.models[self.current_model_index]['model_name']}")
        if self.current_model_index + 1 < len(self.models):
            self.current_model_index += 1
            self.logger.info(f"Rotating to model {self.models[self.current_model_index]['model_name']}")
            return True
        return False

    def run(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Execute the chat completion with automatic model rotation on failures

        Args:
            messages: List of chat messages in OpenAI format
            **kwargs: Additional completion parameters

        Returns:
            Dictionary with 'success', 'result', and 'model_used' keys

        Raises:
            Exception: If all models fail
        """
        last_error = None

        while True:
            current_config = self.models[self.current_model_index]
            client = self._get_current_client()

            try:
                response = client.chat.completions.create(
                    model=current_config['model_name'],
                    messages=messages,
                    **kwargs
                )

                return {
                    'success': True,
                    'result': response.choices[0].message.content,
                    'model_used': current_config['model_name']
                }

            except RateLimitError as e:
                self.logger.warning(f"Rate limit hit for {current_config['model_name']}", e)
                last_error = e
                if not self._rotate_model():
                    break

            except APIError as e:
                self.logger.error(f"API error with {current_config['model_name']}: {str(e)}")
                last_error = e
                if not self._rotate_model():
                    break

            except Exception as e:
                self.logger.error(f"Unexpected error with {current_config['model_name']}: {str(e)}")
                last_error = e
                if not self._rotate_model():
                    break

        raise Exception("All models failed") from last_error

    def get_result(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """
        Simplified version that just returns the content or None

        Args:
            messages: List of chat messages in OpenAI format
            **kwargs: Additional completion parameters

        Returns:
            Content string if successful, None otherwise
        """
        try:
            result = self.run(messages, **kwargs)
            return result['result']
        except Exception:
            return None