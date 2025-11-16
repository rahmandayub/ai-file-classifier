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

    SYSTEM_PROMPT_TEMPLATE = """You are an expert file organization assistant. Your task is to analyze file information and suggest appropriate directory classifications.

Rules:
1. Provide concise, meaningful directory names IN {language} LANGUAGE
2. Use hierarchical structure (parent/child) when appropriate
3. Avoid overly specific categories (max 3 levels deep)
4. Consider file content, name, and metadata
5. Return results in valid JSON format
6. ALL directory names (primary_category, subcategory, sub_subcategory) MUST be in {language}

Language-specific examples for {language}:
{examples}

Output format:
{{
  "primary_category": "string (in {language})",
  "subcategory": "string or null (in {language})",
  "sub_subcategory": "string or null (in {language})",
  "confidence": float (0.0-1.0),
  "reasoning": "string (can be in English)"
}}"""

    LANGUAGE_EXAMPLES = {
        "indonesian": """- Documents → "Dokumen"
- Financial Reports → "Laporan Keuangan"
- Personal Photos → "Foto Pribadi"
- Work Projects → "Proyek Pekerjaan"
- Music → "Musik"
- Videos → "Video"
- Archives → "Arsip"
- Downloads → "Unduhan"
- Images → "Gambar"
- Spreadsheets → "Lembar Kerja"
- Presentations → "Presentasi"
- Code → "Kode Program"
- Books → "Buku"
- Contracts → "Kontrak"
- Invoices → "Faktur"
- Receipts → "Kwitansi"
- Tax Documents → "Dokumen Pajak"
- Annual Reports → "Laporan Tahunan"
- Meeting Notes → "Catatan Rapat"
- Research → "Penelitian"
""",
        "english": """- Documents → "Documents"
- Financial Reports → "Financial Reports"
- Personal Photos → "Personal Photos"
- Work Projects → "Work Projects"
- Music → "Music"
- Videos → "Videos"
- Archives → "Archives"
""",
        "spanish": """- Documents → "Documentos"
- Financial Reports → "Informes Financieros"
- Personal Photos → "Fotos Personales"
- Work Projects → "Proyectos de Trabajo"
""",
        "french": """- Documents → "Documents"
- Financial Reports → "Rapports Financiers"
- Personal Photos → "Photos Personnelles"
- Work Projects → "Projets de Travail"
"""
    }

    def __init__(
        self,
        llm_client: LLMClient,
        cache_manager: Optional[CacheManager] = None,
        max_retries: int = 3,
        retry_delay: int = 2,
        language: str = "english",
        fallback_language: str = "english"
    ):
        """
        Initialize the AI classifier.

        Args:
            llm_client: LLM client instance
            cache_manager: Optional cache manager
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            language: Primary language for directory names
            fallback_language: Fallback language if primary not available
        """
        self.llm_client = llm_client
        self.cache_manager = cache_manager
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.language = language.lower()
        self.fallback_language = fallback_language.lower()

        # Build system prompt with language-specific examples
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """
        Build system prompt with language-specific examples.

        Returns:
            Formatted system prompt string
        """
        # Get examples for the selected language
        examples = self.LANGUAGE_EXAMPLES.get(
            self.language,
            self.LANGUAGE_EXAMPLES.get(self.fallback_language, self.LANGUAGE_EXAMPLES["english"])
        )

        # Format the prompt
        return self.SYSTEM_PROMPT_TEMPLATE.format(
            language=self.language.upper(),
            examples=examples
        )

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
            {"role": "system", "content": self.system_prompt},
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
            {"role": "system", "content": self.system_prompt},
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

    async def classify_multi_file_batch(
        self,
        file_infos: List[FileInfo],
        max_files_per_request: int = 5
    ) -> List[Optional[Classification]]:
        """
        Classify multiple files in a single API request (advanced optimization).

        This method sends multiple files to the LLM in one request, reducing
        API calls but increasing token usage per request.

        Args:
            file_infos: List of file information objects
            max_files_per_request: Maximum files to include in one API request

        Returns:
            List of classification results in the same order as input
        """
        if not file_infos:
            return []

        # Check cache for all files first
        cached_results = []
        uncached_files = []
        uncached_indices = []

        for i, file_info in enumerate(file_infos):
            if self.cache_manager:
                cache_key = self.cache_manager.get_cache_key(
                    str(file_info.path),
                    file_info.size,
                    file_info.modified.timestamp()
                )
                cached = self.cache_manager.get(cache_key)
                if cached:
                    logger.debug(f"Using cached classification for {file_info.name}")
                    cached_results.append((i, Classification.from_dict(cached)))
                    continue

            uncached_files.append(file_info)
            uncached_indices.append(i)

        # Build multi-file prompt
        prompt = self._build_multi_file_prompt(uncached_files[:max_files_per_request])
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]

        # Send request with retry logic
        for attempt in range(self.max_retries):
            try:
                response_text = await self.llm_client.send_request_async(messages)
                classifications = self._parse_multi_file_response(
                    response_text,
                    uncached_files[:max_files_per_request]
                )

                if classifications:
                    # Cache results
                    for file_info, classification in zip(
                        uncached_files[:max_files_per_request],
                        classifications
                    ):
                        if classification and self.cache_manager:
                            cache_key = self.cache_manager.get_cache_key(
                                str(file_info.path),
                                file_info.size,
                                file_info.modified.timestamp()
                            )
                            self.cache_manager.set(cache_key, classification.to_dict())

                    # Merge cached and new results
                    results = [None] * len(file_infos)
                    for i, classification in cached_results:
                        results[i] = classification
                    for i, classification in enumerate(classifications):
                        results[uncached_indices[i]] = classification

                    return results

            except RateLimitError:
                wait_time = self.retry_delay * (2 ** attempt)
                logger.warning(f"Rate limit hit, waiting {wait_time}s")
                await asyncio.sleep(wait_time)

            except Exception as e:
                logger.error(f"Multi-file batch classification failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))

        # Fallback to individual classification if multi-file batch fails
        logger.warning("Multi-file batch failed, falling back to individual classification")
        return await self.classify_batch(file_infos)

    def _build_multi_file_prompt(self, file_infos: List[FileInfo]) -> str:
        """
        Build a prompt for classifying multiple files at once.

        Args:
            file_infos: List of file information objects

        Returns:
            Formatted prompt string
        """
        prompt = f"""Classify the following {len(file_infos)} files.
Return a JSON array with {len(file_infos)} classification objects in the SAME ORDER as the files below.

"""
        for i, file_info in enumerate(file_infos, 1):
            prompt += f"""
File {i}:
  Filename: {file_info.name}
  Extension: {file_info.extension}
  Size: {file_info.size_formatted}
  Modified: {file_info.modified_date}
"""
            if file_info.content_preview:
                preview = file_info.content_preview[:200]  # Shorter for multi-file
                prompt += f"  Content Preview: {preview}...\n"

        prompt += f"""
Return format (JSON array with {len(file_infos)} objects):
[
  {{
    "primary_category": "string (in {self.language.upper()})",
    "subcategory": "string or null (in {self.language.upper()})",
    "sub_subcategory": "string or null (in {self.language.upper()})",
    "confidence": float (0.0-1.0),
    "reasoning": "string"
  }},
  ...
]
"""
        return prompt

    def _parse_multi_file_response(
        self,
        response_text: str,
        file_infos: List[FileInfo]
    ) -> List[Optional[Classification]]:
        """
        Parse LLM response for multi-file classification.

        Args:
            response_text: Raw response text from LLM
            file_infos: List of file information objects

        Returns:
            List of classification objects or None values
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

            # Validate it's an array
            if not isinstance(data, list):
                logger.error("Multi-file response is not an array")
                return [None] * len(file_infos)

            # Parse each classification
            results = []
            for item in data:
                try:
                    JSONResponseValidator.validate_classification_response(item)
                    results.append(Classification.from_dict(item))
                except Exception as e:
                    logger.error(f"Failed to parse classification item: {e}")
                    results.append(None)

            # Ensure we have the right number of results
            while len(results) < len(file_infos):
                results.append(None)

            return results[:len(file_infos)]

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse multi-file JSON response: {e}")
            logger.debug(f"Response text: {response_text[:500]}")
            return [None] * len(file_infos)

        except Exception as e:
            logger.error(f"Failed to parse multi-file classification: {e}")
            return [None] * len(file_infos)

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
