import sys
sys.path.append('/www/alpha')

import inspect
import time
import django_rq
from collections.abc import Iterable
from functools import wraps
from typing import Callable, Any, Optional, AsyncGenerator
from icecream import ic

from apps.rubicon_v3.__function.__log import append_module_log


def _serialize_value(value, module_name, param_name):
    """
    Helper function to safely serialize values including Django models,
    with module-specific and parameter-specific truncation
    """
    import copy
    from django.db import models
    from pydantic import BaseModel
    
    def truncate_based_on_module_and_param(value):
        """Helper function to truncate specific module and parameter outputs"""
        if not module_name:
            return value
        # Process query case - truncate DataFrame records
        elif module_name == "process_query" and param_name == "result" and isinstance(value, list):
            value_copy = copy.deepcopy(value)  # Make a deep copy
            return value_copy[:5]
        # DataFrame records input case - truncate records
        elif module_name == "check_structured_rag" and param_name == "structured_rag_data" and isinstance(value, list):
            value_copy = copy.deepcopy(value)  # Make a deep copy
            return [sublist[:5] if isinstance(sublist, list) and sublist and isinstance(sublist[0], dict) else sublist for sublist in value_copy]
        # Resolve query data case - truncate DataFrame records inside dict values
        elif module_name == "resolve_query_data" and param_name == "query_data" and isinstance(value, dict) and "structured_query_data" in value:
            value_copy = copy.deepcopy(value)  # Make a deep copy
            data = value_copy["structured_query_data"]
            value_copy["structured_query_data"] = [{k: v[:5] if isinstance(v, list) and v and isinstance(v[0], dict) else v 
                                                for k, v in item.items()} 
                                                for item in data]
            return value_copy
        # OpenAI embedding case - truncate embeddings
        elif module_name == "baai_embedding" and param_name == "result" and isinstance(value, list):
            value_copy = copy.deepcopy(value)  # Make a deep copy
            return value_copy[:5]
        elif param_name in ['re_written_query_embedding', 'embeddings', 'embedding', 'filtered_embedded_queries', 'pq_fewshot_vector'] and isinstance(value, list):
            value_copy = copy.deepcopy(value)  # Make a deep copy
            return value_copy[:5]
            
        return value

    # First try to truncate the input value
    truncated_value = truncate_based_on_module_and_param(value)
    
    # Then serialize the truncated value
    if isinstance(truncated_value, (str, int, float, bool, type(None))):
        return truncated_value
    elif isinstance(truncated_value, BaseModel):
        return _serialize_value(truncated_value.model_dump(), module_name, param_name)
    elif isinstance(truncated_value, dict):
        return {k: _serialize_value(v, module_name, param_name) for k, v in truncated_value.items()}
    elif isinstance(truncated_value, models.Model):
        return {
            'model_type': truncated_value.__class__.__name__,
            'pk': truncated_value.pk,
            'str_repr': str(truncated_value)
        }
    elif isinstance(truncated_value, Iterable) and not isinstance(truncated_value, (str, bytes)):
        try:
            return [_serialize_value(item, module_name, param_name) for item in truncated_value]
        except TypeError:
            return str(truncated_value)
    else:
        try:
            return str(truncated_value)
        except Exception as e:
            return f"<Unserializable object of type {type(truncated_value).__name__}>"


