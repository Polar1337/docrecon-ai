"""
Interactive Streamlit Dashboard for DocRecon AI

Provides a web-based interface for exploring analysis results,
managing duplicates, and generating reports.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Optional dependencies
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

logger = logging.getLogger(__name__)


class DocReconDashboard:
    """
    Interactive Streamlit dashboard for DocRecon AI results.
    
    Provides a comprehensive web interface for:
    - Viewing analysis summaries
    - Exploring duplicate groups
    - Managing recommendations
    - Filtering and searching documents
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize dashboard.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if not STREAMLIT_AVAILABLE:
            raise ImportError("Streamlit required for dashboard. Install: pip install streamlit")
        
        if not PLOTLY_AVAILABLE:
            self.logger.warning("Plotly not available. Charts will be limited. Install: pip install plotly")
        
        # Dashboard state
        self.analysis_results = None
        self.current_page = "Overview"
        
        # Initialize session state
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state"""
        if 'analysis_loaded' not in st.session_state:
            st.session_state.analysis_loaded = False
        if 'selected_duplicates' not in st.session_state:
            st.session_state.selected_duplicates = []
        if 'filter_settings' not in st.session_state:
            st.session_state.filter_settings = {}
    
    def run_dashboard(self, analysis_results: Dict[str, Any] = None):
        """
        Run the Streamlit dashboard.
        
        Args:
            analysis_results: Optional pre-loaded analysis results
        """
        st.set_page_config(
            page_title="DocRecon AI Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Load analysis results
        if analysis_results:
            self.analysis_results = analysis_results
            st.session_state.analysis_loaded = True
        
        # Main dashboard layout
        self._render_sidebar()
        self._render_main_content()
    
    def _render_sidebar(self):
        """Render sidebar navigation and controls"""
        st.sidebar.title("📊 DocRecon AI")
        st.sidebar.markdown("---")
        
        # File upload for analysis results
        if not st.session_state.analysis_loaded:
            st.sidebar.subheader("📁 Load Analysis Results")
            uploaded_file = st.sidebar.file_uploader(
                "Upload JSON analysis results",
                type=['json'],
                help="Upload the complete analysis results JSON file"
            )
            
            if uploaded_file is not None:
                try:
                    self.analysis_results = json.load(uploaded_file)
                    st.session_state.analysis_loaded = True
                    st.sidebar.success("Analysis results loaded successfully!")
                    st.experimental_rerun()
                except Exception as e:
                    st.sidebar.error(f"Error loading file: {e}")
        
        # Navigation
        if st.session_state.analysis_loaded:
            st.sidebar.subheader("🧭 Navigation")
            pages = [
                "📊 Overview",
                "📁 Documents", 
                "🔍 Duplicates",
                "🧠 NLP Analysis",
                "💡 Recommendations",
                "📈 Statistics"
            ]
            
            selected_page = st.sidebar.radio("Go to:", pages)
            self.current_page = selected_page.split(" ", 1)[1]  # Remove emoji
            
            # Quick stats in sidebar
            self._render_sidebar_stats()
    
    def _render_sidebar_stats(self):
        """Render quick statistics in sidebar"""
        if not self.analysis_results:
            return
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Quick Stats")
        
        stats = self.analysis_results.get('statistics', {})
        
        # Total documents
        total_docs = stats.get('total_documents', 0)
        st.sidebar.metric("Total Documents", f"{total_docs:,}")
        
        # Duplicate groups
        duplicate_count = self._count_duplicate_groups()
        st.sidebar.metric("Duplicate Groups", duplicate_count)
        
        # Wasted space
        wasted_space = self._calculate_wasted_space()
        st.sidebar.metric("Wasted Space", f"{wasted_space:.1f} MB")
        
        # Recommendations
        rec_count = self._count_recommendations()
        st.sidebar.metric("Recommendations", rec_count)
    
    def _render_main_content(self):
        """Render main content area based on selected page"""
        if not st.session_state.analysis_loaded:
            self._render_welcome_page()
        elif self.current_page == "Overview":
            self._render_overview_page()
        elif self.current_page == "Documents":
            self._render_documents_page()
        elif self.current_page == "Duplicates":
            self._render_duplicates_page()
        elif self.current_page == "NLP Analysis":
            self._render_nlp_page()
        elif self.current_page == "Recommendations":
            self._render_recommendations_page()
        elif self.current_page == "Statistics":
            self._render_statistics_page()
    
    def _render_welcome_page(self):
        """Render welcome page when no data is loaded"""
        st.title("🎉 Welcome to DocRecon AI Dashboard")
        
        st.markdown("""
        ### 📋 Getting Started
        
        1. **Upload Analysis Results**: Use the sidebar to upload your DocRecon AI analysis results (JSON format)
        2. **Explore Your Data**: Navigate through different sections to explore your document analysis
        3. **Manage Duplicates**: Review and manage duplicate files and recommendations
        4. **Generate Reports**: Export filtered data and create custom reports
        
        ### 🔧 Features
        
        - **Interactive Overview**: Visual summary of your document analysis
        - **Document Explorer**: Browse and filter your document inventory
        - **Duplicate Manager**: Review duplicate groups and similarity clusters
        - **NLP Insights**: Explore extracted entities, keywords, and topics
        - **Smart Recommendations**: Review and act on automated suggestions
        - **Detailed Statistics**: Dive deep into analysis metrics
        """)
        
        st.info("👆 Upload your analysis results using the sidebar to get started!")
    
    def _render_overview_page(self):
        """Render overview dashboard page"""
        st.title("📊 Analysis Overview")
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_docs = self.analysis_results.get('statistics', {}).get('total_documents', 0)
            st.metric("Total Documents", f"{total_docs:,}")
        
        with col2:
            duplicate_groups = self._count_duplicate_groups()
            st.metric("Duplicate Groups", duplicate_groups)
        
        with col3:
            wasted_space = self._calculate_wasted_space()
            st.metric("Wasted Space", f"{wasted_space:.1f} MB")
        
        with col4:
            recommendations = self._count_recommendations()
            st.metric("Recommendations", recommendations)
        
        # Charts row
        if PLOTLY_AVAILABLE:
            col1, col2 = st.columns(2)
            
            with col1:
                self._render_duplicate_types_chart()
            
            with col2:
                self._render_file_size_distribution()
        
        # Recent activity / highlights
        st.subheader("🎯 Key Findings")
        self._render_key_findings()
    
    def _render_documents_page(self):
        """Render documents explorer page"""
        st.title("📁 Document Explorer")
        
        # Filters
        st.subheader("🔍 Filters")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            file_types = self._get_file_types()
            selected_types = st.multiselect("File Types", file_types, default=file_types[:5])
        
        with col2:
            size_range = st.slider("File Size (MB)", 0.0, 100.0, (0.0, 100.0))
        
        with col3:
            source_types = self._get_source_types()
            selected_sources = st.multiselect("Source Types", source_types, default=source_types)
        
        # Document table
        st.subheader("📋 Document Inventory")
        documents_df = self._create_documents_dataframe()
        
        # Apply filters
        if selected_types:
            documents_df = documents_df[documents_df['File_Extension'].isin(selected_types)]
        
        documents_df = documents_df[
            (documents_df['Size_MB'] >= size_range[0]) & 
            (documents_df['Size_MB'] <= size_range[1])
        ]
        
        if selected_sources:
            documents_df = documents_df[documents_df['Source_Type'].isin(selected_sources)]
        
        # Display table
        st.dataframe(
            documents_df,
            use_container_width=True,
            height=400
        )
        
        # Download filtered data
        if st.button("📥 Download Filtered Data"):
            csv = documents_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="filtered_documents.csv",
                mime="text/csv"
            )
    
    def _render_duplicates_page(self):
        """Render duplicates management page"""
        st.title("🔍 Duplicate Management")
        
        # Duplicate type tabs
        tab1, tab2, tab3 = st.tabs(["🎯 Exact Duplicates", "🔄 Similar Content", "📝 Document Versions"])
        
        with tab1:
            self._render_hash_duplicates()
        
        with tab2:
            self._render_similarity_duplicates()
        
        with tab3:
            self._render_version_groups()
    
    def _render_nlp_page(self):
        """Render NLP analysis page"""
        st.title("🧠 Content Analysis")
        
        # NLP tabs
        tab1, tab2, tab3 = st.tabs(["🏷️ Named Entities", "🔑 Keywords", "📊 Document Clusters"])
        
        with tab1:
            self._render_entities_analysis()
        
        with tab2:
            self._render_keywords_analysis()
        
        with tab3:
            self._render_clusters_analysis()
    
    def _render_recommendations_page(self):
        """Render recommendations management page"""
        st.title("💡 Smart Recommendations")
        
        recommendations = self.analysis_results.get('recommendations', {})
        
        # Priority tabs
        tab1, tab2, tab3 = st.tabs(["🔴 High Priority", "🟡 Medium Priority", "🟢 Low Priority"])
        
        with tab1:
            self._render_priority_recommendations(recommendations.get('high_priority', []), "high")
        
        with tab2:
            self._render_priority_recommendations(recommendations.get('medium_priority', []), "medium")
        
        with tab3:
            self._render_priority_recommendations(recommendations.get('low_priority', []), "low")
    
    def _render_statistics_page(self):
        """Render detailed statistics page"""
        st.title("📈 Detailed Statistics")
        
        stats = self.analysis_results.get('statistics', {})
        
        # Statistics sections
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Processing Statistics")
            self._render_processing_stats(stats)
        
        with col2:
            st.subheader("🔍 Detection Statistics")
            self._render_detection_stats(stats)
        
        # Detailed breakdowns
        st.subheader("📋 Detailed Breakdowns")
        self._render_detailed_stats(stats)
    
    # Helper methods for rendering specific components
    
    def _render_duplicate_types_chart(self):
        """Render duplicate types pie chart"""
        if not PLOTLY_AVAILABLE:
            st.info("Install plotly for charts: pip install plotly")
            return
        
        st.subheader("🔍 Duplicate Types")
        
        # Count different types of duplicates
        hash_count = len(self.analysis_results.get('hash_duplicates', {}).get('duplicate_groups', []))
        sim_count = len(self.analysis_results.get('similarity_duplicates', {}).get('similarity_groups', []))
        ver_count = len(self.analysis_results.get('version_groups', {}).get('version_groups', []))
        
        if hash_count + sim_count + ver_count == 0:
            st.info("No duplicates found")
            return
        
        fig = px.pie(
            values=[hash_count, sim_count, ver_count],
            names=['Exact Duplicates', 'Similar Content', 'Document Versions'],
            title="Distribution of Duplicate Types"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_file_size_distribution(self):
        """Render file size distribution chart"""
        if not PLOTLY_AVAILABLE:
            st.info("Install plotly for charts: pip install plotly")
            return
        
        st.subheader("📊 File Size Distribution")
        
        # This would need document data to create the chart
        st.info("File size distribution chart would be displayed here")
    
    def _render_key_findings(self):
        """Render key findings section"""
        findings = []
        
        # Check for high-impact duplicates
        wasted_space = self._calculate_wasted_space()
        if wasted_space > 100:
            findings.append(f"🚨 High storage waste detected: {wasted_space:.1f} MB could be recovered")
        
        # Check for many duplicate groups
        duplicate_count = self._count_duplicate_groups()
        if duplicate_count > 10:
            findings.append(f"📁 {duplicate_count} duplicate groups found - significant cleanup opportunity")
        
        # Check for high-priority recommendations
        high_priority = len(self.analysis_results.get('recommendations', {}).get('high_priority', []))
        if high_priority > 0:
            findings.append(f"⚡ {high_priority} high-priority actions require immediate attention")
        
        if not findings:
            findings.append("✅ Document collection appears well-organized with minimal duplicates")
        
        for finding in findings:
            st.info(finding)
    
    def _render_hash_duplicates(self):
        """Render exact duplicates section"""
        hash_results = self.analysis_results.get('hash_duplicates', {})
        duplicate_groups = hash_results.get('duplicate_groups', [])
        
        if not duplicate_groups:
            st.info("No exact duplicates found")
            return
        
        st.subheader(f"Found {len(duplicate_groups)} groups of exact duplicates")
        
        for i, group in enumerate(duplicate_groups[:10]):  # Show first 10
            with st.expander(f"Group {i+1}: {group['document_count']} files ({group['wasted_space']/(1024*1024):.1f} MB wasted)"):
                for doc in group['documents']:
                    st.write(f"📄 {doc['filename']} ({doc['size_mb']:.1f} MB)")
                    st.caption(f"Path: {doc['path']}")
                
                if st.button(f"Mark for deletion", key=f"delete_hash_{i}"):
                    st.success("Marked for deletion (demo)")
    
    def _render_similarity_duplicates(self):
        """Render similar content section"""
        sim_results = self.analysis_results.get('similarity_duplicates', {})
        similarity_groups = sim_results.get('similarity_groups', [])
        
        if not similarity_groups:
            st.info("No similar content groups found")
            return
        
        st.subheader(f"Found {len(similarity_groups)} groups of similar content")
        
        for i, group in enumerate(similarity_groups[:10]):  # Show first 10
            similarity = group.get('avg_similarity', 0)
            with st.expander(f"Group {i+1}: {group['document_count']} files ({similarity:.1%} similarity)"):
                for doc in group['documents']:
                    st.write(f"📄 {doc['filename']}")
                    st.caption(f"Path: {doc['path']}")
                
                st.info(f"Relationship: {group.get('relationship_type', 'similar_content')}")
    
    def _render_version_groups(self):
        """Render document versions section"""
        ver_results = self.analysis_results.get('version_groups', {})
        version_groups = ver_results.get('version_groups', [])
        
        if not version_groups:
            st.info("No document version groups found")
            return
        
        st.subheader(f"Found {len(version_groups)} version groups")
        
        for i, group in enumerate(version_groups[:10]):  # Show first 10
            with st.expander(f"Group {i+1}: {group['document_count']} versions of '{group['base_name']}'"):
                timeline = group.get('timeline', [])
                for entry in timeline:
                    icon = "🆕" if entry.get('is_likely_latest') else "📄"
                    st.write(f"{icon} {entry['filename']}")
                    if entry.get('indicators'):
                        st.caption(f"Indicators: {', '.join(entry['indicators'])}")
    
    def _render_priority_recommendations(self, recommendations: List[Dict], priority: str):
        """Render recommendations for a specific priority level"""
        if not recommendations:
            st.info(f"No {priority} priority recommendations")
            return
        
        for i, rec in enumerate(recommendations):
            with st.expander(f"{rec.get('action', 'Action')} - {rec.get('group_id', '')}"):
                st.write(f"**Reasoning:** {rec.get('reasoning', '')}")
                st.write(f"**Confidence:** {rec.get('confidence', 0):.1%}")
                
                if 'space_saved_mb' in rec:
                    st.write(f"**Space Saved:** {rec['space_saved_mb']:.1f} MB")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Accept", key=f"accept_{priority}_{i}"):
                        st.success("Recommendation accepted (demo)")
                with col2:
                    if st.button("❌ Dismiss", key=f"dismiss_{priority}_{i}"):
                        st.info("Recommendation dismissed (demo)")
    
    # Utility methods
    
    def _count_duplicate_groups(self) -> int:
        """Count total duplicate groups"""
        count = 0
        if 'hash_duplicates' in self.analysis_results:
            count += len(self.analysis_results['hash_duplicates'].get('duplicate_groups', []))
        if 'similarity_duplicates' in self.analysis_results:
            count += len(self.analysis_results['similarity_duplicates'].get('similarity_groups', []))
        if 'version_groups' in self.analysis_results:
            count += len(self.analysis_results['version_groups'].get('version_groups', []))
        return count
    
    def _calculate_wasted_space(self) -> float:
        """Calculate total wasted space in MB"""
        wasted = 0
        if 'hash_duplicates' in self.analysis_results:
            stats = self.analysis_results['hash_duplicates'].get('statistics', {})
            wasted += stats.get('total_wasted_space_mb', 0)
        return wasted
    
    def _count_recommendations(self) -> int:
        """Count total recommendations"""
        rec_data = self.analysis_results.get('recommendations', {})
        summary = rec_data.get('summary', {})
        return summary.get('total_recommendations', 0)
    
    def _get_file_types(self) -> List[str]:
        """Get list of file types from analysis"""
        # This would extract file types from document data
        return ['.pdf', '.docx', '.txt', '.xlsx', '.pptx']
    
    def _get_source_types(self) -> List[str]:
        """Get list of source types from analysis"""
        # This would extract source types from document data
        return ['local', 'smb', 'sharepoint', 'onedrive']
    
    def _create_documents_dataframe(self) -> pd.DataFrame:
        """Create pandas DataFrame from document data"""
        # This would convert document data to DataFrame
        # For now, return empty DataFrame
        return pd.DataFrame(columns=['Filename', 'Size_MB', 'File_Extension', 'Source_Type', 'Modified_Date'])
    
    def _render_entities_analysis(self):
        """Render named entities analysis"""
        entities = self.analysis_results.get('entities', {})
        
        if not entities:
            st.info("No named entities found")
            return
        
        for entity_type, entity_list in entities.items():
            st.subheader(f"{entity_type.title()} ({len(entity_list)} unique)")
            
            # Show top entities
            for entity in entity_list[:10]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(entity['text'])
                with col2:
                    st.caption(f"{entity['count']} mentions")
    
    def _render_keywords_analysis(self):
        """Render keywords analysis"""
        keywords = self.analysis_results.get('keywords', [])
        
        if not keywords:
            st.info("No keywords found")
            return
        
        st.subheader(f"Top Keywords ({len(keywords)} total)")
        
        for keyword in keywords[:20]:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(keyword['word'])
            with col2:
                st.caption(f"Score: {keyword['avg_score']:.2f}")
    
    def _render_clusters_analysis(self):
        """Render document clusters analysis"""
        clusters = self.analysis_results.get('clusters', {})
        
        if not clusters:
            st.info("No document clusters found")
            return
        
        st.subheader("Document Clusters")
        st.info("Cluster analysis would be displayed here")
    
    def _render_processing_stats(self, stats: Dict[str, Any]):
        """Render processing statistics"""
        st.metric("Total Documents", stats.get('total_documents', 0))
        st.metric("Processing Errors", stats.get('processing_errors', 0))
    
    def _render_detection_stats(self, stats: Dict[str, Any]):
        """Render detection statistics"""
        hash_stats = stats.get('hash_detection', {})
        st.metric("Hash Comparisons", hash_stats.get('documents_processed', 0))
        
        sim_stats = stats.get('similarity_analysis', {})
        st.metric("Similarity Comparisons", sim_stats.get('comparisons_made', 0))
    
    def _render_detailed_stats(self, stats: Dict[str, Any]):
        """Render detailed statistics breakdown"""
        st.json(stats)


def run_dashboard(analysis_results: Dict[str, Any] = None, port: int = 8501):
    """
    Run the DocRecon AI dashboard.
    
    Args:
        analysis_results: Optional pre-loaded analysis results
        port: Port to run Streamlit on
    """
    if not STREAMLIT_AVAILABLE:
        print("Streamlit not available. Install: pip install streamlit")
        return
    
    dashboard = DocReconDashboard()
    dashboard.run_dashboard(analysis_results)


if __name__ == "__main__":
    run_dashboard()

