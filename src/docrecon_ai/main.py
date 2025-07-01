#!/usr/bin/env python3
"""
DocRecon AI - Main CLI Application

Command-line interface for the DocRecon AI document consolidation tool.
"""

import argparse
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import time

from .config import DocReconConfig
from .crawler.main import DocumentCrawler
from .nlp.analyzer import NLPAnalyzer
from .detection.main import DuplicateDetector
from .reporting.main import ReportGenerator


def setup_logging(log_level: str = 'INFO', log_file: Optional[str] = None):
    """Setup logging configuration"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Setup file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description='DocRecon AI - Document Consolidation Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze local directory
  docrecon_ai analyze /path/to/documents --output ./results

  # Analyze with custom config
  docrecon_ai analyze /path/to/documents --config config.yaml

  # Generate dashboard
  docrecon_ai dashboard --results ./results/analysis.json

  # Export specific format
  docrecon_ai export ./results/analysis.json --format csv --output ./exports
        """
    )
    
    # Global options
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        help='Log file path'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze documents for duplicates and consolidation opportunities'
    )
    analyze_parser.add_argument(
        'paths',
        nargs='+',
        help='Paths to analyze (directories or files)'
    )
    analyze_parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Output directory for results'
    )
    analyze_parser.add_argument(
        '--include-nlp',
        action='store_true',
        help='Include NLP analysis (slower but more insights)'
    )
    analyze_parser.add_argument(
        '--skip-similarity',
        action='store_true',
        help='Skip similarity analysis (faster)'
    )
    analyze_parser.add_argument(
        '--max-files',
        type=int,
        help='Maximum number of files to analyze'
    )
    analyze_parser.add_argument(
        '--file-types',
        nargs='+',
        help='File extensions to include (e.g., .pdf .docx)'
    )
    
    # Report command
    report_parser = subparsers.add_parser(
        'report',
        help='Generate reports from analysis results'
    )
    report_parser.add_argument(
        'results',
        type=str,
        help='Path to analysis results JSON file'
    )
    report_parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Output directory for reports'
    )
    report_parser.add_argument(
        '--formats',
        nargs='+',
        choices=['html', 'csv', 'json'],
        default=['html', 'csv'],
        help='Report formats to generate'
    )
    report_parser.add_argument(
        '--title',
        type=str,
        help='Custom report title'
    )
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser(
        'dashboard',
        help='Launch interactive dashboard'
    )
    dashboard_parser.add_argument(
        '--results',
        type=str,
        help='Path to analysis results JSON file'
    )
    dashboard_parser.add_argument(
        '--port',
        type=int,
        default=8501,
        help='Port for dashboard (default: 8501)'
    )
    
    # Export command
    export_parser = subparsers.add_parser(
        'export',
        help='Export analysis results in specific format'
    )
    export_parser.add_argument(
        'results',
        type=str,
        help='Path to analysis results JSON file'
    )
    export_parser.add_argument(
        '--format',
        choices=['csv', 'json', 'html'],
        required=True,
        help='Export format'
    )
    export_parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Output path'
    )
    export_parser.add_argument(
        '--component',
        choices=['documents', 'duplicates', 'recommendations', 'all'],
        default='all',
        help='Component to export'
    )
    
    return parser


