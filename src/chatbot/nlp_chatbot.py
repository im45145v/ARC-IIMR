"""
NLP Chatbot for Alumni Database Queries.
Uses OpenAI API for natural language understanding.
"""

import os
import re
import logging
from typing import Dict, Any, List, Optional, Tuple

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AlumniChatbot:
    """
    NLP Chatbot for querying alumni database.
    Uses OpenAI for intent understanding and query generation.
    """
    
    def __init__(
        self,
        api_key: str = None,
        model: str = "gpt-3.5-turbo"
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None
        
        if self.api_key and OpenAI:
            self.client = OpenAI(api_key=self.api_key)
        
        self.system_prompt = """You are an AI assistant for an alumni database. 
Your job is to understand user queries about alumni and extract search parameters.

You should extract:
- name: Name of the alumni to search for
- batch: Graduation year/batch
- company: Company name where alumni works
- designation: Job title/designation
- location: City/location where alumni is based

Respond in JSON format with the extracted parameters. Only include parameters that are mentioned.
If you can't extract any parameters, respond with an empty JSON object {}.

Examples:
User: "Who works at Google?"
Response: {"company": "Google"}

User: "Find software engineers from batch 2020"
Response: {"designation": "software engineer", "batch": "2020"}

User: "List alumni in Bangalore"
Response: {"location": "Bangalore"}
"""
    
    def extract_search_params(self, query: str) -> Dict[str, str]:
        """
        Extract search parameters from natural language query.
        Uses OpenAI if available, otherwise falls back to rule-based extraction.
        """
        if self.client:
            return self._extract_with_openai(query)
        else:
            return self._extract_with_rules(query)
    
    def _extract_with_openai(self, query: str) -> Dict[str, str]:
        """Use OpenAI to extract search parameters."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.1,
                max_tokens=150
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{[^}]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
            
            return {}
            
        except Exception as e:
            logger.error(f"OpenAI extraction error: {e}")
            return self._extract_with_rules(query)
    
    def _extract_with_rules(self, query: str) -> Dict[str, str]:
        """Rule-based extraction when OpenAI is not available."""
        params = {}
        query_lower = query.lower()
        
        # Extract batch/year
        year_match = re.search(r'\b(20\d{2})\b', query)
        if year_match:
            params['batch'] = year_match.group(1)
        
        # Extract company (after "at", "in", "from" when talking about work)
        company_patterns = [
            r'works?\s+at\s+([a-zA-Z0-9\s&]+?)(?:\?|$|\s+(?:in|from|and))',
            r'working\s+at\s+([a-zA-Z0-9\s&]+?)(?:\?|$|\s+(?:in|from|and))',
            r'employed\s+(?:at|by)\s+([a-zA-Z0-9\s&]+?)(?:\?|$)',
            r'company\s+(?:is\s+)?([a-zA-Z0-9\s&]+?)(?:\?|$)',
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, query_lower)
            if match:
                params['company'] = match.group(1).strip()
                break
        
        # Extract location
        location_patterns = [
            r'(?:in|from|based\s+in)\s+([a-zA-Z\s]+?)(?:\?|$|who|that)',
            r'location\s+(?:is\s+)?([a-zA-Z\s]+?)(?:\?|$)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, query_lower)
            if match:
                location = match.group(1).strip()
                # Filter out common words
                if location not in ['the', 'a', 'an', 'batch', 'company']:
                    params['location'] = location
                    break
        
        # Extract designation
        designation_patterns = [
            r'(?:are|is)\s+(?:a\s+)?([a-zA-Z\s]+?)(?:\s+at|\s+in|\?|$)',
            r'(?:find|list|show)\s+([a-zA-Z\s]+?)(?:\s+from|\s+in|\?|$)',
        ]
        
        for pattern in designation_patterns:
            match = re.search(pattern, query_lower)
            if match:
                designation = match.group(1).strip()
                # Filter out question words
                question_words = ['who', 'what', 'where', 'when', 'how', 'alumni', 'all', 'the']
                if designation not in question_words and len(designation) > 2:
                    params['designation'] = designation
                    break
        
        return params
    
    def generate_response(
        self,
        query: str,
        results: List[Any],
        total_count: int = None
    ) -> str:
        """Generate a natural language response based on query results."""
        if not results:
            return self._generate_no_results_response(query)
        
        total = total_count or len(results)
        
        if self.client:
            return self._generate_response_with_openai(query, results, total)
        else:
            return self._generate_response_simple(results, total)
    
    def _generate_no_results_response(self, query: str) -> str:
        """Generate response when no results found."""
        responses = [
            "I couldn't find any alumni matching your query. Try being more specific or use different keywords.",
            "No alumni found with those criteria. You can search by name, company, batch, or location.",
            "Sorry, I didn't find any matches. Try searching with different terms.",
        ]
        import random
        return random.choice(responses)
    
    def _generate_response_simple(self, results: List[Any], total: int) -> str:
        """Generate a simple text response without AI."""
        response = f"Found {total} alumni:\n\n"
        
        for alum in results[:5]:
            response += f"• **{alum.name}**"
            if hasattr(alum, 'batch') and alum.batch:
                response += f" (Batch {alum.batch})"
            if hasattr(alum, 'current_company') and alum.current_company:
                designation = alum.current_designation or 'Employee'
                response += f" - {designation} at {alum.current_company}"
            if hasattr(alum, 'current_location') and alum.current_location:
                response += f", {alum.current_location}"
            response += "\n"
        
        if total > 5:
            response += f"\n*... and {total - 5} more alumni*"
        
        return response
    
    def _generate_response_with_openai(
        self,
        query: str,
        results: List[Any],
        total: int
    ) -> str:
        """Generate response using OpenAI for more natural language."""
        try:
            # Prepare alumni data summary
            alumni_data = []
            for alum in results[:5]:
                data = {
                    'name': alum.name,
                    'batch': getattr(alum, 'batch', None),
                    'company': getattr(alum, 'current_company', None),
                    'designation': getattr(alum, 'current_designation', None),
                    'location': getattr(alum, 'current_location', None),
                }
                alumni_data.append(data)
            
            prompt = f"""Based on the user's query and the search results, generate a helpful response.

User Query: {query}
Total Results: {total}
First 5 Results: {alumni_data}

Generate a friendly, conversational response that summarizes the findings. 
Include key details like names, companies, and locations.
If there are more than 5 results, mention that."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful alumni database assistant. Be concise but informative."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI response generation error: {e}")
            return self._generate_response_simple(results, total)
    
    def suggest_queries(self) -> List[str]:
        """Suggest example queries for users."""
        return [
            "Who works at Google?",
            "Find alumni from batch 2020",
            "List software engineers in Bangalore",
            "Show alumni at McKinsey",
            "Find data scientists",
            "Who is working in Mumbai?",
            "Alumni from 2019 batch working in consulting",
        ]


class SimpleQueryParser:
    """
    Simple query parser for when OpenAI is not available.
    Uses pattern matching to understand user intent.
    """
    
    INTENT_PATTERNS = {
        'search_by_company': [
            r'who\s+works?\s+at\s+(.+)',
            r'alumni\s+at\s+(.+)',
            r'employees?\s+(?:at|of)\s+(.+)',
            r'working\s+(?:at|in)\s+(.+)',
        ],
        'search_by_batch': [
            r'batch\s+(\d{4})',
            r'(\d{4})\s+batch',
            r'from\s+(\d{4})',
            r'graduated?\s+(?:in\s+)?(\d{4})',
        ],
        'search_by_location': [
            r'in\s+([a-zA-Z\s]+)',
            r'based\s+in\s+([a-zA-Z\s]+)',
            r'located?\s+in\s+([a-zA-Z\s]+)',
        ],
        'search_by_designation': [
            r'(?:find|list|show)\s+(.+?)s?\s+(?:at|in|from)',
            r'who\s+(?:are|is)\s+(.+)',
        ],
        'search_by_name': [
            r'find\s+(.+)',
            r'search\s+for\s+(.+)',
            r'looking\s+for\s+(.+)',
        ],
    }
    
    @classmethod
    def parse(cls, query: str) -> Tuple[str, Dict[str, str]]:
        """
        Parse query and return intent and extracted parameters.
        
        Returns:
            Tuple of (intent, parameters)
        """
        query_lower = query.lower().strip()
        
        for intent, patterns in cls.INTENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, query_lower)
                if match:
                    value = match.group(1).strip().rstrip('?.,!')
                    
                    param_key = intent.replace('search_by_', '')
                    return intent, {param_key: value}
        
        # Default to name search if no pattern matches
        return 'search_by_name', {'name': query.strip()}
