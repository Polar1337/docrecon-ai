"""
Main report generator that coordinates all reporting formats

Provides a unified interface for generating reports in multiple formats:
- CSV exports for data analysis
- HTML reports for human consumption
- JSON exports for programmatic access
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .csv_exporter import CSVExporter
from .html_reporter import HTMLReporter
from .json_exporter import JSONExporter

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Main report generator that coordinates all reporting formats.
    
    Provides a unified interface for generating comprehensive reports
    from DocRecon AI analysis results in multiple formats.
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize report generator.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize exporters
        self.csv_exporter = CSVExporter(config)
        self.html_reporter = HTMLReporter(config)
        self.json_exporter = JSONExporter(config)
        
        # Report settings
        self.default_formats = ['html', 'csv', 'json']
        self.include_timestamp = True
        
        # Statistics
        self.reports_generated = 0
        self.total_export_time = 0
    
    def generate_comprehensive_report(self, analysis_results: Dict[str, Any], 
                                    output_dir: str, 
                                    formats: List[str] = None,
                                    report_title: str = None) -> Dict[str, Any]:
        """
        Generate comprehensive reports in multiple formats.
        
        Args:
            analysis_results: Complete analysis results from DocRecon AI
            output_dir: Directory to save all report files
            formats: List of formats to generate ('html', 'csv', 'json')
            report_title: Custom title for the report
            
        Returns:
            dict: Generation status and file paths for each format
        """
        start_time = datetime.now()
        
        if formats is None:
            formats = self.default_formats
        
        if report_title is None:
            report_title = "DocRecon AI - Document Analysis Report"
        
        self.logger.info(f"Generating comprehensive report in formats: {', '.join(formats)}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Add timestamp to directory name if enabled
        if self.include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(output_dir, f"docrecon_report_{timestamp}")
            os.makedirs(output_dir, exist_ok=True)
        
        results = {
            'output_directory': output_dir,
            'formats_generated': [],
            'files_created': {},
            'generation_status': {},
            'summary': {},
        }
        
        # Generate HTML report
        if 'html' in formats:
            html_path = os.path.join(output_dir, 'report.html')
            success = self.html_reporter.generate_comprehensive_report(
                analysis_results, html_path, report_title
            )
            results['generation_status']['html'] = success
            if success:
                results['files_created']['html'] = html_path
                results['formats_generated'].append('html')
        
        # Generate CSV exports
        if 'csv' in formats:
            csv_dir = os.path.join(output_dir, 'csv_exports')
            csv_status = self.csv_exporter.export_all_results(analysis_results, csv_dir)
            results['generation_status']['csv'] = csv_status
            if any(csv_status.values()):
                results['files_created']['csv'] = csv_dir
                results['formats_generated'].append('csv')
        
        # Generate JSON exports
        if 'json' in formats:
            json_dir = os.path.join(output_dir, 'json_exports')
            json_status = self.json_exporter.export_all_formats(analysis_results, json_dir)
            results['generation_status']['json'] = json_status
            if any(json_status.values()):
                results['files_created']['json'] = json_dir
                results['formats_generated'].append('json')
        
        # Generate summary
        end_time = datetime.now()
        generation_time = (end_time - start_time).total_seconds()
        
        results['summary'] = {
            'report_title': report_title,
            'generation_time_seconds': generation_time,
            'total_formats': len(formats),
            'successful_formats': len(results['formats_generated']),
            'output_directory': output_dir,
            'main_report_file': results['files_created'].get('html', ''),
        }
        
        # Update statistics
        self.reports_generated += 1
        self.total_export_time += generation_time
        
        self.logger.info(f"Report generation completed in {generation_time:.2f} seconds")
        self.logger.info(f"Generated {len(results['formats_generated'])} formats: {', '.join(results['formats_generated'])}")
        
        return results
    
    def generate_executive_summary(self, analysis_results: Dict[str, Any], 
                                 output_path: str) -> bool:
        """
        Generate a concise executive summary report.
        
        Args:
            analysis_results: Analysis results
            output_path: Path to output HTML file
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Generating executive summary: {output_path}")
            
            # Create simplified results for executive summary
            summary_data = self._create_executive_summary_data(analysis_results)
            
            # Generate HTML report with executive focus
            success = self.html_reporter.generate_comprehensive_report(
                summary_data, 
                output_path, 
                "DocRecon AI - Executive Summary"
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error generating executive summary: {e}")
            return False
    
    def generate_technical_report(self, analysis_results: Dict[str, Any], 
                                output_dir: str) -> Dict[str, Any]:
        """
        Generate detailed technical report with all data.
        
        Args:
            analysis_results: Complete analysis results
            output_dir: Directory to save technical report files
            
        Returns:
            dict: Generation results
        """
        self.logger.info(f"Generating technical report: {output_dir}")
        
        # Generate all formats with detailed data
        return self.generate_comprehensive_report(
            analysis_results,
            output_dir,
            formats=['html', 'csv', 'json'],
            report_title="DocRecon AI - Technical Analysis Report"
        )
    
    def generate_recommendations_report(self, analysis_results: Dict[str, Any], 
                                      output_path: str) -> bool:
        """
        Generate a focused recommendations report.
        
        Args:
            analysis_results: Analysis results
            output_path: Path to output file
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Generating recommendations report: {output_path}")
            
            # Extract recommendations data
            recommendations = analysis_results.get('recommendations', {})
            
            # Determine output format based on file extension
            file_ext = Path(output_path).suffix.lower()
            
            if file_ext == '.html':
                # Create HTML recommendations report
                rec_data = {'recommendations': recommendations}
                success = self.html_reporter.generate_comprehensive_report(
                    rec_data,
                    output_path,
                    "DocRecon AI - Recommendations Report"
                )
            elif file_ext == '.csv':
                # Create CSV recommendations export
                success = self.csv_exporter.export_recommendations(recommendations, output_path)
            elif file_ext == '.json':
                # Create JSON recommendations export
                success = self.json_exporter.export_recommendations(recommendations, output_path)
            else:
                # Default to HTML
                success = self.html_reporter.generate_comprehensive_report(
                    {'recommendations': recommendations},
                    output_path,
                    "DocRecon AI - Recommendations Report"
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations report: {e}")
            return False
    
    def _create_executive_summary_data(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create simplified data for executive summary"""
        summary_data = {
            'statistics': analysis_results.get('statistics', {}),
            'recommendations': {
                'summary': analysis_results.get('recommendations', {}).get('summary', {}),
                'high_priority': analysis_results.get('recommendations', {}).get('high_priority', [])[:5],  # Top 5 only
            }
        }
        
        # Add simplified duplicate information
        if 'hash_duplicates' in analysis_results:
            hash_stats = analysis_results['hash_duplicates'].get('statistics', {})
            summary_data['duplicate_summary'] = {
                'exact_duplicates': hash_stats.get('duplicate_groups_found', 0),
                'wasted_space_mb': hash_stats.get('total_wasted_space_mb', 0),
            }
        
        return summary_data
    
    def create_report_index(self, output_dir: str, report_info: Dict[str, Any]) -> bool:
        """
        Create an index file linking to all generated reports.
        
        Args:
            output_dir: Directory containing reports
            report_info: Information about generated reports
            
        Returns:
            bool: Success status
        """
        try:
            index_path = os.path.join(output_dir, 'index.html')
            
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocRecon AI - Report Index</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        .report-section {{ margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 5px; }}
        .report-link {{ display: inline-block; margin: 10px 10px 10px 0; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }}
        .report-link:hover {{ background: #2980b9; }}
        .info {{ color: #666; margin: 10px 0; }}
        .timestamp {{ color: #888; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 DocRecon AI - Report Index</h1>
        
        <div class="info">
            <p><strong>Report Title:</strong> {report_info.get('summary', {}).get('report_title', 'Document Analysis Report')}</p>
            <p><strong>Generated:</strong> <span class="timestamp">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</span></p>
            <p><strong>Generation Time:</strong> {report_info.get('summary', {}).get('generation_time_seconds', 0):.2f} seconds</p>
        </div>
        
        <div class="report-section">
            <h2>📄 Main Reports</h2>
"""
            
            # Add links to main reports
            files_created = report_info.get('files_created', {})
            
            if 'html' in files_created:
                html_content += f'<a href="{os.path.relpath(files_created["html"], output_dir)}" class="report-link">📊 HTML Report</a>'
            
            html_content += """
        </div>
        
        <div class="report-section">
            <h2>📁 Data Exports</h2>
"""
            
            if 'csv' in files_created:
                html_content += f'<a href="{os.path.relpath(files_created["csv"], output_dir)}" class="report-link">📈 CSV Data</a>'
            
            if 'json' in files_created:
                html_content += f'<a href="{os.path.relpath(files_created["json"], output_dir)}" class="report-link">🔧 JSON Data</a>'
            
            html_content += """
        </div>
        
        <div class="report-section">
            <h2>ℹ️ About This Report</h2>
            <p>This report was generated by DocRecon AI, a comprehensive document analysis and consolidation tool.</p>
            <p>The analysis includes duplicate detection, content similarity analysis, and actionable recommendations for document management.</p>
        </div>
    </div>
</body>
</html>
"""
            
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Created report index: {index_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating report index: {e}")
            return False
    
    def get_report_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive reporting statistics.
        
        Returns:
            dict: Statistics from all reporting components
        """
        return {
            'reports_generated': self.reports_generated,
            'total_export_time': self.total_export_time,
            'avg_export_time': self.total_export_time / self.reports_generated if self.reports_generated > 0 else 0,
            'csv_exporter': self.csv_exporter.get_statistics(),
            'html_reporter': self.html_reporter.get_statistics(),
            'json_exporter': self.json_exporter.get_statistics(),
        }
    
    def reset_statistics(self):
        """Reset all reporting statistics"""
        self.reports_generated = 0
        self.total_export_time = 0
        
        self.csv_exporter.reset_statistics()
        self.html_reporter.reset_statistics()
        self.json_exporter.reset_statistics()
    
    def validate_analysis_results(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate analysis results before report generation.
        
        Args:
            analysis_results: Analysis results to validate
            
        Returns:
            dict: Validation results with warnings and errors
        """
        validation = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'missing_components': [],
        }
        
        # Check for required components
        required_components = ['statistics']
        optional_components = ['hash_duplicates', 'similarity_duplicates', 'version_groups', 'recommendations', 'entities', 'keywords']
        
        for component in required_components:
            if component not in analysis_results:
                validation['errors'].append(f"Missing required component: {component}")
                validation['valid'] = False
        
        for component in optional_components:
            if component not in analysis_results:
                validation['missing_components'].append(component)
                validation['warnings'].append(f"Optional component missing: {component}")
        
        # Check data quality
        stats = analysis_results.get('statistics', {})
        if stats.get('total_documents', 0) == 0:
            validation['warnings'].append("No documents found in analysis results")
        
        # Check for empty results
        if 'hash_duplicates' in analysis_results:
            hash_groups = analysis_results['hash_duplicates'].get('duplicate_groups', [])
            if len(hash_groups) == 0:
                validation['warnings'].append("No hash duplicates found")
        
        return validation

