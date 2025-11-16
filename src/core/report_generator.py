"""Report generation for classification results."""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.file_info import FileInfo
from ..models.classification import Classification
from ..utils.logger import get_logger

logger = get_logger()


class ReportGenerator:
    """Generates reports and summaries of classification operations."""

    def __init__(self, output_dir: str = "reports"):
        """
        Initialize report generator.

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_summary(
        self,
        classification_map: Dict[FileInfo, Optional[Classification]],
        operation_stats: Dict[str, int],
        execution_time: float
    ) -> Dict[str, Any]:
        """
        Generate summary statistics.

        Args:
            classification_map: Mapping of files to classifications
            operation_stats: Statistics from file operations
            execution_time: Total execution time in seconds

        Returns:
            Summary dictionary
        """
        total_files = len(classification_map)
        classified = sum(1 for c in classification_map.values() if c is not None)
        failed = total_files - classified

        # Category statistics
        categories: Dict[str, int] = {}
        confidence_sum = 0.0

        for classification in classification_map.values():
            if classification:
                category = classification.primary_category
                categories[category] = categories.get(category, 0) + 1
                confidence_sum += classification.confidence

        avg_confidence = confidence_sum / classified if classified > 0 else 0.0

        summary = {
            'timestamp': datetime.now().isoformat(),
            'execution_time_seconds': round(execution_time, 2),
            'total_files': total_files,
            'classified': classified,
            'failed': failed,
            'success_rate': round((classified / total_files * 100), 2) if total_files > 0 else 0,
            'average_confidence': round(avg_confidence, 2),
            'categories': categories,
            'operation_stats': operation_stats
        }

        return summary

    def export_json(
        self,
        data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> Path:
        """
        Export data to JSON file.

        Args:
            data: Data to export
            filename: Output filename (auto-generated if None)

        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"classification_report_{timestamp}.json"

        output_path = self.output_dir / filename

        try:
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            logger.info(f"Exported JSON report to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            raise

    def export_csv(
        self,
        classification_map: Dict[FileInfo, Optional[Classification]],
        filename: Optional[str] = None
    ) -> Path:
        """
        Export classification results to CSV file.

        Args:
            classification_map: Mapping of files to classifications
            filename: Output filename (auto-generated if None)

        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"classification_results_{timestamp}.csv"

        output_path = self.output_dir / filename

        try:
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)

                # Write header
                writer.writerow([
                    'File Name',
                    'File Path',
                    'Size',
                    'Extension',
                    'Primary Category',
                    'Subcategory',
                    'Sub-subcategory',
                    'Full Path',
                    'Confidence',
                    'Strategy'
                ])

                # Write data
                for file_info, classification in classification_map.items():
                    if classification:
                        writer.writerow([
                            file_info.name,
                            str(file_info.path),
                            file_info.size_formatted,
                            file_info.extension,
                            classification.primary_category,
                            classification.subcategory or '',
                            classification.sub_subcategory or '',
                            classification.directory_path,
                            classification.confidence,
                            classification.strategy
                        ])
                    else:
                        writer.writerow([
                            file_info.name,
                            str(file_info.path),
                            file_info.size_formatted,
                            file_info.extension,
                            'FAILED',
                            '',
                            '',
                            '',
                            0.0,
                            ''
                        ])

            logger.info(f"Exported CSV report to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise

    def export_html(
        self,
        summary: Dict[str, Any],
        classification_map: Dict[FileInfo, Optional[Classification]],
        filename: Optional[str] = None
    ) -> Path:
        """
        Export report as HTML file.

        Args:
            summary: Summary statistics
            classification_map: Mapping of files to classifications
            filename: Output filename (auto-generated if None)

        Returns:
            Path to exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"classification_report_{timestamp}.html"

        output_path = self.output_dir / filename

        # Generate simple HTML report
        html = self._generate_html_report(summary, classification_map)

        try:
            with open(output_path, 'w') as f:
                f.write(html)

            logger.info(f"Exported HTML report to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to export HTML: {e}")
            raise

    def _generate_html_report(
        self,
        summary: Dict[str, Any],
        classification_map: Dict[FileInfo, Optional[Classification]]
    ) -> str:
        """Generate HTML report content."""

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>AI File Classifier Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; margin-top: 30px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
        .stat {{ margin: 10px 0; }}
        .stat-label {{ font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .failed {{ color: #d32f2f; }}
        .success {{ color: #388e3c; }}
    </style>
</head>
<body>
    <h1>AI File Classifier Report</h1>

    <div class="summary">
        <h2>Summary</h2>
        <div class="stat"><span class="stat-label">Timestamp:</span> {summary['timestamp']}</div>
        <div class="stat"><span class="stat-label">Execution Time:</span> {summary['execution_time_seconds']} seconds</div>
        <div class="stat"><span class="stat-label">Total Files:</span> {summary['total_files']}</div>
        <div class="stat"><span class="stat-label">Successfully Classified:</span> <span class="success">{summary['classified']}</span></div>
        <div class="stat"><span class="stat-label">Failed:</span> <span class="failed">{summary['failed']}</span></div>
        <div class="stat"><span class="stat-label">Success Rate:</span> {summary['success_rate']}%</div>
        <div class="stat"><span class="stat-label">Average Confidence:</span> {summary['average_confidence']}</div>
    </div>

    <h2>Categories Distribution</h2>
    <table>
        <tr>
            <th>Category</th>
            <th>File Count</th>
        </tr>
"""

        for category, count in sorted(summary['categories'].items()):
            html += f"        <tr><td>{category}</td><td>{count}</td></tr>\n"

        html += """    </table>

    <h2>Classification Details</h2>
    <table>
        <tr>
            <th>File Name</th>
            <th>Extension</th>
            <th>Size</th>
            <th>Classification Path</th>
            <th>Confidence</th>
        </tr>
"""

        for file_info, classification in classification_map.items():
            if classification:
                html += f"""        <tr>
            <td>{file_info.name}</td>
            <td>{file_info.extension}</td>
            <td>{file_info.size_formatted}</td>
            <td>{classification.directory_path}</td>
            <td>{classification.confidence:.2f}</td>
        </tr>
"""
            else:
                html += f"""        <tr class="failed">
            <td>{file_info.name}</td>
            <td>{file_info.extension}</td>
            <td>{file_info.size_formatted}</td>
            <td>FAILED</td>
            <td>-</td>
        </tr>
"""

        html += """    </table>
</body>
</html>"""

        return html