def module_logger(message_id_param: str, module_name: str):
    """
    Decorator for logging function execution. Can handle both async and sync functions.
    
    Args:
        message_id_param (str): Name of the parameter that contains the message_id
        module_name (str): Name of the module/section in the pipeline
    """
    def decorator(func: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(func)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Start function timer
            function_start_time = time.time()
            
            # Get function parameter names
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Extract message_id from args/kwargs
            message_id = bound_args.arguments.get(message_id_param)
            if not message_id:
                raise ValueError(f"Required parameter '{message_id_param}' not found in function call")

            # Get pipeline_start_time from function parameters if it exists
            pipeline_start_time = bound_args.arguments.get('pipeline_start_time')
            
            # Convert function inputs to list format
            function_input = []
            for param_name, param_value in bound_args.arguments.items():
                if param_name != 'self':
                    function_input.append({
                        "parameter": param_name,
                        "value": _serialize_value(param_value, module_name, param_name)
                    })

            try:
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Calculate timing metrics
                function_end_time = time.time()
                function_time = function_end_time - function_start_time
                
                total_elapsed_time = None
                if pipeline_start_time is not None:
                    total_elapsed_time = function_end_time - pipeline_start_time
                
                # Convert function output
                if isinstance(result, dict):
                    function_output = [{"value": _serialize_value(result, module_name, "result")}]
                elif isinstance(result, (str, int, float, bool, type(None))):
                    function_output = [{"value": result}]
                elif isinstance(result, Iterable) and not isinstance(result, str):
                    function_output = [{"value": _serialize_value(list(result), module_name, "result")}]
                else:
                    function_output = [{"value": _serialize_value(result, module_name, "result")}]
                
                # Check if this is an LLM call
                is_llm_call = 'model_name' in bound_args.arguments
                
                if is_llm_call:
                    llm_input = {
                        "messages": bound_args.arguments.get('messages'),
                        "temperature": bound_args.arguments.get('temperature', None),
                        "stream": False
                    }
                    django_rq.enqueue(
                        append_module_log, 
                        message_id=message_id,
                        module=module_name,
                        function_input=function_input,
                        function_output=function_output,
                        llm_model=bound_args.arguments['model_name'],
                        llm_input=llm_input,
                        llm_output=result,
                        error=None,
                        function_time=function_time,
                        total_elapsed_time=total_elapsed_time
                    )       
                    # append_module_log(
                    #     message_id=message_id,
                    #     module=module_name,
                    #     function_input=function_input,
                    #     function_output=function_output,
                    #     llm_model=bound_args.arguments['model_name'],
                    #     llm_input=llm_input,
                    #     llm_output=result,
                    #     error=None,
                    #     function_time=function_time,
                    #     total_elapsed_time=total_elapsed_time
                    # )
                else:
                    django_rq.enqueue(
                        append_module_log, 
                        message_id=message_id,
                        module=module_name,
                        function_input=function_input,
                        function_output=function_output,
                        error=None,
                        function_time=function_time,
                        total_elapsed_time=total_elapsed_time
                    )
                    # append_module_log(
                    #     message_id=message_id,
                    #     module=module_name,
                    #     function_input=function_input,
                    #     function_output=function_output,
                    #     error=None,
                    #     function_time=function_time,
                    #     total_elapsed_time=total_elapsed_time
                    # )
                
                return result
                
            except Exception as e:
                function_end_time = time.time()
                function_time = function_end_time - function_start_time
                
                total_elapsed_time = None
                if pipeline_start_time is not None:
                    total_elapsed_time = function_end_time - pipeline_start_time
                
                llm_input = None
                if 'model_name' in bound_args.arguments:
                    llm_input = {
                        "messages": bound_args.arguments.get('messages'),
                        "temperature": bound_args.arguments.get('temperature', None),
                        "stream": False
                    }
                
                append_module_log(
                    message_id=message_id,
                    module=module_name,
                    function_input=function_input,
                    function_output=[],
                    llm_model=bound_args.arguments.get('model_name'),
                    llm_input=llm_input,
                    llm_output=None,
                    error=str(e),
                    function_time=function_time,
                    total_elapsed_time=total_elapsed_time
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Start function timer
            function_start_time = time.time()
            
            # Get function parameter names
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Extract message_id from args/kwargs
            message_id = bound_args.arguments.get(message_id_param)
            if not message_id:
                raise ValueError(f"Required parameter '{message_id_param}' not found in function call")

            # Get pipeline_start_time from function parameters if it exists
            pipeline_start_time = bound_args.arguments.get('pipeline_start_time')
            
            # Convert function inputs to list format
            function_input = []
            for param_name, param_value in bound_args.arguments.items():
                if param_name != 'self':
                    function_input.append({
                        "parameter": param_name,
                        "value": _serialize_value(param_value, module_name, param_name)
                    })

            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Calculate timing metrics
                function_end_time = time.time()
                function_time = function_end_time - function_start_time
                
                total_elapsed_time = None
                if pipeline_start_time is not None:
                    total_elapsed_time = function_end_time - pipeline_start_time
                
                # Convert function output
                if isinstance(result, dict):
                    function_output = [{"value": _serialize_value(result, module_name, "result")}]
                elif isinstance(result, (str, int, float, bool, type(None))):
                    function_output = [{"value": result}]
                elif isinstance(result, Iterable) and not isinstance(result, str):
                    function_output = [{"value": _serialize_value(list(result), module_name, "result")}]
                else:
                    function_output = [{"value": _serialize_value(result, module_name, "result")}]
                
                # Check if this is an LLM call
                is_llm_call = 'model_name' in bound_args.arguments
                
                if is_llm_call:
                    llm_input = {
                        "messages": bound_args.arguments.get('prompt'),
                        "temperature": bound_args.arguments.get('temperature', None),
                        "stream": False
                    }
                    
                    append_module_log(
                        message_id=message_id,
                        module=module_name,
                        function_input=function_input,
                        function_output=function_output,
                        llm_model=bound_args.arguments['model_name'],
                        llm_input=llm_input,
                        llm_output=result,
                        error=None,
                        function_time=function_time,
                        total_elapsed_time=total_elapsed_time
                    )
                else:
                    append_module_log(
                        message_id=message_id,
                        module=module_name,
                        function_input=function_input,
                        function_output=function_output,
                        error=None,
                        function_time=function_time,
                        total_elapsed_time=total_elapsed_time
                    )
                
                return result
                
            except Exception as e:
                function_end_time = time.time()
                function_time = function_end_time - function_start_time
                
                total_elapsed_time = None
                if pipeline_start_time is not None:
                    total_elapsed_time = function_end_time - pipeline_start_time
                
                llm_input = None
                if 'model_name' in bound_args.arguments:
                    llm_input = {
                        "prompt": bound_args.arguments.get('prompt'),
                        "temperature": bound_args.arguments.get('temperature', None),
                        "stream": False
                    }
                
                append_module_log(
                    message_id=message_id,
                    module=module_name,
                    function_input=function_input,
                    function_output=[],
                    llm_model=bound_args.arguments.get('model_name'),
                    llm_input=llm_input,
                    llm_output=None,
                    error=str(e),
                    function_time=function_time,
                    total_elapsed_time=total_elapsed_time
                )
                raise

        return async_wrapper if is_async else sync_wrapper
    return decorator


def streaming_module_logger(message_id_param: str, module_name: str):
    """
    Simplified decorator for logging OpenAI streaming function execution.
    Specifically designed for open_ai_call_stream function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Start function timer
            function_start_time = time.time()
            
            # Get function parameter names
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Extract key parameters
            message_id = bound_args.arguments.get(message_id_param)
            pipeline_start_time = bound_args.arguments.get('pipeline_start_time')

            # Convert function inputs to list format
            function_input = []
            for param_name, param_value in bound_args.arguments.items():
                if param_name != 'self':
                    function_input.append({
                        "parameter": param_name,
                        "value": _serialize_value(param_value, module_name, param_name)
                    })
            
            try:
                # Execute the function - don't await it since it's an async generator
                result_generator = func(*args, **kwargs)
                
                # For streaming responses, collect while yielding
                full_response = ""
                async for chunk in result_generator:
                    full_response += chunk
                    yield chunk
                
                # Calculate timing metrics
                function_end_time = time.time()
                function_time = function_end_time - function_start_time
                total_elapsed_time = function_end_time - pipeline_start_time if pipeline_start_time else None

                llm_input = {
                    "messages": bound_args.arguments.get('messages'),
                    "temperature": bound_args.arguments.get('temperature', None),
                    "stream": True
                }

                # Log completion
                append_module_log(
                    message_id=message_id,
                    module=module_name,
                    function_input=function_input,
                    function_output=[{"value": full_response}],
                    llm_model=bound_args.arguments['model_name'],
                    llm_input=llm_input,
                    llm_output=full_response,
                    error=None,
                    function_time=function_time,
                    total_elapsed_time=total_elapsed_time
                )
                
            except Exception as e:
                # Calculate timing for error case
                function_end_time = time.time()
                function_time = function_end_time - function_start_time
                total_elapsed_time = function_end_time - pipeline_start_time if pipeline_start_time else None
                
                llm_input = {
                    "messages": bound_args.arguments.get('messages'),
                    "temperature": bound_args.arguments.get('temperature', None),
                    "stream": True
                }

                # Log error
                append_module_log(
                    message_id=message_id,
                    module=module_name,
                    function_input=function_input,
                    function_output=[],
                    llm_model=bound_args.arguments['model_name'],
                    llm_input=llm_input,
                    llm_output=None,
                    error=str(e),
                    function_time=function_time,
                    total_elapsed_time=total_elapsed_time
                )
                raise

        return wrapper
    return decorator