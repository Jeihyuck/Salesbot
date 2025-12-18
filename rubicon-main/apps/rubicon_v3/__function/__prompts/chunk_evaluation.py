PROMPT_TEMPLATE = """
Evaluates retrieval score for a given query and context or a multi-turn conversation, including reasoning.
The retrieval measure assesses the AI system's performance in retrieving information
for additional context (e.g. a RAG scenario).
Retrieval scores are between 1 to 5.
5 means retrieved document is relevant to the query.
1 means retrieved document does not provide any useful information to generate informative response about the query.
High retrieval scores indicate that the AI system has successfully extracted and ranked
the most relevant information at the top, without introducing bias from external knowledge
and ignoring factual correctness. Conversely, low retrieval scores suggest that the AI system
has failed to surface the most relevant context chunks at the top of the list
and/or introduced bias and ignored factual correctness.

### additional instructions
- If the response to the user's query is about a product, service, promotion that is not sold, or if the information cannot be found, you should give a score of 5.
- If the response to the user's query indicates that the product code or product name is incorrect or not exact, you should give a score of 5
- In multi-turn scenarios, if the user's query expresses a negative reaction to the response, In such cases, do not automatically assign a score of 5.
- If the AI system re-asks the user's query, you should give a score of 5.
- If the context includes a statement such as "As a Samsung AI, I cannot comment on other brands,(저는 삼성전자의 AI로서 타 브랜드의 제품에 대해 말씀드리기는 어려워요.)" do not deduct points based solely on this content. Evaluate the response based on the remaining information provided. Don't assign a score of 1 just because the response contains this statement.
- Do not give a score of 1 when the response mentions that a product, feature is not available and then provides additional information. 
  The fact that a product, feature is unavailable should not affect the evaluation itself, as this information is intended to inform the customer and ask for their understanding.
- If the response contains a phrase there are not enough reviews for the product yet, you should give a score of 5.
  (e.g., "There aren't enough reviews for the product yet, so it's difficult to provide a clear answer. Instead, let me tell you about some of the features of this product!", "제품에 대한 리뷰가 충분하지 않아 명확한 답변을 드리기 어려워요. 대신 이 제품의 특징에 대해 말씀드릴게요!")
- If the response contains the this phrase "아쉽게도 제가 답변드리기 어려운 질문이에요 you must", You should assign a score of 1. Absolutely do assign a score of 1.
- If the response only asks for patience, requests the user to wait, or suggests breaking down the question without providing any informative answer, you must assign a '-'. Do not assign a score
  (e.g., "Hello! I appreciate your patience as I work to provide you with the best possible answer. It seems that processing your question is taking a bit longer than expected. If your inquiry contains a lot of details, it might be helpful to break it down into smaller parts. Please feel free to ask me anything else in the meantime!",
          "안녕하세요. 질문에 대한 답변을 드리지 못해 죄송합니다. 현재 시스템상에서 질문을 처리하는 데 시간이 걸리고 있습니다. 더 나은 답변을 드리기 위해 노력 중이니, 혹시 질문 내에 많은 내용이 포함되어 있다면 질문을 여러 개로 나누어 시도해 보시는 것도 좋습니다. 더 궁금한 점이 있으시다면 저에게 말씀해 주세요.")
QUERY:
{query}

CONTEXT:
{context}

Respond with exactly ONE token: 1 to 5 on integer or '-'. No extra text.
""".strip()

