import sys

sys.path.append("/www/alpha/")

from apps.rubicon_v3.__function import _82_response_prompts, __utils
from apps.rubicon_v3.__function.__llm_call import open_ai_call_stream
from apps.rubicon_v3.__function._80_stream_moderator import ModeratedStream
from apps.rubicon_v3.__function.definitions import response_types
from apps.rubicon_v3.models import Disclaimer_Msg


def response(
    data_dict,
    sys_prompt,
    response_path,
    model_name,
    temperature,
    seed,
    web_links=None,
):
    # Use only the data for the response_path
    input_data_info = _82_response_prompts.input_prompt_data_mapping.get(response_path)

    if not input_data_info:
        raise ValueError(f"No input data mapping for response path: {response_path}")

    open_ai_input_data = {}
    for data in input_data_info.get("open_ai_inputs", []):
        if data_dict.get(data) is not None:
            open_ai_input_data[data] = data_dict.get(data)
        else:
            raise ValueError(
                f"Necessary open ai input for {response_path}: {data} is missing"
            )

    prompt_input_data = {}
    for data in input_data_info.get("prompt_inputs", []):
        if data_dict.get(data) is not None:
            prompt_input_data[data] = data_dict.get(data)
        else:
            raise ValueError(
                f"Necessary prompt input for {response_path}: {data} is missing"
            )

    # Generate Input Prompt
    input_prompt = _82_response_prompts.dict_to_multiline_comment(prompt_input_data)

    # Initialize messages with system prompt
    messages = [{"role": "system", "content": [{"type": "text", "text": sys_prompt}]}]

    # Add Message History If Available # Disable message history for informative response
    if open_ai_input_data.get("message_history"):
        # Add message history
        for message in open_ai_input_data["message_history"]:
            if response_path != response_types.INFORMATIVE_RESPONSE:
                messages.append(message)
            else:
                # Truncate the content of the message to 100 for Korean, and 200 for other languages
                if message["role"] == "user":
                    continue
                if data_dict["output_language"] == "Korean":
                    message["content"] = message["content"][:100] + "..."
                else:
                    message["content"] = message["content"][:200] + "..."
                messages.append(message)

    # Image Files If Available
    processed_images = None
    if open_ai_input_data.get("image_files"):
        # 성공적으로 처리된 모든 이미지를 수집
        processed_images = []
        for file in open_ai_input_data["image_files"]:
            try:
                image_dict = __utils.process_image_file(file)
                processed_images.append(image_dict)
            except Exception as e:
                print(f"Error processing image {file.name}: {str(e)}")
                continue

    # Add Input Prompt If Available
    if input_prompt:
        messages.append(
            {
                "role": "system",
                "content": [{"type": "text", "text": input_prompt + "\n[DATA-END]"}],
            }
        )

    # User Content If Available
    if open_ai_input_data.get("user_query"):
        user_content = []

        # Add files if available
        if processed_images:
            user_content.extend(processed_images)

        # Add user input
        user_prompt = f"""{open_ai_input_data["user_query"]}"""
        user_content.append({"type": "text", "text": user_prompt})

        # Add user content to messages
        messages.append({"role": "user", "content": user_content})

    if open_ai_input_data.get("original_query"):
        user_content = []

        # Add files if available
        if processed_images:
            user_content.extend(processed_images)

        # Add user input
        user_prompt = f"""{open_ai_input_data["original_query"]}"""
        user_content.append({"type": "text", "text": user_prompt})

        # Add user content to messages
        messages.append({"role": "user", "content": user_content})

    # Get the disclaimer message
    disclaimer_msg = (
        Disclaimer_Msg.objects.filter(
            channel__contains=[data_dict.get("channel", "")],
            intelligence__contains=data_dict.get("intelligence_info", []),
            sub_intelligence__contains=data_dict.get("sub_intelligence_info", []),
            country_code=data_dict.get("country_code", ""),
        )
        .values_list("message", flat=True)
        .first()
    )

    # If no disclaimer message is found, use the default one (This may still be None)
    if not disclaimer_msg:
        disclaimer_msg = (
            Disclaimer_Msg.objects.filter(
                channel__isnull=True,
                intelligence__contains=data_dict.get("intelligence_info", []),
                sub_intelligence__contains=data_dict.get("sub_intelligence_info", []),
                country_code__isnull=True,
            )
            .values_list("message", flat=True)
            .first()
        )

    # Initialize the ModeratedStream
    stream = ModeratedStream(
        sys_prompt,
        language=data_dict["output_language"],
        country_code=data_dict["original_country_code"],
        gpt_model=model_name,
        temperature=temperature,
        seed=seed,
    )

    # Call OpenAI with Moderation
    for chunk in stream.stream_gpt_response(messages):
        yield chunk

    # If the stream is not terminated, continue to generate the additional information
    if (
        chunk.startswith("\n[STREAM TERMINATED:") == False
        or chunk.startswith("\n[STREAM ERROR:") == False
    ):
        # Only generate additional information if the response path is informative
        if response_path == response_types.INFORMATIVE_RESPONSE:
            # Generate the web links if applicable
            if web_links and isinstance(web_links, list):
                yield "\n\n"

                # Yield each web link (already formatted as markdown)
                if len(web_links) == 1:
                    yield web_links[0]
                else:
                    for web_link in web_links[:-1]:
                        yield f"{web_link}\n\n"
                    yield web_links[-1]

            # Generate the disclaimer if applicable
            if disclaimer_msg:
                yield "\n\n"

                # Call OpenAI
                for chunk in open_ai_call_stream(
                    model_name=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"""
Generate the text below in {data_dict['output_language']}. Return only the text below and do NOT add any other words under any circumstances.

{disclaimer_msg}
""",
                                }
                            ],
                        }
                    ],
                    temperature=temperature,
                    seed=seed,
                    stream=True,
                ):
                    yield chunk
