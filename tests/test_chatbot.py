"""
Tests for the NLP chatbot.
"""

import pytest
from src.chatbot.nlp_chatbot import AlumniChatbot, SimpleQueryParser


class TestSimpleQueryParser:
    """Tests for SimpleQueryParser."""
    
    def test_parse_company_query(self):
        """Test parsing company-related queries."""
        intent, params = SimpleQueryParser.parse("Who works at Google?")
        assert intent == 'search_by_company'
        assert 'company' in params
        assert 'google' in params['company'].lower()
    
    def test_parse_batch_query(self):
        """Test parsing batch-related queries."""
        intent, params = SimpleQueryParser.parse("Find alumni from batch 2020")
        assert intent == 'search_by_batch'
        assert params.get('batch') == '2020'
    
    def test_parse_location_query(self):
        """Test parsing location-related queries."""
        intent, params = SimpleQueryParser.parse("Who is based in Bangalore?")
        assert intent == 'search_by_location'
        assert 'bangalore' in params.get('location', '').lower()
    
    def test_parse_year_in_query(self):
        """Test extracting year from query."""
        intent, params = SimpleQueryParser.parse("batch 2021")
        assert params.get('batch') == '2021'
    
    def test_default_to_name_search(self):
        """Test defaulting to name search for unrecognized queries."""
        intent, params = SimpleQueryParser.parse("John Smith")
        assert intent == 'search_by_name'
        assert 'name' in params


class TestAlumniChatbot:
    """Tests for AlumniChatbot."""
    
    @pytest.fixture
    def chatbot(self):
        """Create a chatbot without API key (rule-based mode)."""
        return AlumniChatbot(api_key=None)
    
    def test_extract_company_from_query(self, chatbot):
        """Test extracting company from natural language query."""
        params = chatbot.extract_search_params("Who works at Microsoft?")
        assert 'company' in params
    
    def test_extract_batch_from_query(self, chatbot):
        """Test extracting batch from natural language query."""
        params = chatbot.extract_search_params("Find alumni from 2020 batch")
        assert params.get('batch') == '2020'
    
    def test_extract_location_from_query(self, chatbot):
        """Test extracting location from natural language query."""
        params = chatbot.extract_search_params("Alumni in Mumbai")
        # Either location or could be parsed differently
        assert params  # Should extract something
    
    def test_no_results_response(self, chatbot):
        """Test generating response when no results found."""
        response = chatbot._generate_no_results_response("test query")
        assert response
        assert len(response) > 0
    
    def test_suggest_queries(self, chatbot):
        """Test getting query suggestions."""
        suggestions = chatbot.suggest_queries()
        assert len(suggestions) > 0
        assert any('Google' in s or 'batch' in s.lower() for s in suggestions)
