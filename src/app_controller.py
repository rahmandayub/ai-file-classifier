"""Application controller orchestrating the classification workflow."""

import asyncio
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core.file_scanner import FileScanner, FileFilter, create_scanner_from_config, create_filter_from_config
from .core.ai_classifier import AIClassifier, LLMClient
from .core.directory_manager import DirectoryManager, create_directory_manager_from_config
from .core.file_mover import FileMover, create_file_mover_from_config
from .core.report_generator import ReportGenerator
from .models.file_info import FileInfo
from .models.classification import Classification
from .strategies.content_based import ContentBasedStrategy
from .utils.logger import get_logger
from .utils.cache_manager import CacheManager
from .utils.exceptions import ClassifierError

logger = get_logger()


class ApplicationController:
    """Orchestrates the entire file classification workflow."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the application controller.

        Args:
            config: Application configuration dictionary
        """
        self.config = config

        # Initialize components
        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize all application components."""
        logger.info("Initializing application components...")

        # Cache manager
        cache_config = self.config['app']
        self.cache_manager = CacheManager(
            cache_dir=cache_config.get('cache_dir', '.cache'),
            ttl_hours=cache_config.get('cache_ttl_hours', 24),
            enabled=cache_config.get('cache_enabled', True)
        ) if cache_config.get('cache_enabled', True) else None

        # LLM client
        api_config = self.config['api']
        self.llm_client = LLMClient(api_config)

        # AI classifier with language support
        language_config = self.config.get('language', {})
        self.ai_classifier = AIClassifier(
            llm_client=self.llm_client,
            cache_manager=self.cache_manager,
            max_retries=api_config.get('max_retries', 3),
            retry_delay=api_config.get('retry_delay', 2),
            language=language_config.get('primary', 'english'),
            fallback_language=language_config.get('fallback', 'english')
        )

        # Classification strategy
        strategy_weight = self.config['classification']['strategies']['content_based'].get('weight', 1.0)
        self.strategy = ContentBasedStrategy(
            ai_classifier=self.ai_classifier,
            weight=strategy_weight
        )

        # File scanner
        scan_config = self.config['scanning']
        self.file_scanner = create_scanner_from_config(scan_config)
        self.file_filter = create_filter_from_config(scan_config)

        # Report generator
        report_config = self.config['reporting']
        self.report_generator = ReportGenerator(
            output_dir=report_config.get('output_dir', 'reports')
        )

        logger.info("Components initialized successfully")

    def execute(
        self,
        source_dir: Path,
        dest_dir: Path,
        dry_run: bool = False,
        generate_report: bool = True
    ) -> Dict[str, Any]:
        """
        Execute the complete classification workflow.

        Args:
            source_dir: Source directory to scan
            dest_dir: Destination directory for organized files
            dry_run: If True, preview changes without executing
            generate_report: Whether to generate reports

        Returns:
            Execution results dictionary
        """
        start_time = time.time()

        try:
            logger.info("="*60)
            logger.info("Starting file classification workflow")
            logger.info(f"Source: {source_dir}")
            logger.info(f"Destination: {dest_dir}")
            logger.info(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
            logger.info("="*60)

            # Step 1: Scan files
            logger.info("Step 1/5: Scanning files...")
            files = self._scan_files(source_dir)

            if not files:
                logger.warning("No files found to classify")
                return self._create_result([], {}, {}, 0)

            # Step 2: Classify files
            logger.info(f"Step 2/5: Classifying {len(files)} files...")
            classification_map = self._classify_files(files)

            # Step 3: Create directory structure
            logger.info("Step 3/5: Planning directory structure...")
            directory_manager = create_directory_manager_from_config(
                dest_dir,
                self.config['directories']
            )
            directory_manager.create_structure(classification_map, dry_run=dry_run)

            # Step 4: Move files
            logger.info("Step 4/5: Moving files...")
            operation_stats = self._move_files(
                files,
                classification_map,
                directory_manager,
                dry_run
            )

            # Step 5: Generate reports
            execution_time = time.time() - start_time
            logger.info(f"Step 5/5: Generating reports...")

            result = self._create_result(
                files,
                classification_map,
                operation_stats,
                execution_time
            )

            if generate_report and self.config['reporting'].get('enabled', True):
                self._generate_reports(classification_map, operation_stats, execution_time)

            logger.info("="*60)
            logger.info("Classification workflow completed successfully")
            logger.info(f"Total time: {execution_time:.2f} seconds")
            logger.info(f"Files processed: {len(files)}")
            logger.info(f"Successfully classified: {operation_stats.get('success', 0)}")
            logger.info("="*60)

            return result

        except Exception as e:
            logger.error(f"Workflow failed: {e}", exc_info=True)
            raise ClassifierError(f"Application execution failed: {e}")

    def _scan_files(self, source_dir: Path) -> List[FileInfo]:
        """
        Scan source directory for files.

        Args:
            source_dir: Source directory

        Returns:
            List of file information objects
        """
        # Read content for text files if configured
        perf_config = self.config['performance']['content_analysis']
        read_content = True
        max_content_length = perf_config.get('max_content_length', 5000)

        files = self.file_scanner.scan(
            source_dir,
            file_filter=self.file_filter,
            read_content=read_content,
            max_content_length=max_content_length
        )

        logger.info(f"Scanned {len(files)} files")
        return files

    def _classify_files(
        self,
        files: List[FileInfo]
    ) -> Dict[FileInfo, Optional[Classification]]:
        """
        Classify all files using optimized batch processing.

        Args:
            files: List of file information objects

        Returns:
            Dictionary mapping files to classifications
        """
        # Get batch processing configuration
        perf_config = self.config.get('performance', {})
        batch_config = perf_config.get('batch_processing', {})

        use_batch = batch_config.get('enabled', True)
        batch_size = batch_config.get('batch_size', perf_config.get('batch_size', 50))
        max_concurrent = self.config['api'].get('max_concurrent_requests', 5)

        if use_batch and len(files) > 1:
            logger.info(f"Using batch processing (batch_size={batch_size}, max_concurrent={max_concurrent})")
            return self._classify_files_batch(files, batch_size, max_concurrent)
        else:
            logger.info("Using serial processing")
            return self._classify_files_serial(files)

    def _classify_files_serial(
        self,
        files: List[FileInfo]
    ) -> Dict[FileInfo, Optional[Classification]]:
        """
        Classify files serially (legacy mode).

        Args:
            files: List of file information objects

        Returns:
            Dictionary mapping files to classifications
        """
        classification_map = {}

        for i, file_info in enumerate(files, 1):
            logger.info(f"Classifying [{i}/{len(files)}]: {file_info.name}")

            classification = self.strategy.classify(file_info)
            classification_map[file_info] = classification

            if classification is None:
                logger.warning(f"Failed to classify: {file_info.name}")

        classified = sum(1 for c in classification_map.values() if c is not None)
        logger.info(f"Successfully classified {classified}/{len(files)} files")

        return classification_map

    def _classify_files_batch(
        self,
        files: List[FileInfo],
        batch_size: int,
        max_concurrent: int
    ) -> Dict[FileInfo, Optional[Classification]]:
        """
        Classify files using concurrent batch processing.

        Args:
            files: List of file information objects
            batch_size: Maximum files per batch
            max_concurrent: Maximum concurrent API requests

        Returns:
            Dictionary mapping files to classifications
        """
        # Run async batch processing in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            classification_map = loop.run_until_complete(
                self._classify_files_batch_async(files, batch_size, max_concurrent)
            )
            return classification_map
        finally:
            loop.close()

    def _group_files_intelligently(
        self,
        files: List[FileInfo],
        strategy: str = 'extension'
    ) -> List[FileInfo]:
        """
        Group and sort files intelligently for better batch processing.

        Args:
            files: List of file information objects
            strategy: Grouping strategy ('extension', 'size', 'mixed')

        Returns:
            Reordered list of files
        """
        if strategy == 'extension':
            # Group by extension for better classification context
            return sorted(files, key=lambda f: (f.extension, f.size))
        elif strategy == 'size':
            # Group by size categories for memory management
            return sorted(files, key=lambda f: (f.size // 10000, f.extension))
        elif strategy == 'mixed':
            # Mixed strategy: extension first, then size
            return sorted(files, key=lambda f: (f.extension, f.size // 10000))
        else:
            return files

    async def _classify_files_batch_async(
        self,
        files: List[FileInfo],
        batch_size: int,
        max_concurrent: int
    ) -> Dict[FileInfo, Optional[Classification]]:
        """
        Asynchronously classify files in batches with controlled concurrency.

        Args:
            files: List of file information objects
            batch_size: Maximum files per batch
            max_concurrent: Maximum concurrent API requests

        Returns:
            Dictionary mapping files to classifications
        """
        classification_map = {}
        total_files = len(files)

        # Apply intelligent file grouping
        batch_config = self.config.get('performance', {}).get('batch_processing', {})
        grouping_strategy = batch_config.get('grouping_strategy', 'extension')

        if grouping_strategy != 'none':
            logger.info(f"Grouping files by strategy: {grouping_strategy}")
            files = self._group_files_intelligently(files, grouping_strategy)

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)

        async def classify_with_semaphore(file_info: FileInfo, index: int) -> tuple:
            """Classify a single file with semaphore-controlled concurrency."""
            async with semaphore:
                logger.info(f"Classifying [{index + 1}/{total_files}]: {file_info.name}")
                classification = await self.ai_classifier.classify_async(file_info)

                if classification is None:
                    logger.warning(f"Failed to classify: {file_info.name}")

                return (file_info, classification)

        # Process files in batches
        for batch_start in range(0, total_files, batch_size):
            batch_end = min(batch_start + batch_size, total_files)
            batch_files = files[batch_start:batch_end]

            logger.info(f"Processing batch {batch_start // batch_size + 1}: "
                       f"files {batch_start + 1}-{batch_end} of {total_files}")

            # Create tasks for this batch
            tasks = [
                classify_with_semaphore(file_info, batch_start + i)
                for i, file_info in enumerate(batch_files)
            ]

            # Execute batch concurrently with controlled concurrency
            batch_start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            batch_time = time.time() - batch_start_time

            # Process results
            batch_success = 0
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Batch classification error: {result}")
                elif isinstance(result, tuple):
                    file_info, classification = result
                    classification_map[file_info] = classification
                    if classification is not None:
                        batch_success += 1

            # Calculate batch performance metrics
            files_per_second = len(batch_files) / batch_time if batch_time > 0 else 0
            logger.info(f"Batch completed in {batch_time:.2f}s: "
                       f"{batch_success}/{len(batch_files)} successful "
                       f"({files_per_second:.1f} files/sec)")

        classified = sum(1 for c in classification_map.values() if c is not None)
        logger.info(f"Successfully classified {classified}/{total_files} files")

        return classification_map

    def _move_files(
        self,
        files: List[FileInfo],
        classification_map: Dict[FileInfo, Optional[Classification]],
        directory_manager: DirectoryManager,
        dry_run: bool
    ) -> Dict[str, int]:
        """
        Move files to classified directories.

        Args:
            files: List of file information objects
            classification_map: File to classification mapping
            directory_manager: Directory manager instance
            dry_run: Whether this is a dry run

        Returns:
            Operation statistics
        """
        file_mover = create_file_mover_from_config(self.config['operations'])

        operations = []
        for file_info in files:
            classification = classification_map.get(file_info)
            if classification:
                destination = directory_manager.get_destination_path(
                    file_info,
                    classification
                )
                operations.append((file_info.path, destination))

        if operations:
            stats = file_mover.move_batch(operations, dry_run=dry_run)
        else:
            stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

        return stats

    def _generate_reports(
        self,
        classification_map: Dict[FileInfo, Optional[Classification]],
        operation_stats: Dict[str, int],
        execution_time: float
    ) -> None:
        """
        Generate classification reports.

        Args:
            classification_map: File to classification mapping
            operation_stats: Operation statistics
            execution_time: Total execution time
        """
        try:
            summary = self.report_generator.generate_summary(
                classification_map,
                operation_stats,
                execution_time
            )

            # Export in configured formats
            formats = self.config['reporting'].get('formats', ['json'])

            if 'json' in formats:
                self.report_generator.export_json(summary)

            if 'csv' in formats:
                self.report_generator.export_csv(classification_map)

            if 'html' in formats:
                self.report_generator.export_html(summary, classification_map)

        except Exception as e:
            logger.error(f"Failed to generate reports: {e}")

    def _create_result(
        self,
        files: List[FileInfo],
        classification_map: Dict[FileInfo, Optional[Classification]],
        operation_stats: Dict[str, int],
        execution_time: float
    ) -> Dict[str, Any]:
        """
        Create result dictionary.

        Args:
            files: List of processed files
            classification_map: Classification results
            operation_stats: Operation statistics
            execution_time: Execution time

        Returns:
            Result dictionary
        """
        total = len(files)
        classified = sum(1 for c in classification_map.values() if c is not None)

        return {
            'success': True,
            'total_files': total,
            'classified': classified,
            'failed': total - classified,
            'operation_stats': operation_stats,
            'execution_time': execution_time,
            'cache_stats': self.cache_manager.get_stats() if self.cache_manager else None
        }
