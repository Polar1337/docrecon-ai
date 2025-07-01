#!/usr/bin/env python3
"""
DocRecon AI - Main CLI Application

AI-powered document analysis and consolidation tool for enterprise environments.
"""

import click
import logging
import sys
import os
from pathlib import Path
from typing import List, Optional

from .config import Config
from .crawler.main import DocumentCrawler
from .nlp.analyzer import NLPAnalyzer
from .detection.main import DuplicateDetector
from .reporting.main import ReportGenerator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0")
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), default='INFO', help='Logging level')
@click.option('--log-file', type=click.Path(), help='Log file path')
@click.pass_context
def cli(ctx, config, log_level, log_file):
    """DocRecon AI - Document Analysis and Consolidation Tool"""
    
    # Set up logging
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(file_handler)
    
    logging.getLogger().setLevel(getattr(logging, log_level))
    
    # Load configuration
    if config:
        config_path = Path(config)
    else:
        # Try default config locations
        config_path = Path('config/default.yaml')
        if not config_path.exists():
            config_path = Path('config/sharepoint_onprem.yaml')
    
    if config_path.exists():
        ctx.obj = Config(str(config_path))
        logger.info(f"Loaded configuration from {config_path}")
    else:
        ctx.obj = Config()
        logger.warning("No configuration file found, using defaults")


@cli.command()
@click.argument('paths', nargs=-1, type=click.Path())
@click.option('--output', '-o', required=True, type=click.Path(), help='Output directory for results')
@click.option('--include-nlp', is_flag=True, help='Enable NLP analysis (slower but more detailed)')
@click.option('--skip-similarity', is_flag=True, help='Skip similarity analysis (faster)')
@click.option('--max-files', type=int, help='Maximum number of files to analyze')
@click.option('--file-types', multiple=True, help='File extensions to include (e.g., .pdf .docx)')
@click.option('--sharepoint-site', help='Specific SharePoint site to crawl')
@click.option('--parallel-workers', type=int, help='Number of parallel workers')
@click.pass_context
def analyze(ctx, paths, output, include_nlp, skip_similarity, max_files, file_types, sharepoint_site, parallel_workers):
    """Analyze documents for duplicates and similarities."""
    
    config = ctx.obj
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Update config with command line options
        if max_files:
            config.set('crawler.max_files', max_files)
        if file_types:
            config.set('crawler.file_extensions', list(file_types))
        if parallel_workers:
            config.set('crawler.parallel_workers', parallel_workers)
        
        # Initialize crawler
        logger.info("Initializing document crawler...")
        crawler = DocumentCrawler(config)
        
        # Crawl documents
        if sharepoint_site:
            logger.info(f"Crawling SharePoint site: {sharepoint_site}")
            sharepoint_crawler = crawler.get_crawler('sharepoint_onprem')
            if sharepoint_crawler:
                documents = sharepoint_crawler.crawl_path(sharepoint_site)
            else:
                logger.error("SharePoint crawler not available")
                sys.exit(1)
        else:
            logger.info("Crawling all configured sources...")
            documents = crawler.crawl_all_sources(list(paths) if paths else None)
        
        logger.info(f"Found {len(documents)} documents")
        
        # NLP Analysis
        if include_nlp:
            logger.info("Performing NLP analysis...")
            nlp_analyzer = NLPAnalyzer(config)
            documents = nlp_analyzer.analyze_documents(documents)
        
        # Duplicate Detection
        if not skip_similarity:
            logger.info("Detecting duplicates and similarities...")
            detector = DuplicateDetector(config)
            duplicate_groups, similar_groups = detector.detect_duplicates(documents)
        else:
            duplicate_groups, similar_groups = [], []
        
        # Generate Reports
        logger.info("Generating reports...")
        report_generator = ReportGenerator(config)
        report_generator.generate_all_reports(
            documents=documents,
            duplicate_groups=duplicate_groups,
            similar_groups=similar_groups,
            output_dir=str(output_path)
        )
        
        # Save analysis results
        import json
        results = {
            'documents': [doc.to_dict() for doc in documents],
            'duplicate_groups': duplicate_groups,
            'similar_groups': similar_groups,
            'statistics': crawler.get_statistics()
        }
        
        with open(output_path / 'analysis_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Analysis complete! Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--config', type=click.Path(exists=True), help='Configuration file to validate')
@click.option('--verbose', is_flag=True, help='Show detailed validation results')
@click.pass_context
def validate_config(ctx, config, verbose):
    """Validate configuration file."""
    
    config_obj = ctx.obj
    if config:
        config_obj = Config(config)
    
    try:
        # Initialize crawler to validate configuration
        crawler = DocumentCrawler(config_obj)
        validation_results = crawler.validate_configurations()
        
        all_valid = True
        for crawler_name, result in validation_results.items():
            if result['valid']:
                click.echo(f"✅ {crawler_name}: Configuration valid")
            else:
                click.echo(f"❌ {crawler_name}: Configuration invalid")
                for error in result['errors']:
                    click.echo(f"   - {error}")
                all_valid = False
        
        if verbose:
            click.echo("\nDetailed configuration:")
            for key, value in config_obj.get_all().items():
                if 'password' not in key.lower():
                    click.echo(f"  {key}: {value}")
        
        if all_valid:
            click.echo("\n✅ All configurations are valid!")
        else:
            click.echo("\n❌ Some configurations have errors!")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Configuration validation failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--crawler', help='Test specific crawler (local, smb, sharepoint_onprem, onenote)')
