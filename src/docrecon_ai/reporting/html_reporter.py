"""
HTML report generation for DocRecon AI results

Creates comprehensive HTML reports with interactive elements, charts,
and detailed analysis summaries for human consumption.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HTMLReporter:
    """
    Generates comprehensive HTML reports for DocRecon AI analysis results.
    
    Creates interactive, visually appealing reports with:
    - Executive summary
    - Detailed analysis sections
    - Interactive charts and tables
    - Actionable recommendations
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize HTML reporter.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Report settings
        self.include_charts = True
        self.include_details = True
        self.theme = 'modern'
        
        # Statistics
        self.reports_generated = 0
    
    def generate_comprehensive_report(self, analysis_results: Dict[str, Any], 
                                    output_path: str, title: str = None) -> bool:
        """
        Generate a comprehensive HTML report.
        
        Args:
            analysis_results: Complete analysis results
            output_path: Path to output HTML file
            title: Report title
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info(f"Generating comprehensive HTML report: {output_path}")
            
            if title is None:
                title = "DocRecon AI - Document Analysis Report"
            
            # Create output directory if needed
            os.makedirs(Path(output_path).parent, exist_ok=True)
            
            # Generate HTML content
            html_content = self._generate_html_report(analysis_results, title)
            
            # Write HTML file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.reports_generated += 1
            self.logger.info(f"Successfully generated HTML report: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating HTML report: {e}")
            return False
    
    def _generate_html_report(self, results: Dict[str, Any], title: str) -> str:
        """Generate complete HTML report content"""
        
        # Extract key metrics
        stats = results.get('statistics', {})
        recommendations = results.get('recommendations', {})
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {self._get_css_styles()}
    {self._get_javascript()}
</head>
<body>
    <div class="container">
        {self._generate_header(title)}
        {self._generate_executive_summary(results)}
        {self._generate_document_overview(results)}
        {self._generate_duplicate_analysis(results)}
        {self._generate_nlp_analysis(results)}
        {self._generate_recommendations(results)}
        {self._generate_detailed_tables(results)}
        {self._generate_footer()}
    </div>
</body>
</html>
"""
        return html
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for the report"""
        return """
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        color: #333;
        background-color: #f5f5f5;
    }
    
    .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
        background-color: white;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    
    .header {
        text-align: center;
        padding: 30px 0;
        border-bottom: 3px solid #2c3e50;
        margin-bottom: 30px;
    }
    
    .header h1 {
        color: #2c3e50;
        font-size: 2.5em;
        margin-bottom: 10px;
    }
    
    .header .subtitle {
        color: #7f8c8d;
        font-size: 1.2em;
    }
    
    .section {
        margin-bottom: 40px;
        padding: 20px;
        border-radius: 8px;
        background-color: #fff;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .section h2 {
        color: #2c3e50;
        font-size: 1.8em;
        margin-bottom: 20px;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
    }
    
    .section h3 {
        color: #34495e;
        font-size: 1.4em;
        margin-bottom: 15px;
        margin-top: 25px;
    }
    
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-bottom: 30px;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #3498db, #2980b9);
        color: white;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .metric-card.warning {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
    }
    
    .metric-card.success {
        background: linear-gradient(135deg, #27ae60, #229954);
    }
    
    .metric-card.info {
        background: linear-gradient(135deg, #f39c12, #e67e22);
    }
    
    .metric-value {
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 5px;
    }
    
    .metric-label {
        font-size: 1.1em;
        opacity: 0.9;
    }
    
    .table-container {
        overflow-x: auto;
        margin: 20px 0;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        background-color: white;
    }
    
    th, td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }
    
    th {
        background-color: #34495e;
        color: white;
        font-weight: bold;
    }
    
    tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    tr:hover {
        background-color: #e8f4f8;
    }
    
    .priority-high {
        background-color: #ffebee !important;
        border-left: 4px solid #e74c3c;
    }
    
    .priority-medium {
        background-color: #fff3e0 !important;
        border-left: 4px solid #f39c12;
    }
    
    .priority-low {
        background-color: #e8f5e8 !important;
        border-left: 4px solid #27ae60;
    }
    
    .chart-container {
        margin: 30px 0;
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 8px;
    }
    
    .progress-bar {
        width: 100%;
        height: 20px;
        background-color: #ecf0f1;
        border-radius: 10px;
        overflow: hidden;
        margin: 10px 0;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #3498db, #2980b9);
        transition: width 0.3s ease;
    }
    
    .alert {
        padding: 15px;
        margin: 20px 0;
        border-radius: 5px;
        border-left: 4px solid;
    }
    
    .alert-info {
        background-color: #d1ecf1;
        border-color: #17a2b8;
        color: #0c5460;
    }
    
    .alert-warning {
        background-color: #fff3cd;
        border-color: #ffc107;
        color: #856404;
    }
    
    .alert-danger {
        background-color: #f8d7da;
        border-color: #dc3545;
        color: #721c24;
    }
    
    .footer {
        text-align: center;
        padding: 30px 0;
        border-top: 1px solid #ddd;
        color: #7f8c8d;
        margin-top: 50px;
    }
    
    .collapsible {
        cursor: pointer;
        padding: 10px;
        background-color: #f1f1f1;
        border: none;
        text-align: left;
        outline: none;
        font-size: 15px;
        border-radius: 5px;
        margin: 5px 0;
        width: 100%;
    }
    
    .collapsible:hover {
        background-color: #ddd;
    }
    
    .collapsible-content {
        padding: 0 18px;
        display: none;
        overflow: hidden;
        background-color: #f9f9f9;
        border-radius: 0 0 5px 5px;
    }
    
    .tag {
        display: inline-block;
        padding: 4px 8px;
        margin: 2px;
        background-color: #3498db;
        color: white;
        border-radius: 12px;
        font-size: 0.8em;
    }
    
    .file-path {
        font-family: 'Courier New', monospace;
        background-color: #f4f4f4;
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 0.9em;
    }
    
    @media (max-width: 768px) {
        .container {
            padding: 10px;
        }
        
        .metric-grid {
            grid-template-columns: 1fr;
        }
        
        .header h1 {
            font-size: 2em;
        }
        
        table {
            font-size: 0.9em;
        }
    }
</style>
"""
    
    def _get_javascript(self) -> str:
        """Get JavaScript for interactive elements"""
        return """
<script>
    document.addEventListener('DOMContentLoaded', function() {
        // Make collapsible sections work
        var collapsibles = document.getElementsByClassName('collapsible');
        for (var i = 0; i < collapsibles.length; i++) {
            collapsibles[i].addEventListener('click', function() {
                this.classList.toggle('active');
                var content = this.nextElementSibling;
                if (content.style.display === 'block') {
                    content.style.display = 'none';
                } else {
                    content.style.display = 'block';
                }
            });
        }
        
        // Animate progress bars
        var progressBars = document.getElementsByClassName('progress-fill');
        for (var i = 0; i < progressBars.length; i++) {
            var bar = progressBars[i];
            var width = bar.getAttribute('data-width');
            setTimeout(function(b, w) {
                return function() {
                    b.style.width = w + '%';
                };
            }(bar, width), 500);
        }
        
        // Add sorting to tables
        addTableSorting();
    });
    
    function addTableSorting() {
        var tables = document.getElementsByTagName('table');
        for (var i = 0; i < tables.length; i++) {
            var table = tables[i];
            var headers = table.getElementsByTagName('th');
            for (var j = 0; j < headers.length; j++) {
                headers[j].style.cursor = 'pointer';
                headers[j].onclick = function() {
                    sortTable(this);
                };
            }
        }
    }
    
    function sortTable(header) {
        var table = header.closest('table');
        var tbody = table.getElementsByTagName('tbody')[0];
        var rows = Array.from(tbody.getElementsByTagName('tr'));
        var columnIndex = Array.from(header.parentNode.children).indexOf(header);
        var isNumeric = true;
        
        // Check if column contains numeric data
        for (var i = 0; i < Math.min(5, rows.length); i++) {
            var cellText = rows[i].cells[columnIndex].textContent.trim();
            if (cellText && isNaN(parseFloat(cellText))) {
                isNumeric = false;
                break;
            }
        }
        
        rows.sort(function(a, b) {
            var aText = a.cells[columnIndex].textContent.trim();
            var bText = b.cells[columnIndex].textContent.trim();
            
            if (isNumeric) {
                return parseFloat(aText) - parseFloat(bText);
            } else {
                return aText.localeCompare(bText);
            }
        });
        
        // Re-append sorted rows
        for (var i = 0; i < rows.length; i++) {
            tbody.appendChild(rows[i]);
        }
    }
    
    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        var k = 1024;
        var sizes = ['Bytes', 'KB', 'MB', 'GB'];
        var i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
</script>
"""
    
    def _generate_header(self, title: str) -> str:
        """Generate report header"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
<div class="header">
    <h1>{title}</h1>
    <div class="subtitle">Generated on {timestamp}</div>
</div>
"""
    
    def _generate_executive_summary(self, results: Dict[str, Any]) -> str:
        """Generate executive summary section"""
        stats = results.get('statistics', {})
        recommendations = results.get('recommendations', {})
        
        # Extract key metrics
        total_docs = stats.get('total_documents', 0)
        duplicate_groups = 0
        total_duplicates = 0
        space_wasted = 0
        
        # Count duplicates from different sources
        if 'hash_duplicates' in results:
            hash_stats = results['hash_duplicates'].get('statistics', {})
            duplicate_groups += hash_stats.get('duplicate_groups_found', 0)
            total_duplicates += hash_stats.get('total_duplicates', 0)
            space_wasted += hash_stats.get('total_wasted_space_mb', 0)
        
        if 'similarity_duplicates' in results:
            sim_stats = results['similarity_duplicates'].get('statistics', {})
            duplicate_groups += sim_stats.get('similarity_groups_found', 0)
        
        if 'version_groups' in results:
            ver_stats = results['version_groups'].get('statistics', {})
            duplicate_groups += ver_stats.get('version_groups_found', 0)
        
        # Recommendations summary
        rec_summary = recommendations.get('summary', {})
        total_recommendations = rec_summary.get('total_recommendations', 0)
        high_priority = rec_summary.get('high_priority_count', 0)
        potential_savings = rec_summary.get('total_space_saved_mb', 0)
        
        return f"""
<div class="section">
    <h2>📊 Executive Summary</h2>
    
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-value">{total_docs:,}</div>
            <div class="metric-label">Documents Analyzed</div>
        </div>
        
        <div class="metric-card warning">
            <div class="metric-value">{duplicate_groups:,}</div>
            <div class="metric-label">Duplicate Groups Found</div>
        </div>
        
        <div class="metric-card info">
            <div class="metric-value">{space_wasted:.1f} MB</div>
            <div class="metric-label">Wasted Storage Space</div>
        </div>
        
        <div class="metric-card success">
            <div class="metric-value">{total_recommendations:,}</div>
            <div class="metric-label">Recommendations</div>
        </div>
    </div>
    
    <div class="alert alert-info">
        <strong>Key Findings:</strong>
        <ul>
            <li>Found {duplicate_groups} groups of duplicate or similar documents</li>
            <li>{high_priority} high-priority recommendations require immediate attention</li>
            <li>Potential storage savings: {potential_savings:.1f} MB</li>
            <li>Duplicate rate: {(total_duplicates/total_docs*100):.1f}% of analyzed documents</li>
        </ul>
    </div>
</div>
"""
    
    def _generate_document_overview(self, results: Dict[str, Any]) -> str:
        """Generate document overview section"""
        # This would analyze document types, sizes, dates, etc.
        return f"""
<div class="section">
    <h2>📁 Document Overview</h2>
    
    <h3>File Type Distribution</h3>
    <div class="chart-container">
        <p>File type analysis would be displayed here with charts showing distribution of document types, sizes, and modification dates.</p>
    </div>
    
    <h3>Storage Analysis</h3>
    <div class="chart-container">
        <p>Storage usage charts and trends would be displayed here.</p>
    </div>
</div>
"""
    
    def _generate_duplicate_analysis(self, results: Dict[str, Any]) -> str:
        """Generate duplicate analysis section"""
        html = """
<div class="section">
    <h2>🔍 Duplicate Analysis</h2>
"""
        
        # Hash duplicates
        if 'hash_duplicates' in results:
            hash_results = results['hash_duplicates']
            duplicate_groups = hash_results.get('duplicate_groups', [])
            
            html += f"""
    <h3>Exact Duplicates (Hash-based)</h3>
    <p>Found {len(duplicate_groups)} groups of identical files.</p>
    
    <button class="collapsible">Show Exact Duplicate Groups ({len(duplicate_groups)})</button>
    <div class="collapsible-content">
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Group ID</th>
                        <th>Files</th>
                        <th>Size per File</th>
                        <th>Wasted Space</th>
                        <th>Hash</th>
                    </tr>
                </thead>
                <tbody>
"""
            
            for group in duplicate_groups[:10]:  # Show top 10
                html += f"""
                    <tr>
                        <td>{group['group_id']}</td>
                        <td>{group['document_count']}</td>
                        <td>{group['documents'][0]['size_mb']:.1f} MB</td>
                        <td>{group['wasted_space']/(1024*1024):.1f} MB</td>
                        <td class="file-path">{group.get('hash', '')[:16]}...</td>
                    </tr>
"""
            
            html += """
                </tbody>
            </table>
        </div>
    </div>
"""
        
        # Similarity duplicates
        if 'similarity_duplicates' in results:
            sim_results = results['similarity_duplicates']
            similarity_groups = sim_results.get('similarity_groups', [])
            
            html += f"""
    <h3>Similar Content</h3>
    <p>Found {len(similarity_groups)} groups of semantically similar documents.</p>
    
    <button class="collapsible">Show Similar Document Groups ({len(similarity_groups)})</button>
    <div class="collapsible-content">
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Group ID</th>
                        <th>Files</th>
                        <th>Avg Similarity</th>
                        <th>Relationship Type</th>
                    </tr>
                </thead>
                <tbody>
"""
            
            for group in similarity_groups[:10]:  # Show top 10
                html += f"""
                    <tr>
                        <td>{group['group_id']}</td>
                        <td>{group['document_count']}</td>
                        <td>{group['avg_similarity']:.1%}</td>
                        <td>{group.get('relationship_type', 'similar_content')}</td>
                    </tr>
"""
            
            html += """
                </tbody>
            </table>
        </div>
    </div>
"""
        
        html += "</div>"
        return html
    
    def _generate_nlp_analysis(self, results: Dict[str, Any]) -> str:
        """Generate NLP analysis section"""
        html = """
<div class="section">
    <h2>🧠 Content Analysis</h2>
"""
        
        # Entities
        if 'entities' in results:
            entities = results['entities']
            html += f"""
    <h3>Named Entities</h3>
    <p>Extracted {sum(len(ents) for ents in entities.values())} unique entities across {len(entities)} categories.</p>
    
    <div class="chart-container">
"""
            
            for entity_type, entity_list in list(entities.items())[:5]:  # Top 5 entity types
                html += f"<h4>{entity_type.title()}</h4>"
                for entity in entity_list[:10]:  # Top 10 entities per type
                    html += f'<span class="tag">{entity["text"]} ({entity["count"]})</span>'
                html += "<br><br>"
            
            html += "</div>"
        
        # Keywords
        if 'keywords' in results:
            keywords = results['keywords']
            html += f"""
    <h3>Key Terms</h3>
    <p>Identified {len(keywords)} important keywords across all documents.</p>
    
    <div class="chart-container">
"""
            
            for keyword in keywords[:20]:  # Top 20 keywords
                html += f'<span class="tag">{keyword["word"]} ({keyword["avg_score"]:.2f})</span>'
            
            html += "</div>"
        
        # Clusters
        if 'clusters' in results:
            clusters = results['clusters']
            cluster_summary = clusters.get('cluster_summary', {})
            
            html += f"""
    <h3>Document Clusters</h3>
    <p>Organized documents into {len(cluster_summary)} thematic clusters.</p>
"""
        
        html += "</div>"
        return html
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> str:
        """Generate recommendations section"""
        recommendations = results.get('recommendations', {})
        
        html = """
<div class="section">
    <h2>💡 Recommendations</h2>
"""
        
        # High priority recommendations
        high_priority = recommendations.get('high_priority', [])
        if high_priority:
            html += f"""
    <h3>🔴 High Priority ({len(high_priority)} items)</h3>
    <div class="table-container">
        <table>
            <thead>
                <tr>
                    <th>Action</th>
                    <th>Group</th>
                    <th>Files</th>
                    <th>Space Saved</th>
                    <th>Reasoning</th>
                </tr>
            </thead>
            <tbody>
"""
            
            for rec in high_priority[:10]:  # Show top 10
                space_saved = rec.get('space_saved_mb', 0)
                file_count = len(rec.get('delete_documents', rec.get('documents', [])))
                
                html += f"""
                <tr class="priority-high">
                    <td>{rec.get('action', '')}</td>
                    <td>{rec.get('group_id', '')}</td>
                    <td>{file_count}</td>
                    <td>{space_saved:.1f} MB</td>
                    <td>{rec.get('reasoning', '')}</td>
                </tr>
"""
            
            html += """
            </tbody>
        </table>
    </div>
"""
        
        # Medium priority recommendations
        medium_priority = recommendations.get('medium_priority', [])
        if medium_priority:
            html += f"""
    <h3>🟡 Medium Priority ({len(medium_priority)} items)</h3>
    <button class="collapsible">Show Medium Priority Recommendations</button>
    <div class="collapsible-content">
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Action</th>
                        <th>Group</th>
                        <th>Files</th>
                        <th>Reasoning</th>
                    </tr>
                </thead>
                <tbody>
"""
            
            for rec in medium_priority[:10]:  # Show top 10
                file_count = len(rec.get('documents', []))
                
                html += f"""
                <tr class="priority-medium">
                    <td>{rec.get('action', '')}</td>
                    <td>{rec.get('group_id', '')}</td>
                    <td>{file_count}</td>
                    <td>{rec.get('reasoning', '')}</td>
                </tr>
"""
            
            html += """
                </tbody>
            </table>
        </div>
    </div>
"""
        
        html += "</div>"
        return html
    
    def _generate_detailed_tables(self, results: Dict[str, Any]) -> str:
        """Generate detailed data tables section"""
        return """
<div class="section">
    <h2>📋 Detailed Data</h2>
    
    <div class="alert alert-info">
        <strong>Note:</strong> For complete detailed data, please refer to the CSV exports. 
        This report shows summarized information for readability.
    </div>
    
    <p>Detailed tables with all documents, duplicate groups, and analysis results are available in the CSV export files.</p>
</div>
"""
    
    def _generate_footer(self) -> str:
        """Generate report footer"""
        return f"""
<div class="footer">
    <p>Generated by DocRecon AI - Document Consolidation Tool</p>
    <p>Report created on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}</p>
</div>
"""
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get report generation statistics.
        
        Returns:
            dict: Statistics
        """
        return {
            'reports_generated': self.reports_generated,
        }
    
    def reset_statistics(self):
        """Reset statistics"""
        self.reports_generated = 0