PROMPT_TEMPLATE_SIM = """
system:
# Instruction
You are an AI assistant. You will be given the definition of an evaluation metric for assessing the quality of an answer in a question-answering task. Your job is to compute an accurate evaluation score using the provided evaluation metric. You should return a single integer value between 1 to 5 representing the evaluation metric. You will include no other text or information.
- **Data**: Your input data include QUERY, RESPONSE and GROUND_TRUTH.
- **Tasks**: To complete your evaluation you will be asked to evaluate the Data in different ways.
user:
Equivalence, as a metric, measures the similarity between the RESPONSE and the GROUND_TRUTH. If the information and content in the RESPONSE is similar or equivalent to the GROUND_TRUTH, then the value of the Equivalence metric should be high, else it should be low. Given the question, GROUND_TRUTH, and RESPONSE, determine the value of Equivalence metric using the following rating scale:
One star: the RESPONSE is not at all similar to the GROUND_TRUTH
Two stars: the RESPONSE is mostly not similar to the GROUND_TRUTH
Three stars: the RESPONSE is somewhat similar to the GROUND_TRUTH
Four stars: the RESPONSE is mostly similar to the GROUND_TRUTH
Five stars: the RESPONSE is completely similar to the GROUND_TRUTH

This rating value should always be an integer between 1 and 5. So the rating produced should be 1 or 2 or 3 or 4 or 5.

The examples below show the Equivalence score for a QUERY, a GROUND_TRUTH, and a RESPONSE.

QUERY: What is the role of ribosomes?
GROUND_TRUTH: Ribosomes are cellular structures responsible for protein synthesis. They interpret the genetic information carried by messenger RNA (mRNA) and use it to assemble amino acids into proteins.
RESPONSE: Ribosomes participate in carbohydrate breakdown by removing nutrients from complex sugar molecules.
stars: 1

QUERY: Why did the Titanic sink?
GROUND_TRUTH: The Titanic sank after it struck an iceberg during its maiden voyage in 1912. The impact caused the ship's hull to breach, allowing water to flood into the vessel. The ship's design, lifeboat shortage, and lack of timely rescue efforts contributed to the tragic loss of life.
RESPONSE: The sinking of the Titanic was a result of a large iceberg collision. This caused the ship to take on water and eventually sink, leading to the death of many passengers due to a shortage of lifeboats and insufficient rescue attempts.
stars: 2

QUERY: What causes seasons on Earth?
GROUND_TRUTH: Seasons on Earth are caused by the tilt of the Earth's axis and its revolution around the Sun. As the Earth orbits the Sun, the tilt causes different parts of the planet to receive varying amounts of sunlight, resulting in changes in temperature and weather patterns.
RESPONSE: Seasons occur because of the Earth's rotation and its elliptical orbit around the Sun. The tilt of the Earth's axis causes regions to be subjected to different sunlight intensities, which leads to temperature fluctuations and alternating weather conditions.
stars: 3

QUERY: How does photosynthesis work?
GROUND_TRUTH: Photosynthesis is a process by which green plants and some other organisms convert light energy into chemical energy. This occurs as light is absorbed by chlorophyll molecules, and then carbon dioxide and water are converted into glucose and oxygen through a series of reactions.
RESPONSE: In photosynthesis, sunlight is transformed into nutrients by plants and certain microorganisms. Light is captured by chlorophyll molecules, followed by the conversion of carbon dioxide and water into sugar and oxygen through multiple reactions.
stars: 4

QUERY: What are the health benefits of regular exercise?
GROUND_TRUTH: Regular exercise can help maintain a healthy weight, increase muscle and bone strength, and reduce the risk of chronic diseases. It also promotes mental well-being by reducing stress and improving overall mood.
RESPONSE: Routine physical activity can contribute to maintaining ideal body weight, enhancing muscle and bone strength, and preventing chronic illnesses. In addition, it supports mental health by alleviating stress and augmenting general mood.
stars: 5

QUERY: {query}
GROUND_TRUTH:{ground_truth}
RESPONSE: {response}

# Tasks
## Please provide your assessment Score for the previous RESPONSE in relation to the QUERY based on the Definitions above. Your output should include the following information:
- **Score**: based on your previous analysis, provide your Score. The Score you give MUST be a integer score (i.e., "1", "2"...) based on the levels of the definitions.
## Please provide ONE token Score: 1 to 5 on integer or '-'. No extra text.
# """.strip()