def load_analysis_results(results_path: str) -> Dict[str, Any]:
    """Load analysis results from JSON file"""
    try:
        with open(results_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading analysis results from {results_path}: {e}")
        sys.exit(1)


def save_analysis_results(results: Dict[str, Any], output_path: str):
    """Save analysis results to JSON file"""
    try:
        os.makedirs(Path(output_path).parent, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        logging.info(f"Analysis results saved to {output_path}")
    except Exception as e:
        logging.error(f"Error saving analysis results to {output_path}: {e}")
        sys.exit(1)


def cmd_analyze(args, config: DocReconConfig) -> int:
    """Execute analyze command"""
    logging.info("Starting document analysis...")
    start_time = time.time()
    
    try:
        # Initialize components
        crawler = DocumentCrawler(config)
        duplicate_detector = DuplicateDetector(config)
        
        # Optional NLP analyzer
        nlp_analyzer = None
        if args.include_nlp:
            nlp_analyzer = NLPAnalyzer(config)
        
        # Crawl documents
        logging.info(f"Crawling documents from {len(args.paths)} path(s)...")
        documents = []
        
        for path in args.paths:
            if not os.path.exists(path):
                logging.warning(f"Path does not exist: {path}")
                continue
            
            path_documents = crawler.crawl_path(path)
            documents.extend(path_documents)
            
            if args.max_files and len(documents) >= args.max_files:
                documents = documents[:args.max_files]
                break
        
        if not documents:
            logging.error("No documents found to analyze")
            return 1
        
        logging.info(f"Found {len(documents)} documents")
        
        # Filter by file types if specified
        if args.file_types:
            extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                         for ext in args.file_types]
            documents = [doc for doc in documents if doc.file_extension.lower() in extensions]
            logging.info(f"Filtered to {len(documents)} documents by file type")
        
        # Detect duplicates
        logging.info("Detecting duplicates...")
        duplicate_results = duplicate_detector.detect_all_duplicates(documents)
        
        # NLP analysis
        nlp_results = {}
        if nlp_analyzer and not args.skip_similarity:
            logging.info("Performing NLP analysis...")
            nlp_results = nlp_analyzer.analyze_documents(documents)
        
        # Generate recommendations
        logging.info("Generating recommendations...")
        recommendations = duplicate_detector.generate_recommendations(
            duplicate_results, documents
        )
        
        # Compile results
        analysis_results = {
            'metadata': {
                'analysis_timestamp': time.time(),
                'analysis_duration': time.time() - start_time,
                'tool_version': '1.0.0',
                'analyzed_paths': args.paths,
                'total_documents': len(documents),
            },
            'statistics': {
                'total_documents': len(documents),
                'processing_time': time.time() - start_time,
                'paths_analyzed': len(args.paths),
            },
            'documents': [doc.__dict__ for doc in documents],
            **duplicate_results,
            **nlp_results,
            'recommendations': recommendations,
        }
        
        # Save results
        output_file = os.path.join(args.output, 'analysis_results.json')
        save_analysis_results(analysis_results, output_file)
        
        # Generate basic report
        report_generator = ReportGenerator(config)
        report_results = report_generator.generate_comprehensive_report(
            analysis_results,
            args.output,
            formats=['html'],
            report_title="DocRecon AI - Analysis Report"
        )
        
        # Summary
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✅ Analysis completed in {duration:.2f} seconds")
        print(f"📊 Analyzed {len(documents)} documents")
        print(f"🔍 Found {len(duplicate_results.get('hash_duplicates', {}).get('duplicate_groups', []))} exact duplicate groups")
        print(f"📁 Results saved to: {args.output}")
        
        if report_results.get('files_created', {}).get('html'):
            print(f"📄 HTML report: {report_results['files_created']['html']}")
        
        return 0
        
    except Exception as e:
        logging.error(f"Error during analysis: {e}")
        return 1


def cmd_report(args, config: DocReconConfig) -> int:
    """Execute report command"""
    logging.info("Generating reports...")
    
    try:
        # Load analysis results
        analysis_results = load_analysis_results(args.results)
        
        # Generate reports
        report_generator = ReportGenerator(config)
        report_results = report_generator.generate_comprehensive_report(
            analysis_results,
            args.output,
            formats=args.formats,
            report_title=args.title
        )
        
        # Summary
        print(f"\n✅ Reports generated successfully")
        print(f"📁 Output directory: {args.output}")
        
        for format_name, file_path in report_results.get('files_created', {}).items():
            print(f"📄 {format_name.upper()}: {file_path}")
        
        return 0
        
    except Exception as e:
        logging.error(f"Error generating reports: {e}")
        return 1


def cmd_dashboard(args, config: DocReconConfig) -> int:
    """Execute dashboard command"""
    try:
        from .dashboard.main import run_dashboard
        
        analysis_results = None
        if args.results:
            analysis_results = load_analysis_results(args.results)
        
        print(f"🚀 Starting dashboard on port {args.port}")
        print(f"🌐 Open your browser to: http://localhost:{args.port}")
        
        run_dashboard(analysis_results, args.port)
        return 0
        
    except ImportError:
        logging.error("Dashboard requires Streamlit. Install: pip install streamlit")
        return 1
    except Exception as e:
        logging.error(f"Error starting dashboard: {e}")
        return 1


def cmd_export(args, config: DocReconConfig) -> int:
    """Execute export command"""
    logging.info("Exporting analysis results...")
    
    try:
        # Load analysis results
        analysis_results = load_analysis_results(args.results)
        
        # Initialize appropriate exporter
        if args.format == 'csv':
            from .reporting.csv_exporter import CSVExporter
            exporter = CSVExporter(config)
            
            if args.component == 'all':
                success = exporter.export_all_results(analysis_results, args.output)
            elif args.component == 'documents':
                success = exporter.export_document_inventory(
                    analysis_results.get('documents', []), args.output
                )
            # Add other components as needed
            
        elif args.format == 'json':
            from .reporting.json_exporter import JSONExporter
            exporter = JSONExporter(config)
            success = exporter.export_complete_results(analysis_results, args.output)
            
        elif args.format == 'html':
            from .reporting.html_reporter import HTMLReporter
            reporter = HTMLReporter(config)
            success = reporter.generate_comprehensive_report(analysis_results, args.output)
        
        if success:
            print(f"✅ Export completed: {args.output}")
            return 0
        else:
            print("❌ Export failed")
            return 1
            
    except Exception as e:
        logging.error(f"Error during export: {e}")
        return 1


def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else args.log_level
    setup_logging(log_level, args.log_file)
    
    # Load configuration
    try:
        config = DocReconConfig(args.config)
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        return 1
    
    # Execute command
    if args.command == 'analyze':
        return cmd_analyze(args, config)
    elif args.command == 'report':
        return cmd_report(args, config)
    elif args.command == 'dashboard':
        return cmd_dashboard(args, config)
    elif args.command == 'export':
        return cmd_export(args, config)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())

