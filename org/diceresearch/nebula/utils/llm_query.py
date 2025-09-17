

from openai import OpenAI
import logging
import settings

#https://dice-llm-chat.cs.uni-paderborn.de/ollama/http://tentris-ml.cs.upb.de:8000/api/generate llama3.3:70b
class LLMQueryClass:
    def __init__(self):
        logging("starting LLM request.")


    def get_article_verdict(self, claim_verdicts: dict, article_text: str = ""):
        """
        :param claim_verdicts: dict where key = claim string, value = "TRUE" or "FALSE"
        :param article_title: optional, just for logging/context
        :return: final news decision: RELIABLE / UNRELIABLE / MIXED
        """
        MODEL_ID = settings.MODEL_NAME
        OPAI_CLIENT = OpenAI(base_url=settings.BASE_LLM_URL, api_key=settings.LLM_API_KEY)

        sys_prompt = (
            "You are verifying news article reliability.\n"
            "You will be given a set of claims from a news article and their evidence verdicts "
            "(TRUE or FALSE or NOT ENOUGH INFO). Use only those verdicts, no other knowledge.\n"
            "\n"
            "Decision rules:\n"
            "- If the majority of claims are TRUE, output 'RELIABLE'.\n"
            "- If the majority are FALSE, output 'UNRELIABLE'.\n"
            "- If it is a mixture (no clear majority or close tie), output 'MIXED'.\n"
            "- Do not output explanations or any other text. Only 'RELIABLE', 'UNRELIABLE', or 'MIXED'.\n"
            "Return only one label: RELIABLE, UNRELIABLE, or MIXED.\n"
        )

        # Format claims + verdicts for input
        verdicts_text = "\n".join([f"- Claim: {c}\n  Verdict: {v}" for c, v in claim_verdicts.items()])

        prompt = (
            f"Claim verdicts:\n{verdicts_text}\n\n"
            f"Article: {article_text}\n\n"
            "Final Decision:"
        )

        completion = OPAI_CLIENT.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt},
            ],
        )

        result = completion.choices[0].message.content.strip()
        logging.info(f"Final decision for article '{article_text}': {result}")
        return result

    def get_single_claim_classification_response_from_api_call(self, summaries: list, claim: str):
        """
        :param summaries: List of summaries (strings), typically 10
        :param claim: The claim to verify (string)
        :return: "TRUE" or "FALSE"
        """
        MODEL_ID = settings.MODEL_NAME
        OPAI_CLIENT = OpenAI(base_url=settings.BASE_LLM_URL, api_key=settings.LLM_API_KEY)

        # New system prompt for claim verification from multiple summaries
        sys_prompt = (
            "You are performing claim verification.\n"
            "You are given a claim and multiple summaries of texts. "
            "Each summary may support the claim or refute it.\n"
            "Your task is to decide if the claim is TRUE, FALSE or NOT ENOUGH INFORMATION available for this task, "
            "based only on the summaries provided (no outside knowledge).\n"
            "\n"
            "Decision rules:\n"
            "- If the majority of summaries clearly support the claim, output ONLY 'TRUE'.\n"
            "- If the majority clearly contradict or refute the claim, output ONLY 'FALSE'.\n"
            "- If NONE of the summaries support or refute the claim, output ONLY 'NOT ENOUGH INFO'.\n"
            "- Do not output explanations or any other text. Only 'TRUE', 'FALSE' or 'NOT ENOUGH INFO'.\n'."
        )

        # Format the summaries clearly
        summaries_text = "\n".join([f"{i + 1}. {s}" for i, s in enumerate(summaries)])

        # User prompt
        prompt = (
            f"Claim: {claim}\n\n"
            f"Summaries:\n{summaries_text}\n\n"
            "Answer:"
        )

        completion = OPAI_CLIENT.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt},
            ],
        )

        result = completion.choices[0].message.content.strip()
        logging.info(result)
        return result


    def get_coref_res_from_api_call(self, text: str):
        """
        :param summaries: List of summaries (strings), typically 10
        :param claim: The claim to verify (string)
        :return: "TRUE" or "FALSE"
        """
        MODEL_ID = settings.MODEL_NAME
        OPAI_CLIENT = OpenAI(base_url=settings.BASE_LLM_URL, api_key=settings.LLM_API_KEY)

        # New system prompt for claim verification from multiple summaries
        system_prompt = """You are a text transformation system that performs coreference resolution.
        Your task: Replace pronouns and ambiguous references with explicit entity names.
        Rules:
        1. Do NOT remove any information.
        2. Do NOT add any external information.
        3. Keep the original sentences, order, and formatting intact.
        4. Only adjust references (he, she, his, they, their, it, the man, etc.) to the correct entity.
        5. You may clean the text and remove unnecessary whitespace or URLs.
        6. Do not start with something like: 'Here is the text with coreference resolution applied:'. Start directly with output."""

        # Format the summaries clearly
        user_prompt = (f"Resolve coreference in the following text:\n\n{text}.\n"
                       f"Coreference text:")



        completion = OPAI_CLIENT.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        result = completion.choices[0].message.content.strip()
        logging.info(result)
        return result

    def get_response_from_api_call(self, text: str, claim: str):
        """
        :param text: textual description
        :param claim: the claim to focus the summary on
        """

        MODEL_ID = settings.MODEL_NAME
        OPAI_CLIENT = OpenAI(base_url=settings.BASE_LLM_URL, api_key=settings.LLM_API_KEY)

        # New system prompt for summarization
        sys_prompt = (
            "You are an assistant that generates concise summaries.\n"
            "Given a claim and the textual document, produce a short summary of the text "
            "that focuses only on information relevant to the claim.\n"
            "Do not include unrelated details or explanations.\n"
            "Output in the form of complete sentences.\n"
            "Output only the summary, nothing else."
        )

        # User prompt
        prompt = (
            f"Claim: {claim}\n\n"
            f"Text:\n{text}\n\n"
            "Summary:"
        )

        completion = OPAI_CLIENT.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt},
            ],
        )

        result = completion.choices[0].message.content
        logging.info(result)
        return result
