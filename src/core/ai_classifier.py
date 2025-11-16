"""AI-powered file classification using LLM."""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI, OpenAI
from openai import (
    APIError,
    APIConnectionError,
    RateLimitError,
    APITimeoutError
)

from ..models.file_info import FileInfo
from ..models.classification import Classification
from ..utils.logger import get_logger
from ..utils.exceptions import APIError as ClassifierAPIError, ClassificationError
from ..utils.validators import JSONResponseValidator
from ..utils.cache_manager import CacheManager

logger = get_logger()


class LLMClient:
    """Client for interacting with OpenAI-compatible APIs."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM client.

        Args:
            config: API configuration dictionary
        """
        self.config = config
        self.client = OpenAI(
            api_key=config.get('api_key', 'default'),
            base_url=config['base_url'],
            timeout=config.get('timeout', 30),
            max_retries=0  # We handle retries manually
        )
        self.async_client = AsyncOpenAI(
            api_key=config.get('api_key', 'default'),
            base_url=config['base_url'],
            timeout=config.get('timeout', 30),
            max_retries=0
        )
        self.model = config['model_name']
        self.temperature = config.get('temperature', 0.2)
        self.max_tokens = config.get('max_tokens', 1000)

    def send_request(self, messages: List[Dict[str, str]]) -> str:
        """
        Send synchronous request to LLM.

        Args:
            messages: List of message dictionaries

        Returns:
            Response text from LLM

        Raises:
            ClassifierAPIError: If API call fails
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"API request failed: {e}")
            raise ClassifierAPIError(f"LLM API call failed: {e}")

    async def send_request_async(self, messages: List[Dict[str, str]]) -> str:
        """
        Send asynchronous request to LLM.

        Args:
            messages: List of message dictionaries

        Returns:
            Response text from LLM

        Raises:
            ClassifierAPIError: If API call fails
        """
        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Async API request failed: {e}")
            raise ClassifierAPIError(f"LLM API call failed: {e}")


class AIClassifier:
    """AI-powered file classifier using LLM."""

    SYSTEM_PROMPT = """You are an expert file organization assistant. Your task is to analyze file information and suggest appropriate directory classifications.

Rules:
1. Provide concise, meaningful directory names
2. Use hierarchical structure (parent/child) when appropriate
3. Avoid overly specific categories (max 3 levels deep)
4. Consider file content, name, and metadata
5. Return results in valid JSON format

Output format:
{
  "primary_category": "string",
  "subcategory": "string or null",
  "sub_subcategory": "string or null",
  "confidence": float (0.0-1.0),
  "reasoning": "string"
}"""

    def __init__(
        self,
        llm_client: LLMClient,
        cache_manager: Optional[CacheManager] = None,
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        """
        Initialize the AI classifier.

        Args:
            llm_client: LLM client instance
            cache_manager: Optional cache manager
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.llm_client = llm_client
        self.cache_manager = cache_manager
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def classify(self, file_info: FileInfo) -> Optional[Classification]:
        """
        Classify a single file.

        Args:
            file_info: File information object

        Returns:
            Classification result or None if failed
        """
        # Check cache first
        if self.cache_manager:
            cache_key = self.cache_manager.get_cache_key(
                str(file_info.path),
                file_info.size,
                file_info.modified.timestamp()
            )
            cached = self.cache_manager.get(cache_key)
            if cached:
                logger.debug(f"Using cached classification for {file_info.name}")
                return Classification.from_dict(cached)

        # Build prompt
        prompt = self._build_content_prompt(file_info)
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        # Send request with retry logic
        for attempt in range(self.max_retries):
            try:
                response_text = self.llm_client.send_request(messages)
                classification = self._parse_response(response_text)

                if classification:
                    # Cache the result
                    if self.cache_manager:
                        self.cache_manager.set(cache_key, classification.to_dict())

                    logger.info(
                        f"Classified {file_info.name} -> {classification.directory_path} "
                        f"(confidence: {classification.confidence:.2f})"
                    )
                    return classification

            except RateLimitError:
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"Rate limit hit, waiting {wait_time}s")
                time.sleep(wait_time)

            except APITimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to classify {file_info.name} after {self.max_retries} attempts")

            except (APIConnectionError, APIError) as e:
                logger.error(f"API error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))

            except ClassifierAPIError as e:
                logger.error(f"Classification failed: {e}")
                if attempt == self.max_retries - 1:
                    break

        return None

    async def classify_async(self, file_info: FileInfo) -> Optional[Classification]:
        """
        Classify a single file asynchronously.

        Args:
            file_info: File information object

        Returns:
            Classification result or None if failed
        """
        # Check cache first
        if self.cache_manager:
            cache_key = self.cache_manager.get_cache_key(
                str(file_info.path),
                file_info.size,
                file_info.modified.timestamp()
            )
            cached = self.cache_manager.get(cache_key)
            if cached:
                logger.debug(f"Using cached classification for {file_info.name}")
                return Classification.from_dict(cached)

        # Build prompt
        prompt = self._build_content_prompt(file_info)
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]

        # Send request with retry logic
        for attempt in range(self.max_retries):
            try:
                response_text = await self.llm_client.send_request_async(messages)
                classification = self._parse_response(response_text)

                if classification:
                    # Cache the result
                    if self.cache_manager:
                        self.cache_manager.set(cache_key, classification.to_dict())

                    logger.info(
                        f"Classified {file_info.name} -> {classification.directory_path} "
                        f"(confidence: {classification.confidence:.2f})"
                    )
                    return classification

            except RateLimitError:
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"Rate limit hit, waiting {wait_time}s")
                await asyncio.sleep(wait_time)

            except APITimeoutError:
                logger.warning(f"Timeout on attempt {attempt + 1}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to classify {file_info.name} after {self.max_retries} attempts")

            except (APIConnectionError, APIError) as e:
                logger.error(f"API error: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))

            except ClassifierAPIError as e:
                logger.error(f"Classification failed: {e}")
                if attempt == self.max_retries - 1:
                    break

        return None

    async def classify_batch(self, file_infos: List[FileInfo]) -> List[Optional[Classification]]:
        """
        Classify multiple files concurrently.

        Args:
            file_infos: List of file information objects

        Returns:
            List of classification results
        """
        tasks = [self.classify_async(file_info) for file_info in file_infos]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to None
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch classification error: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)

        return processed_results

    def _build_content_prompt(self, file_info: FileInfo) -> str:
        """
        Build a prompt for content-based classification.

        Args:
            file_info: File information object

        Returns:
            Formatted prompt string
        """
        prompt = f"""Classify the following file:

Filename: {file_info.name}
Extension: {file_info.extension}
Size: {file_info.size_formatted}
Created: {file_info.created_date}
Modified: {file_info.modified_date}"""

        if file_info.content_preview:
            prompt += f"\n\nContent Preview:\n{file_info.content_preview[:500]}"

        prompt += "\n\nSuggest an appropriate directory structure for this file."

        return prompt

    def _parse_response(self, response_text: str) -> Optional[Classification]:
        """
        Parse LLM response and extract classification.

        Args:
            response_text: Raw response text from LLM

        Returns:
            Classification object or None if parsing failed
        """
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            data = json.loads(text.strip())

            # Validate response
            JSONResponseValidator.validate_classification_response(data)

            # Build classification
            return Classification.from_dict(data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            return None

        except Exception as e:
            logger.error(f"Failed to parse classification: {e}")
            return None
