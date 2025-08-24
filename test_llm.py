#!/usr/bin/env python3
"""
Test script for LLM-enhanced analysis functionality
"""

import os
from dotenv import load_dotenv
from src.tools.llm_analyzer import LLMAnalyzer

def test_llm_analyzer():
    """Test the LLM analyzer functionality"""
    
    # Load environment variables
    load_dotenv()
    
    # Check if OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  No OpenAI API key found. Set OPENAI_API_KEY in .env file")
        print("   The system will fall back to basic analysis mode.")
        return
    
    print("🔑 OpenAI API key found. Testing LLM integration...")
    
    # Create LLM analyzer
    llm = LLMAnalyzer(api_key=api_key)
    
    # Test with sample data
    sample_context = {
        "profile": {
            "sector": "Technology",
            "longBusinessSummary": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide."
        },
        "facts": {
            "fcf_yield_ttm": 0.0281,
            "roic_est": 2.0539,
            "gross_margin": 0.4668,
            "operating_margin": 0.2999,
            "debt_to_equity": None
        },
        "risk_items": [
            "Foreign exchange rate fluctuations may impact margins",
            "Supply chain disruptions could affect production",
            "Intense competition in consumer electronics market"
        ]
    }
    
    # Test checklist analysis
    checklist_items = [
        "Moat: network effects / switching costs / data advantage?",
        "Unit economics: gross margin path vs R&D/S&M intensity"
    ]
    
    print("\n🧪 Testing LLM analysis for AAPL...")
    print("=" * 50)
    
    try:
        analyses = llm.analyze_sector_checklist("AAPL", checklist_items, sample_context)
        
        for i, analysis in enumerate(analyses, 1):
            print(f"\n📋 Analysis {i}:")
            print(analysis)
            print("-" * 30)
            
    except Exception as e:
        print(f"❌ LLM analysis failed: {str(e)}")
        print("   This might be due to API rate limits or network issues.")

if __name__ == "__main__":
    test_llm_analyzer()
