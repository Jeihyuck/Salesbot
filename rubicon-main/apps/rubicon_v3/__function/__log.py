import sys
sys.path.append("/www/alpha/")

import tiktoken
from datetime import datetime
from typing import Dict, Any
from icecream import ic

from alpha._db import chat_log_collection


def create_message_log (
    channel: str,
    country_code: str,
    user_id: str,
    department: str,
    session_id: str,
    message_id: str,
    message_history: list,
    message: dict,
) -> None:
    print('create_message_log')
    message_init_log = {
        "channel": channel,
        "country_code": country_code,
        "user_id": user_id,
        "department": department,
        "session_id": session_id,
        "message_id": message_id,
        "message_history": message_history,
        "message": message,
        "log": [
        ],
        "appraisal" : {},
        "created_on": datetime.now()
    }
    # chat_log_collection.insert_one(message_init_log)


def extract_message_text(content) -> str:
    """
    Extracts text content from a message, handling both simple text and structured content.
    
    Args:
        content: Message content which can be a string, list, or dict
    
    Returns:
        str: Extracted text content
    """
    # If content is a string, return it directly
    if isinstance(content, str):
        return content
        
    # If content is a list, process each item
    if isinstance(content, list):
        text_parts = []
        for item in content:
            # Recursively process list items
            if isinstance(item, (dict, list)):
                text_parts.append(extract_message_text(item))
            elif isinstance(item, str):
                text_parts.append(item)
        return " ".join(filter(None, text_parts))
        
    # If content is a dict (single content item)
    if isinstance(content, dict):
        if content.get("type") == "text" and "text" in content:
            return content["text"]
            
    return ""


def count_tokens(sentence: str, model: str = "gpt-4") -> int:
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(sentence)
    return len(tokens)


def append_module_log (
    message_id: str,
    module: str,
    function_input: list,
    function_output: list,
    function_time: float,
    total_elapsed_time: float = None,
    llm_model: str = None,
    llm_input: Dict[str, Any] = None,
    llm_output: str = None,
    cache: bool = False,
    error: str = None,
) -> None:
    return ### added in 12.20
    module_log = {
        "module": module,
        "function": {
            "input":  function_input,
            "output": function_output,
            "time":   function_time,
        },
        "error": error,
        "created_on": datetime.now()
    }
    
    if llm_model is not None and llm_input is not None:
        total_input = ""
        # llm_input is a dict with a 'messages' key that contains a list
        if "messages" in llm_input:
            for message in llm_input["messages"]:
                if "content" in message:  # content might be a list of dicts
                    message_text = extract_message_text(message["content"])
                    total_input += message_text + " "
        
        module_log['llm'] = {
            "model":  llm_model,
            "input":  llm_input,
            "output": llm_output,
            "input_token": count_tokens(total_input, model=llm_model),
            "output_token": count_tokens(str(llm_output), model=llm_model),  
        }
    if total_elapsed_time != None:
        module_log['total_elapsed_time'] = total_elapsed_time

    # chat_log_collection.update_one({'message_id': message_id}, {'$push': {'log': module_log}})
