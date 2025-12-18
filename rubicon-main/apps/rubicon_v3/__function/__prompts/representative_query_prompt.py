REPRESENTATIVE_PROMPT = """
[Task]
Create a representative question from the given examples that could be used in a Samsung Customer Service setting.

[Requirements]
- The question should be general enough to encompass all provided examples
- Maintain the same tone, formality level, and phrasing style as the original examples
- Preserve key product categories or service types mentioned in the examples
- Keep the question concise but include enough detail to be meaningful

[Style Guidelines]
- Match the linguistic style of the examples
- If examples use simple, direct language (e.g., "최신 스마트폰 추천해주세요"), keep that simplicity
- If examples use more formal phrasing, maintain that formality
- Do not change the basic sentence structure or question format used in the examples
- The question should always be formal, regardless of simplicity.

[Content Rules]
- Do not ask about product drawbacks or negative aspects
- Do not mention competitor products or brands (LG Gram, Apple iPhone)
- Write the question in the language indicated in [Target Language]

[Special Instructions]
1) Store related questions
- Must include a specific location (not generic terms like "내 근처" or "near me")
- Use the location mentioned in the provided examples if available
- If no location is provided in examples:
  * For Korean: use "강남역" (e.g., "강남역에 가까운 삼성스토어 알려줘")
  * For other languages: use "King's Cross"
- Focus only on store location, not operating hours or phone numbers

2) Product related questions:
- Include specific product names or series mentioned in the examples
- Do not use generic terms like "삼성 제품" or "Samsung products"
- Always infer the product category/name from the given examples
- If there are no specific product names that can be inferred from the examples, select a general product line from the catalog below, which is relevant to the representative question
- Here is information on Samsung's product catalog:
     - Mobile: Smartphones, Tablets, Wearables (Galaxy Watch, Buds, etc)
     - TV & Audio: TVs, Monitors, Projectors, Soundbars
     - Home Appliances: Refrigerators, Washing Machines, Dryers, Dishwashers, Ovens, Microwaves, Air Conditioners
     - Computing: Laptops, Desktops, Monitors

3) Galaxy Phone related questions:
- The Galaxy S series has only released until Galaxy S25 as of now, so do not include any Galaxy S26 or later in the representative question.
"""