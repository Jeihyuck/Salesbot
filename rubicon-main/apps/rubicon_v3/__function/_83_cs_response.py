import sys

sys.path.append("/www/alpha/")

from apps.rubicon_v3.__function.__simulate_stream import stream_markdown
from apps.rubicon_v3.__function._80_response import response
from apps.rubicon_v3.__function.__exceptions import (
    EmptyStreamData,
    ResponseGenerationFailureException,
)
from apps.rubicon_v3.__external_api._04_cs_ai_agent import cs_ai_agent_stream


def cs_mixed_response(
    cs_data_dict: dict,
    data_dict,
    sys_prompt,
    response_path,
    model_name,
    temperature,
    seed,
    web_links=None,
):
    """
    Function to handle cs related queries using the CS AI AGENT and combine the response with rubicon response.
    """
    stream_data = ""
    # First stream the cs_result using the stream markdown function
    for cs_result in cs_data_dict.values():
        if cs_result.get("response"):
            stream_data += "\n\n" + cs_result["response"]

    # Check if the stream data is empty
    if not stream_data.strip():
        raise EmptyStreamData("CS AI Agent returned empty stream data.")

    for cs_chunk in stream_markdown(stream_data.strip()):
        yield cs_chunk

    # Yield a separator between the two responses
    yield "\n\n"
    yield "\n\n"

    # Then stream the rest of the response
    for chunk in response(
        data_dict,
        sys_prompt,
        response_path,
        model_name,
        temperature,
        seed,
        web_links,
    ):
        yield chunk


def cs_stream_response(data_dict: dict):
    """
    Function to get the CS AI AGENT response in streaming mode.
    """
    # Get the original query and message history
    query = data_dict.get("original_query", "")
    message_history = data_dict.get("message_history", [])

    # Get the CS AI AGENT response in streaming mode
    try:
        for cs_chunk in cs_ai_agent_stream(query, message_history):
            yield cs_chunk

    except Exception as e:
        # Re-raise as a custom exception
        raise ResponseGenerationFailureException(
            f"Error during CS AI Agent streaming: {str(e)}"
        ) from e


if __name__ == "__main__":
    query = "핸드폰이 안되요"
    message_history = []
    for chunk in cs_ai_agent_stream(query, message_history):
        print(chunk, end="", flush=True)