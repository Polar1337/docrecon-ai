"""
Named Entity Recognition and keyword extraction

Extracts named entities, keywords, and key phrases from document text
to provide semantic metadata and improve searchability.
"""

import re
from collections import Counter
from typing import List, Dict, Any, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)

# Optional NLP dependencies
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available. Install: pip install spacy")

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.tag import pos_tag
    from nltk.chunk import ne_chunk
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not available. Install: pip install nltk")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class EntityExtractor:
    """
    Extracts named entities and keywords from text content.
    
    Supports multiple NLP libraries:
    - spaCy (recommended for entity recognition)
    - NLTK (fallback and keyword extraction)
    - TF-IDF (keyword extraction)
    """
    
    def __init__(self, config: Optional[Any] = None):
        """
        Initialize entity extractor.
        
        Args:
            config: Configuration object with NLP settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Configuration
        self.language = getattr(config.nlp, 'language', 'de') if config else 'de'
        self.enable_entities = getattr(config.nlp, 'enable_entities', True) if config else True
        self.enable_keywords = getattr(config.nlp, 'enable_keywords', True) if config else True
        
        # Models
        self.spacy_model = None
        self.nltk_initialized = False
        self.lemmatizer = None
        self.stop_words = set()
        
        # Statistics
        self.texts_processed = 0
        self.entities_extracted = 0
        self.keywords_extracted = 0
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize NLP models"""
        # Initialize spaCy
        if SPACY_AVAILABLE and self.enable_entities:
            self._initialize_spacy()
        
        # Initialize NLTK
        if NLTK_AVAILABLE:
            self._initialize_nltk()
    
    def _initialize_spacy(self):
        """Initialize spaCy model"""
        try:
            # Map language codes to spaCy model names
            model_map = {
                'de': 'de_core_news_sm',
                'en': 'en_core_web_sm',
                'fr': 'fr_core_news_sm',
                'es': 'es_core_news_sm',
            }
            
            model_name = model_map.get(self.language, 'en_core_web_sm')
            
            try:
                self.spacy_model = spacy.load(model_name)
                self.logger.info(f"Loaded spaCy model: {model_name}")
            except OSError:
                # Try to download the model
                self.logger.info(f"Downloading spaCy model: {model_name}")
                spacy.cli.download(model_name)
                self.spacy_model = spacy.load(model_name)
                
        except Exception as e:
            self.logger.warning(f"Failed to initialize spaCy model: {e}")
            self.spacy_model = None
    
    def _initialize_nltk(self):
        """Initialize NLTK resources"""
        try:
            # Download required NLTK data
            nltk_downloads = [
                'punkt', 'averaged_perceptron_tagger', 'maxent_ne_chunker',
                'words', 'stopwords', 'wordnet'
            ]
            
            for resource in nltk_downloads:
                try:
                    nltk.data.find(f'tokenizers/{resource}')
                except LookupError:
                    try:
                        nltk.download(resource, quiet=True)
                    except Exception:
                        pass
            
            # Initialize lemmatizer
            self.lemmatizer = WordNetLemmatizer()
            
            # Load stop words
            try:
                if self.language == 'de':
                    self.stop_words = set(stopwords.words('german'))
                elif self.language == 'en':
                    self.stop_words = set(stopwords.words('english'))
                else:
                    self.stop_words = set(stopwords.words('english'))  # Default
            except Exception:
                self.stop_words = set()
            
            self.nltk_initialized = True
            self.logger.info("NLTK initialized successfully")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize NLTK: {e}")
            self.nltk_initialized = False
    
    def extract_entities_and_keywords(self, text: str) -> Dict[str, Any]:
        """
        Extract entities and keywords from text.
        
        Args:
            text: Text content to analyze
            
        Returns:
            dict: Extracted entities and keywords
        """
        result = {
            'entities': {},
            'keywords': [],
            'key_phrases': [],
            'statistics': {
                'text_length': len(text),
                'word_count': len(text.split()),
                'sentence_count': 0,
            }
        }
        
        if not text or not text.strip():
            return result
        
        try:
            # Extract entities
            if self.enable_entities:
                if self.spacy_model:
                    entities = self._extract_entities_spacy(text)
                elif self.nltk_initialized:
                    entities = self._extract_entities_nltk(text)
                else:
                    entities = {}
                
                result['entities'] = entities
                self.entities_extracted += len(entities)
            
            # Extract keywords
            if self.enable_keywords:
                keywords = self._extract_keywords(text)
                key_phrases = self._extract_key_phrases(text)
                
                result['keywords'] = keywords
                result['key_phrases'] = key_phrases
                self.keywords_extracted += len(keywords)
            
            # Calculate statistics
            if self.nltk_initialized:
                try:
                    sentences = sent_tokenize(text)
                    result['statistics']['sentence_count'] = len(sentences)
                except Exception:
                    pass
            
            self.texts_processed += 1
            
        except Exception as e:
            self.logger.error(f"Error extracting entities and keywords: {e}")
        
        return result
    
    def _extract_entities_spacy(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities using spaCy"""
        entities = {}
        
        try:
            doc = self.spacy_model(text)
            
            for ent in doc.ents:
                entity_type = ent.label_
                entity_text = ent.text.strip()
                
                if entity_type not in entities:
                    entities[entity_type] = []
                
                # Check if entity already exists
                existing = False
                for existing_ent in entities[entity_type]:
                    if existing_ent['text'].lower() == entity_text.lower():
                        existing_ent['count'] += 1
                        existing = True
                        break
                
                if not existing:
                    entities[entity_type].append({
                        'text': entity_text,
                        'count': 1,
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'confidence': getattr(ent, 'confidence', 1.0)
                    })
            
            # Sort entities by count
            for entity_type in entities:
                entities[entity_type].sort(key=lambda x: x['count'], reverse=True)
                
        except Exception as e:
            self.logger.error(f"Error in spaCy entity extraction: {e}")
        
        return entities
    
    def _extract_entities_nltk(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract entities using NLTK"""
        entities = {}
        
        try:
            # Tokenize and tag
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            
            # Named entity chunking
            tree = ne_chunk(pos_tags)
            
            for chunk in tree:
                if hasattr(chunk, 'label'):
                    entity_type = chunk.label()
                    entity_text = ' '.join([token for token, pos in chunk])
                    
                    if entity_type not in entities:
                        entities[entity_type] = []
                    
                    # Check if entity already exists
                    existing = False
                    for existing_ent in entities[entity_type]:
                        if existing_ent['text'].lower() == entity_text.lower():
                            existing_ent['count'] += 1
                            existing = True
                            break
                    
                    if not existing:
                        entities[entity_type].append({
                            'text': entity_text,
                            'count': 1,
                            'confidence': 0.8  # Default confidence for NLTK
                        })
            
            # Sort entities by count
            for entity_type in entities:
                entities[entity_type].sort(key=lambda x: x['count'], reverse=True)
                
        except Exception as e:
            self.logger.error(f"Error in NLTK entity extraction: {e}")
        
        return entities
    
    def _extract_keywords(self, text: str, max_keywords: int = 20) -> List[Dict[str, Any]]:
        """Extract keywords using multiple methods"""
        keywords = []
        
        try:
            # Method 1: TF-IDF based keywords
            if SKLEARN_AVAILABLE:
                tfidf_keywords = self._extract_tfidf_keywords(text, max_keywords // 2)
                keywords.extend(tfidf_keywords)
            
            # Method 2: Frequency-based keywords
            freq_keywords = self._extract_frequency_keywords(text, max_keywords // 2)
            keywords.extend(freq_keywords)
            
            # Remove duplicates and sort by score
            seen = set()
            unique_keywords = []
            for kw in keywords:
                if kw['word'].lower() not in seen:
                    seen.add(kw['word'].lower())
                    unique_keywords.append(kw)
            
            # Sort by score and limit
            unique_keywords.sort(key=lambda x: x['score'], reverse=True)
            keywords = unique_keywords[:max_keywords]
            
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
        
        return keywords
    
    def _extract_tfidf_keywords(self, text: str, max_keywords: int) -> List[Dict[str, Any]]:
        """Extract keywords using TF-IDF"""
        keywords = []
        
        try:
            # Split text into sentences for TF-IDF
            if self.nltk_initialized:
                sentences = sent_tokenize(text)
            else:
                sentences = text.split('.')
            
            if len(sentences) < 2:
                return keywords
            
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=max_keywords * 2,
                stop_words=list(self.stop_words) if self.stop_words else None,
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.8
            )
            
            # Fit and transform
            tfidf_matrix = vectorizer.fit_transform(sentences)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get average TF-IDF scores
            mean_scores = tfidf_matrix.mean(axis=0).A1
            
            # Create keyword list
            for i, score in enumerate(mean_scores):
                if score > 0:
                    keywords.append({
                        'word': feature_names[i],
                        'score': float(score),
                        'method': 'tfidf'
                    })
            
            # Sort by score
            keywords.sort(key=lambda x: x['score'], reverse=True)
            keywords = keywords[:max_keywords]
            
        except Exception as e:
            self.logger.error(f"Error in TF-IDF keyword extraction: {e}")
        
        return keywords
    
    def _extract_frequency_keywords(self, text: str, max_keywords: int) -> List[Dict[str, Any]]:
        """Extract keywords based on frequency"""
        keywords = []
        
        try:
            # Tokenize and clean
            if self.nltk_initialized:
                tokens = word_tokenize(text.lower())
            else:
                tokens = re.findall(r'\b\w+\b', text.lower())
            
            # Filter tokens
            filtered_tokens = []
            for token in tokens:
                if (len(token) > 2 and 
                    token.isalpha() and 
                    token not in self.stop_words):
                    
                    # Lemmatize if possible
                    if self.lemmatizer:
                        token = self.lemmatizer.lemmatize(token)
                    
                    filtered_tokens.append(token)
            
            # Count frequencies
            word_freq = Counter(filtered_tokens)
            
            # Create keyword list
            total_words = len(filtered_tokens)
            for word, count in word_freq.most_common(max_keywords):
                score = count / total_words  # Normalize by total words
                keywords.append({
                    'word': word,
                    'score': score,
                    'count': count,
                    'method': 'frequency'
                })
                
        except Exception as e:
            self.logger.error(f"Error in frequency keyword extraction: {e}")
        
        return keywords
    
    def _extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[Dict[str, Any]]:
        """Extract key phrases (multi-word expressions)"""
        phrases = []
        
        try:
            # Simple n-gram extraction
            if self.nltk_initialized:
                sentences = sent_tokenize(text)
            else:
                sentences = text.split('.')
            
            phrase_counts = Counter()
            
            for sentence in sentences:
                # Extract 2-3 word phrases
                words = re.findall(r'\b\w+\b', sentence.lower())
                
                # Filter stop words
                filtered_words = [w for w in words if w not in self.stop_words and len(w) > 2]
                
                # Generate n-grams
                for n in [2, 3]:
                    for i in range(len(filtered_words) - n + 1):
                        phrase = ' '.join(filtered_words[i:i+n])
                        if len(phrase) > 5:  # Minimum phrase length
                            phrase_counts[phrase] += 1
            
            # Create phrase list
            total_phrases = sum(phrase_counts.values())
            for phrase, count in phrase_counts.most_common(max_phrases):
                if count > 1:  # Only phrases that appear multiple times
                    score = count / total_phrases
                    phrases.append({
                        'phrase': phrase,
                        'score': score,
                        'count': count
                    })
                    
        except Exception as e:
            self.logger.error(f"Error extracting key phrases: {e}")
        
        return phrases
    
    def get_entity_summary(self, entities: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Get summary statistics for extracted entities.
        
        Args:
            entities: Extracted entities
            
        Returns:
            dict: Entity summary statistics
        """
        summary = {
            'total_entities': 0,
            'entity_types': {},
            'most_common_entities': [],
        }
        
        all_entities = []
        
        for entity_type, entity_list in entities.items():
            count = len(entity_list)
            total_mentions = sum(ent['count'] for ent in entity_list)
            
            summary['entity_types'][entity_type] = {
                'unique_entities': count,
                'total_mentions': total_mentions,
                'top_entities': entity_list[:5]  # Top 5 entities of this type
            }
            
            summary['total_entities'] += count
            
            # Add to global list
            for ent in entity_list:
                all_entities.append({
                    'text': ent['text'],
                    'type': entity_type,
                    'count': ent['count'],
                    'confidence': ent.get('confidence', 1.0)
                })
        
        # Sort all entities by count
        all_entities.sort(key=lambda x: x['count'], reverse=True)
        summary['most_common_entities'] = all_entities[:10]
        
        return summary
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get entity extraction statistics.
        
        Returns:
            dict: Statistics about entity extraction
        """
        return {
            'texts_processed': self.texts_processed,
            'entities_extracted': self.entities_extracted,
            'keywords_extracted': self.keywords_extracted,
        }
    
    def reset_statistics(self):
        """Reset entity extraction statistics"""
        self.texts_processed = 0
        self.entities_extracted = 0
        self.keywords_extracted = 0