@click.pass_context
def test_connection(ctx, crawler):
    """Test connections to configured sources."""
    
    config = ctx.obj
    
    try:
        document_crawler = DocumentCrawler(config)
        
        if crawler:
            # Test specific crawler
            crawler_instance = document_crawler.get_crawler(crawler)
            if not crawler_instance:
                click.echo(f"❌ Crawler '{crawler}' not found or not enabled")
                sys.exit(1)
            
            if hasattr(crawler_instance, 'test_connection'):
                result = crawler_instance.test_connection()
                if result:
                    click.echo(f"✅ {crawler}: Connection successful")
                else:
                    click.echo(f"❌ {crawler}: Connection failed")
                    sys.exit(1)
            else:
                click.echo(f"⚠️  {crawler}: No connection test available")
        else:
            # Test all crawlers
            results = document_crawler.test_connections()
            
            all_passed = True
            for crawler_name, result in results.items():
                if result:
                    click.echo(f"✅ {crawler_name}: Connection successful")
                else:
                    click.echo(f"❌ {crawler_name}: Connection failed")
                    all_passed = False
            
            if all_passed:
                click.echo("\n✅ All connection tests passed!")
            else:
                click.echo("\n❌ Some connection tests failed!")
                sys.exit(1)
                
    except Exception as e:
        click.echo(f"❌ Connection test failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument('results_file', type=click.Path(exists=True))
@click.option('--output', '-o', required=True, type=click.Path(), help='Output directory for reports')
@click.option('--formats', multiple=True, default=['html', 'csv'], help='Report formats (html, csv, json)')
@click.option('--title', help='Custom report title')
@click.pass_context
def report(ctx, results_file, output, formats, title):
    """Generate reports from analysis results."""
    
    config = ctx.obj
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load analysis results
        import json
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Generate reports
        report_generator = ReportGenerator(config)
        
        for format_type in formats:
            if format_type == 'html':
                report_generator.generate_html_report(
                    documents=results['documents'],
                    duplicate_groups=results.get('duplicate_groups', []),
                    similar_groups=results.get('similar_groups', []),
                    output_path=str(output_path / 'report.html'),
                    title=title
                )
            elif format_type == 'csv':
                report_generator.generate_csv_reports(
                    documents=results['documents'],
                    duplicate_groups=results.get('duplicate_groups', []),
                    output_dir=str(output_path)
                )
            elif format_type == 'json':
                report_generator.generate_json_report(
                    documents=results['documents'],
                    duplicate_groups=results.get('duplicate_groups', []),
                    similar_groups=results.get('similar_groups', []),
                    output_path=str(output_path / 'report.json')
                )
        
        logger.info(f"Reports generated in {output_path}")
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--results', type=click.Path(exists=True), help='Analysis results file')
@click.option('--port', type=int, default=8501, help='Port for dashboard')
@click.pass_context
def dashboard(ctx, results, port):
    """Start interactive dashboard."""
    
    try:
        import streamlit.web.cli as stcli
        import sys
        
        # Prepare streamlit arguments
        dashboard_script = Path(__file__).parent / 'dashboard' / 'main.py'
        
        args = [
            'streamlit', 'run', str(dashboard_script),
            '--server.port', str(port),
            '--server.headless', 'true'
        ]
        
        if results:
            args.extend(['--', '--results', results])
        
        # Run streamlit
        sys.argv = args
        stcli.main()
        
    except ImportError:
        click.echo("❌ Streamlit not installed. Install with: pip install streamlit")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Dashboard failed to start: {e}")
        sys.exit(1)


@cli.command()
@click.argument('results_file', type=click.Path(exists=True))
@click.option('--format', 'export_format', type=click.Choice(['csv', 'json']), required=True, help='Export format')
@click.option('--output', '-o', required=True, type=click.Path(), help='Output file path')
@click.option('--component', type=click.Choice(['documents', 'duplicates', 'recommendations']), help='Specific component to export')
@click.pass_context
def export(ctx, results_file, export_format, output, component):
    """Export analysis data in various formats."""
    
    try:
        # Load analysis results
        import json
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # Export data
        if export_format == 'csv':
            import pandas as pd
            
            if component == 'documents' or not component:
                df = pd.DataFrame(results['documents'])
                df.to_csv(output, index=False, encoding='utf-8')
            elif component == 'duplicates':
                # Flatten duplicate groups
                duplicate_data = []
                for group in results.get('duplicate_groups', []):
                    for doc in group.get('documents', []):
                        duplicate_data.append({
                            'group_id': group.get('group_id'),
                            'filename': doc.get('filename'),
                            'path': doc.get('path'),
                            'size': doc.get('size')
                        })
                df = pd.DataFrame(duplicate_data)
                df.to_csv(output, index=False, encoding='utf-8')
                
        elif export_format == 'json':
            export_data = results
            if component:
                export_data = {component: results.get(component, [])}
            
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
        
        click.echo(f"✅ Data exported to {output}")
        
    except Exception as e:
        click.echo(f"❌ Export failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()

