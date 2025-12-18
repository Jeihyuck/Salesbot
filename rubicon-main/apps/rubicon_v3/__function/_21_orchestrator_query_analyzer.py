import sys
import os
import django
import uuid
import asyncio
import enum
from typing import Literal, List, Optional, Tuple

# --- Setup Django environment ---
sys.path.append("/www/alpha/") 
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

from alpha import __log
from apps.rubicon_v3.models import Prompt_Template
from apps.rubicon_v3.__function import __llm_call
from pydantic import BaseModel, Field


class RAGDepth(enum.Enum):
    NONE = "None"
    DEEP = "Deep"

class QueryType(enum.Enum):
    NONE = "None"
    EXTENDED_REQUEST = "Extended Request"
    PRE_OWNED_PRODUCTS = "Pre-owned Products"
    ACCESSORIES_CONSUMABLES = "Accessories/Consumables"
    BEST_SELLING_PRODUCTS = "Best Selling Products"
    REGISTERED_PRODUCTS = "Registered Products"

# --- Pydantic Model Definition ---
class AnalyzeQuery(BaseModel):
    RAG_depth: Literal[*(e.value for e in RAGDepth)] # type: ignore
    # query_type: Literal["Extended Request", "Pre-owned Products", "Accessories/Consumables", "Best Selling Products", "Registered Products", "None"]
    query_type: List[QueryType] = Field(
        description="A list containing all applicable Query Types. Returns ['None'] if no specific type applies."
    )

# --- Main Functions ---
def get_analyzer_prompt(country_code: str) -> str:
    """Loads the corresponding prompt for the given Country Code from the DB."""
    try:
        # print(f"Loading prompt from DB for country: {country_code}")
        prompt_template = Prompt_Template.objects.get(
            response_type="query_analyzer", active=True, country_code=country_code
        )
        return prompt_template.prompt
    except Exception as e:
        __log.error(f"Error loading prompt from DB: {e}")
        raise

def query_analyzer(
        top_query: str,
        message_history: list,
        gpt_model_name: str = "gpt-4.1-mini",
        country_code: str = "KR") -> dict:
    """Performs analysis using the rewritten query and the provided prompt."""
    prompt = get_analyzer_prompt(country_code)
    messages = [{"role": "system", "content": prompt}, {"role": "user", "content": top_query}]

    response_obj = __llm_call.open_ai_call_structured(
        model_name="gpt-4.1-mini", messages=messages, temperature=0.0, top_p=0.1,
        response_format=AnalyzeQuery, seed=42
    )

    final_result ={
        "RAG_depth": response_obj["RAG_depth"],
        "query_type": [*(e.value for e in response_obj['query_type'])]
    }
    return final_result



    # return __llm_call.open_ai_call_structured(
    #     model_name=gpt_model_name, messages=messages, temperature=0.0, top_p=0.1,
    #     response_format=AnalyzeQuery, message_id=message_id,
    # )