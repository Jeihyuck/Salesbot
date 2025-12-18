import sys

sys.path.append("/www/alpha/")

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "alpha.settings")
django.setup()

import asyncio
import re

from typing import List
from datetime import datetime
from pydantic import BaseModel

from apps.rubicon_v3.models import Managed_Word, Prompt_Template
from apps.rubicon_v3.__function import __llm_call, __utils


class ReWriteQuery(BaseModel):
    re_write_query_list: List[str]
    re_write_keyword_list: List[str]

LANG_DICT = {"KR": "Korean", "GB": "English"}
TODAY_ISO_DATE_STR = datetime.now().strftime('%Y-%m-%d') # ISO 8601 format (e.g., "2025-06-05")
THIS_YEAR_STR = str(datetime.now().year) # e.g., "2025"
LAST_YEAR_STR = str(datetime.now().year - 1) # e.g., "2024"


def re_write_history(
    original_query: str,
    files: list,
    message_history: list,
    mentioned_products: list,
    channel: str,
    country_code: str,
    gpt_model_name: str = "gpt-4.1",
    temperature: float = 0.0,
    top_p: float = 0.1,
):
    """
    Function to process and clearly rewrite the user's query.
    :param original_query: The main query
    :param files: List of files
    :param message_history: List of message history
    :param channel: Channel name
    :param country_code: Country code
    :param gpt_model_name: Model name (default: gpt-4.1)
    :param temperature: Temperature for the model (default: 0.0)
    :param top_p: Top-p sampling parameter (default: 0.1)
    :return: Response object
    """
    
    # Default to English if not found.
    language = LANG_DICT.get(country_code, "English")

    # Fetch replacement words from the database based on the channel
    replace_words = list(
        Managed_Word.objects
        .filter(active=True, module="RE-WRITE", processing="replace", channel__contains=[channel])
        .values("word", "replace_word")
    )
    for rw in replace_words:
        # IMPORTANT: If the word requires word boundary pattern, add '\b' in 'rubicon_v3_managed_word'
        word_pattern = rw["word"]
        # Use re.sub to replace all occurrences of the word with the replacement word
        original_query = re.sub(word_pattern, rw["replace_word"], original_query, flags=re.IGNORECASE)

    # Mentioned products are from product card (extended_info_result by default, or product extraction) 
    mentioned_products_str = ",".join(p.get("code", "") for p in mentioned_products)
    
    # Not using early-exit block for now
    early_exit_block_content = ""

    # Load the prompt template from the database
    tmpl = Prompt_Template.objects.filter(
        response_type="rewrite", active=True, country_code=country_code
    ).values_list("prompt", flat=True)[0]
    
    # Prepare the prompt with dynamic values
    prompt_template_values = {
        'early_exit_block_placeholder': early_exit_block_content,
        'today_iso_date_placeholder': TODAY_ISO_DATE_STR,
        'this_year_placeholder': THIS_YEAR_STR,
        'last_year_placeholder': LAST_YEAR_STR,
        'mentioned_products_placeholder': mentioned_products_str,
        'language_placeholder': language,
        'language_placeholder_2': language
    }
    prompt = tmpl % prompt_template_values

    # Initialize messages with the system prompt
    messages = [{"role": "system", "content": prompt}]
    messages.extend(message_history)

    # Collect all successfully processed images
    processed_images = []
    for file in files:
        try:
            image_dict = __utils.process_image_file(file)
            processed_images.append(image_dict)
        except Exception as e:
            print(f"Error processing image {file.name}: {str(e)}")
            continue

    # Create user message including images and text
    user_content = []

    # Add images first if they exist
    if processed_images:
        user_content.extend(processed_images)

    # Add text content
    user_content.append(
        {"type": "text", "text": f"{original_query}"}
    )

    # Add the completed user message
    messages.append({"role": "user", "content": user_content})

    # Call the LLM with structured response
    response = __llm_call.open_ai_call_structured(
        gpt_model_name, messages, ReWriteQuery, temperature, top_p, 42
    )

    return response


async def main():
    input_list = """can i buy s25 in here?""".strip().split("\n")
    files = ""
    message_history = []
    mentioned_products = []

    for input_query in input_list:
        input_query=input_query.strip()
        response = re_write_history(
            input_query,
            files,
            message_history,
            mentioned_products,
            gpt_model_name="gpt-4.1",
            country_code="GB",
            channel = 'Retail_KX'
        )
        print(f" >>> {response}")

       
if __name__ == "__main__":
    asyncio.run(main())