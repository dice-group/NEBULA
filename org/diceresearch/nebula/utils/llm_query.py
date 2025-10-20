

# from openai import OpenAI
import logging
import settings
from vllm import LLM, SamplingParams
import os
import requests
from collections import Counter
# Declare global variable
_llm_instance = None
from transformers import AutoTokenizer

def get_llm_instance():
    global _llm_instance
    if _llm_instance is None:
        # Create it once
        _llm_instance = LLMQueryClass()
    return _llm_instance

#https://dice-llm-chat.cs.uni-paderborn.de/ollama/http://tentris-ml.cs.upb.de:8000/api/generate llama3.3:70b
class LLMQueryClass:
    def __init__(self):
        logging.info("starting LLM request.")
        self.llm = LLM(model=settings.MODEL_NAME)
        self.tokenizer = AutoTokenizer.from_pretrained(settings.MODEL_NAME)
        # Create a sampling params object.
        self.sampling_params = SamplingParams(temperature=0.0, max_tokens=10000)
        self.prompts = []



    def get_article_verdict(self, claim_verdicts: dict, article_text: str = ""):
        """
        Final news article reliability decision.
        Input: claim_verdicts = {claim_str: verdict ("TRUE", "FALSE", or "NOT ENOUGH INFO")}
        Output: "RELIABLE", "UNRELIABLE", or "MIXED"
        """
        if not claim_verdicts:
            return "MIXED"  # no claims -> can't decide

        counts = Counter(v.strip().upper() for v in claim_verdicts.values())
        true_count = counts.get("TRUE", 0)
        false_count = counts.get("FALSE", 0)
        nei_count = counts.get("NOT ENOUGH INFO", 0)

        total = true_count + false_count + nei_count

        # Decision logic
        if true_count > false_count:
            return "RELIABLE"
        elif false_count > true_count:
            return "UNRELIABLE"
        else:
            return "MIXED"

    def get_article_verdict_llm(self, claim_verdicts: dict, article_text: str = ""):
        """
        :param claim_verdicts: dict where key = claim string, value = "TRUE" or "FALSE"
        :param article_title: optional, just for logging/context
        :return: final news decision: RELIABLE / UNRELIABLE / MIXED , api_key=settings.LLM_API_KEY
        """

        # MODEL_ID = settings.MODEL_NAME
        # OPAI_CLIENT = OpenAI(base_url=settings.BASE_LLM_URL)
        #
        # system_prompt = (
        #     "You are verifying news article reliability.\n"
        #     "You will be given a set of claims from a news article and their evidence verdicts "
        #     "(TRUE or FALSE or NOT ENOUGH INFO). Use only those verdicts, no other knowledge.\n"
        #     "\n"
        #     "Decision rules:\n"
        #     "- If the majority of claims are TRUE, output 'RELIABLE'.\n"
        #     "- If the majority are FALSE, output 'UNRELIABLE'.\n"
        #     "- If most claims are NOT ENOUGH INFO, or verdicts are a mixture without a clear majority, output 'MIXED'.\n"
        #     "- Do not output explanations or any other text. Only 'RELIABLE', 'UNRELIABLE', or 'MIXED'.\n"
        #     "Return only one label: RELIABLE, UNRELIABLE, or MIXED.\n"
        # )
        system_prompt = (
            "You are an assistant evaluating the reliability of a news article.\n"
            "You will be given:\n"
            "- The article text.\n"
            "- A list of claims extracted from it, each with a veracity score "
            "(TRUE, FALSE, or NOT ENOUGH INFO).\n"
            "\n"
            "Your task:\n"
            "- Decide if the article overall is RELIABLE, UNRELIABLE, or MIXED.\n"
            "- Make this decision by considering both:\n"
            "   (1) How central each claim is to the main content/message of the article.\n"
            "   (2) The truthfulness of the central claims based on their provided veracity scores.\n"
            "\n"
            "Decision rules:\n"
            "- If the main/central claims are TRUE, and any false or uncertain claims are peripheral, output 'RELIABLE'.\n"
            "- If one or more central claims are FALSE, output 'UNRELIABLE'.\n"
            "- If the central claims are mostly NOT ENOUGH INFO, or there is a significant mix of TRUE/FALSE/NOT ENOUGH INFO "
            "verdicts across critical parts of the article, output 'MIXED'.\n"
            "\n"
            "Output format:\n"
            "- Return only one label: RELIABLE, UNRELIABLE, or MIXED.\n"
            "- Do not provide explanations or any other text.\n"
            "- Do not return None or null or any other label except one of these three: RELIABLE, UNRELIABLE, or MIXED.\n"
        )

        # Format claims + verdicts for input
        verdicts_text = "\n".join([f"- Claim: {c}\n  Verdict: {v}" for c, v in claim_verdicts.items()])

        user_prompt = (
            f"Claim verdicts:\n{verdicts_text}\n\n"
            f"Article: {article_text}\n\n"
            "Final Decision:"
        )
        outputs = self.llm.chat(
            sampling_params=self.sampling_params,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        result = outputs[0].outputs[0].text
        return result
        # return "RELIABLE"
    # def get_article_verdict(self, claim_verdicts: dict, article_text: str = ""):
    #     """
    #     :param claim_verdicts: dict where key = claim string, value = "TRUE" or "FALSE"
    #     :param article_title: optional, just for logging/context
    #     :return: final news decision: RELIABLE / UNRELIABLE / MIXED , api_key=settings.LLM_API_KEY
    #     """
    #     MODEL_ID = settings.MODEL_NAME
    #     OPAI_CLIENT = OpenAI(base_url=settings.BASE_LLM_URL)
    #
    #     sys_prompt = (
    #         "You are verifying news article reliability.\n"
    #         "You will be given a set of claims from a news article and their evidence verdicts "
    #         "(TRUE or FALSE or NOT ENOUGH INFO). Use only those verdicts, no other knowledge.\n"
    #         "\n"
    #         "Decision rules:\n"
    #         "- If the majority of claims are TRUE, output 'RELIABLE'.\n"
    #         "- If the majority are FALSE, output 'UNRELIABLE'.\n"
    #         "- If it is a mixture (no clear majority or close tie), output 'MIXED'.\n"
    #         "- Do not output explanations or any other text. Only 'RELIABLE', 'UNRELIABLE', or 'MIXED'.\n"
    #         "Return only one label: RELIABLE, UNRELIABLE, or MIXED.\n"
    #     )
    #
    #     # Format claims + verdicts for input
    #     verdicts_text = "\n".join([f"- Claim: {c}\n  Verdict: {v}" for c, v in claim_verdicts.items()])
    #
    #     prompt = (
    #         f"Claim verdicts:\n{verdicts_text}\n\n"
    #         f"Article: {article_text}\n\n"
    #         "Final Decision:"
    #     )
    #
    #     completion = OPAI_CLIENT.chat.completions.create(
    #         model=MODEL_ID,
    #         messages=[
    #             {"role": "system", "content": sys_prompt},
    #             {"role": "user", "content": prompt},
    #         ],
    #     )
    #
    #     result = completion.choices[0].message.content.strip()
    #     logging.info(f"Final decision for article '{article_text}': {result}")
    #     return result

    def get_single_claim_classification_response_from_api_call(self, summaries: list, claim: str):
        """
        Verify a claim based only on provided summaries.
        Returns: "TRUE", "FALSE", or "NOT ENOUGH INFO".
        """
        # If everything is empty: quick fallback
        if not any(s.strip() for s in summaries):
            return "NOT ENOUGH INFO"

        # system_prompt = (
        #     "You are performing claim verification.\n"
        #     "You are given a claim and multiple summaries of texts. "
        #     "Each summary may support, contradict, be neutral, or provide no information about the claim.\n"
        #     "Your task is to decide if the claim is TRUE, FALSE, or NOT ENOUGH INFO, "
        #     "based only on the summaries provided (no outside knowledge).\n"
        #     "\n"
        #     "Decision rules:\n"
        #     "- If at least one summary clearly supports the claim, and none clearly contradict it → output ONLY 'TRUE'.\n"
        #     "- If at least one summary clearly contradicts the claim, and none support it → output ONLY 'FALSE'.\n"
        #     "- If there is a mixture of supporting and contradicting evidence, or if none support/contradict → output ONLY 'NOT ENOUGH INFO'.\n"
        #     "- Do not output explanations or any other text."
        # )
        system_prompt = (
            "You are performing claim verification.\n"
            "You will be given two separate items: (1) a claim and (2) multiple summaries of texts. \n"
            "Each summary may support, contradict, be neutral, or provide no information about the claim.\n"
            "Your task is to carefully analyze the summaries and decide if the claim is TRUE, FALSE, or NOT ENOUGH INFO. \n"
            "Base your decision strictly on the provided summaries and do not rely on any outside knowledge.\n"
            "Output ONLY one of the following labels: 'TRUE', 'FALSE', or 'NOT ENOUGH INFO'. \n"
            "Do not provide explanations or any additional text  — no preamble or commentary. \n"
            "Strictly only output allowed is only one of these 3 labels: 'TRUE', 'FALSE', 'NOT ENOUGH INFO'. \n"
        )


        summaries_text = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(summaries) if s.strip())

        user_prompt = (
            f"Claim: {claim}\n\n"
            f"Summaries:\n{summaries_text}\n\n"
            "Answer:"
        )

        outputs = self.llm.chat(
            sampling_params=self.sampling_params,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        result = outputs[0].outputs[0].text.strip()
        return result
        # return "TRUE"

    def get_coref_res_from_api_call(self, text: str):
        """
        :param summaries: List of summaries (strings), typically 10
        :param claim: The claim to verify (string)
        :return: "TRUE" or "FALSE", api_key=settings.LLM_API_KEY
        """
        # MODEL_ID = settings.MODEL_NAME
        # OPAI_CLIENT = OpenAI(base_url=settings.BASE_LLM_URL)

        # url = settings.BASE_LLM_URL
        # model = settings.MODEL_NAME
        # headers = {"Content-Type": "application/json"}

        # New system prompt for claim verification from multiple summaries
        # system_prompt = """You are a text transformation system that performs coreference resolution.
        # Your task: Replace pronouns and ambiguous references with explicit entity names.
        #
        # Rules:
        # 1. Do NOT remove any information.
        # 2. Do NOT add or invent any external information not present in the text.
        # 3. Keep the original sentences, order, and formatting intact.
        # 4. Replace pronouns (he, she, his, they, their, it, etc.) AND vague role-based or nominal references
        #    (e.g., "the man", "the woman", "the professor", "the director") with the correct explicit entity name
        #    when that entity is identifiable in the text.
        # 5. If a noun phrase is generic and not clearly referring to a specific entity, leave it unchanged.
        # 6. You may clean the text and remove unnecessary whitespaces, new lines, or URLs.
        # 7. Do not provide explanations, summaries, or lists of replacements made.
        # 8. Output only the transformed text — no preamble or commentary."""
        #
        # # Format the summaries clearly
        # user_prompt = (f"Resolve coreference in the following text:\n\n{text}.\n"
        #                f"Resolved text:")
        system_prompt = """You are a text-transformation system that performs COMPLETE coreference resolution.
            Make every reference explicit so each sentence is unambiguous and self-contained with STRICTLY NO PRONOUNS in the resolved text.
    
            STRICT RULES:
            1. Do NOT remove, skip, rephrase, or shorten any information.
            2. Do NOT invent new facts. The only additions allowed are explicit entity names clearly identifiable from the text.
            3. Preserve sentence order, sentence boundaries, and formatting exactly.
            4. Replace ALL pronouns (he, she, him, her, his, they, them, their, we, us, our, I, me, my, mine, you, your, it, its, etc.) with explicit entity names from the text.  
               - Examples: “She added” → “Rep. Alexandria Ocasio-Cortez (D-NY) added.”  
                 “He takes office” → “Joe Biden takes office.”  
                 “I think” → “Cori Bush said Cori Bush thinks.”
            5. Replace vague expressions (“it,” “this,” “that agreement,” “this administration,” etc.) with the specific noun phrase they refer to, IF identifiable.  
               - Examples: “It represents …” → “The movement represents …”  
                 “That agreement” → “the $2 trillion climate plan agreement.”  
                 “This administration” → “the Biden administration.”
            6. Replace ambiguous role-based references (e.g., “the congresswoman,” “the professor”) with explicit names if identifiable.
            7. Generic references not tied to a specific entity (e.g., “voters,” “people,” “a community”) must remain unchanged.
            8. In direct quotes: replace first-person or group pronouns with the explicit speaker name or group.  
               - Examples: Cori Bush says, “I want bold action” → “Cori Bush said Cori Bush wants bold action.”  
                 Alexandria Ocasio-Cortez says, “We must fight” → “Alexandria Ocasio-Cortez said Alexandria Ocasio-Cortez and the movement must fight.”
            9. If multiple consecutive sentences or quotes are by the same speaker, repeat the speaker’s name in each sentence (no pronouns).
            10. Do NOT use brackets, parentheses, or explanatory notes. Insert entity names naturally.
            11. Minor spacing or punctuation fixes are allowed, but no rewriting.
            12. Delete only irrelevant extras (e.g., “Read more” links, references).
            13. The final resolved text must contain ZERO pronouns — only explicit names or noun phrases.
            14. Output ONLY the resolved text — nothing else.
            15. All first-person expressions in quotes must expand to the explicit speaker name. Example: “I am calling it” → “Cori Bush said Cori Bush is calling it.”
            16. Before output, re-scan and audit: if ANY pronoun remains (I, we, us, our, it, this, that, he, she, etc.), rewrite that part with the explicit entity name. Do not show repeated texts. Only give final output and it must contain no pronouns.
            """

        user_prompt = (f"Resolve all coreferences in each sentence of the following text without repeating any information:\n{text}\nResolved text:")

        # data = {
        #     "model": model,
        #     "messages": [{"role": "system", "content": system_prompt },{"role": "user", "content": user_prompt}],
        #     "stream": False,
        #     "keep_alive": -1,
        #     "temperature": 0,
        #     "max_tokens": 512
        # }

        # result = requests.post(url, headers=headers, json=data)

        outputs = self.llm.chat(
            sampling_params=self.sampling_params,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        result = outputs[0].outputs[0].text
        logging.info(result)
        return result
        # return "TRUE"
    # def get_coref_res_from_api_call(self, text: str):
    #     """
    #     :param summaries: List of summaries (strings), typically 10
    #     :param claim: The claim to verify (string)
    #     :return: "TRUE" or "FALSE", api_key=settings.LLM_API_KEY
    #     """
    #     MODEL_ID = settings.MODEL_NAME
    #     OPAI_CLIENT = OpenAI(base_url=settings.BASE_LLM_URL)
    #
    #     # New system prompt for claim verification from multiple summaries
    #     system_prompt = """You are a text transformation system that performs coreference resolution.
    #     Your task: Replace pronouns and ambiguous references with explicit entity names.
    #     Rules:
    #     1. Do NOT remove any information.
    #     2. Do NOT add any external information.
    #     3. Keep the original sentences, order, and formatting intact.
    #     4. Only adjust references (he, she, his, they, their, it, the man, etc.) to the correct entity.
    #     5. You may clean the text and remove unnecessary whitespace or URLs.
    #     6. Do not start with something like: 'Here is the text with coreference resolution applied:'. Start directly with output."""
    #
    #     # Format the summaries clearly
    #     user_prompt = (f"Resolve coreference in the following text:\n\n{text}.\n"
    #                    f"Coreference text:")
    #
    #
    #
    #     completion = OPAI_CLIENT.chat.completions.create(
    #         model=MODEL_ID,
    #         messages=[
    #             {"role": "system", "content": system_prompt},
    #             {"role": "user", "content": user_prompt},
    #         ],
    #     )
    #
    #     result = completion.choices[0].message.content.strip()
    #     logging.info(result)
    #     return result

    # def get_response_from_api_call(self, evidences: list, claim: str):
    #     """
    #     :param text: textual description
    #     :param claim: the claim to focus the summary on , api_key=settings.LLM_API_KEY
    #     """
    #     # # New system prompt for summarization
    #     sys_prompt = (
    #         "You are an assistant that generates STRICT extractive summaries.\n"
    #         "Given a claim and the text, produce a concise summary of ONLY the information "
    #         "explicitly present in the text that is related to the claim.\n"
    #         "Follow these rules:\n"
    #         "- Do NOT restate the claim.\n"
    #         "- Do NOT add, assume, or infer information not directly supported by the text.\n"
    #         "- If the text contains NO relevant information about the claim, output NOTHING.\n"
    #         "- Use only complete sentences copied or strictly paraphrased from the text.\n"
    #         "- Keep the summary short and factual, without commentary.\n"
    #         "- Do not use prior knowledge or outside facts.\n"
    #         "Your output must ONLY extract from the text, never generate new facts."
    #     )
    #     system_instruction = {"role": "system", "content": sys_prompt}
    #     chat_prompts = []
    #     for ev in evidences:
    #         prompt = (
    #             f"Claim: {claim}\n\n"
    #             f"Text:\n{ev}\n\n"
    #             "Summary:")
    #         messages = [
    #             system_instruction,
    #             {"role": "user", "content": prompt}
    #         ]
    #         chat_prompt = self.tokenizer.apply_chat_template(
    #             messages,
    #             tokenize=False,
    #             add_generation_prompt=True
    #         )
    #         chat_prompts.append(chat_prompt)
    #
    #     # Batch inference for all docs
    #     outputs = self.llm.generate(chat_prompts, self.sampling_params)
    #
    #     # Collect summaries
    #     summaries = []
    #     for i, output in enumerate(outputs):
    #         response_text = output.outputs[0].text.strip()
    #         summaries.append(response_text)
    #         print(f"Doc {i + 1} Summary: {response_text}\n{'-' * 60}\n")
    #
    #     return summaries

    # "You are an assistant that generates STRICT extractive summaries ONLY with respect to the given Claim.\n"
    # "You MUST ignore all unrelated text (to the given claim), even if it is informative or important.\n"
    # "If there is NO explicit mention in the text that directly supports or contradicts the given claim, output NOTHING.\n"
    # "\nStrict Rules:\n"
    # "- You may copy complete sentences or phrases that are explicitly present in the Evidence Text related to given claim.\n"
    # "- You MUST NOT restate, paraphrase, or repeat the Claim unless those exact words are present in the Evidence Text.\n"
    # "- Do NOT summarize unrelated parts of the text.\n"
    # "- Keep it concise and factual.\n"
    # "- Do not add or infer any information.\n"
    # "- If there is no explicit evidence supporting or contradicting the claim, you MUST output EXACTLY: NOTHING.\n"
    def get_response_from_api_call(self, evidences: list, claim: str):
        """
        Summarize evidence documents strictly with respect to the given claim.
        Returns list of per-doc summaries (strings).
        """
        sys_prompt = (
            f"You are an assistant that generates STRICT extractive summaries of evidence text with respect to the given Claim.\n"
            f"You will be given two separate items:\n"
            f"(1) A Claim\n"
            f"(2) Evidence Text\n"
            f"You MUST ignore all unrelated text.\n"
            f"If there is NO explicit mention in the text that directly supports or contradicts the given claim, output NOTHING.\n"
            f"Output rules: \n"
            f"- You may copy COMPLETE SENTENCES or PHRASES from the Evidence Text if, and only if, they explicitly support OR contradict the Claim. \n"
            f"- You MUST NOT echo or restate the Claim unless the exact same words are present in the Evidence Text. \n"
            f"- You MUST IGNORE unrelated portions of the Evidence Text. \n"
            f"- If there is NO relevant evidence, your ENTIRE output must be the single word: NOTHING \n"
            f"- Do NOT output synonyms like \"No information\", \"None\", \"No relevant text.\" Use exactly NOTHING. \n"
            f"- Do not include explanations, reasoning, or commentary. Only the extract or NOTHING. \n"
            f"Task:\n"
            f"- Extract only the exact sentences or phrases from the Evidence Text that support or contradict the Claim."
            f"- You may copy complete sentences or phrases that are explicitly present in the Evidence Text related to given Claim.\n"
            f"- You MUST NOT restate, paraphrase, or repeat the given Claim.\n"
            f"- If there are no relevant sentences in the Evidence Text, output exactly: NOTHING (no punctuation, no explanation, no additional words)\n"
        )
        system_instruction = {"role": "system", "content": sys_prompt}

        chat_prompts = []
        ev_map = []  # keep track of which evidence each belongs to
        print(claim)
        for i, ev in enumerate(evidences):
            if not ev.strip():
                continue  # skip empty
            prompt = (
                f"Claim:\n{claim}\n\n"
                f"Evidence Text:\n{ev}\n\n"
                f"Summary:"
            )
            messages = [system_instruction, {"role": "user", "content": prompt}]
            chat_prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            chat_prompts.append(chat_prompt)
            ev_map.append(i)

        if not chat_prompts:
            return []

        outputs = self.llm.generate(chat_prompts, self.sampling_params)

        summaries = [""] * len(evidences)  # maintain alignment
        for idx, output in zip(ev_map, outputs):
            response_text = output.outputs[0].text.strip()
            # optional extra cleaning: discard irrelevant repetitions NOTHING
            if "nothing" in response_text.lower():
                response_text = ""
            # if response_text.lower() in {"", "none", "no information"}:
            #     response_text = "" #"No information related to the given claim in this summary."
            summaries[idx] = response_text
            print(f"Doc {idx + 1} Summary: {response_text}\n{'-' * 60}\n")

        return summaries

    # """You are a text transformation system that performs COMPLETE coreference resolution.
    #             Your task: make every reference explicit so that each sentence is unambiguous and self‑contained with STRICTLY NO PRONOUNS in the resolved text.
    #
    #             STRICT RULES:
    #             1. Do NOT remove, skip, rephrase, or shorten any information from the text.
    #             2. Do NOT invent new details. The only additions allowed are explicit entity names.
    #             3. Preserve sentence order, sentence boundaries, and overall formatting exactly.
    #             4. In EVERY sentence replace ALL pronouns (he, she, him, her, his, they, them, their, we, us, our, I, me, my, mine, you, your, it, its, etc.) with the correct explicit entity names from the text.
    #                - Example: “She added” → “Rep. Alexandria Ocasio-Cortez (D-NY) added.”
    #                - Example: “He takes office” → “Joe Biden takes office.”
    #                - Example: “I think” → “Cori Bush said Cori Bush thinks.”
    #             5. Replace vague expressions like “it,” “this,” “that agreement,” or “this administration” with the specific noun phrase they refer to, IF identifiable in the text.
    #                - Example: “It represents …” → “The movement represents…”
    #                - Example: “That agreement” → “the $2 trillion climate plan agreement.”
    #                - Example: “This administration” → “the Biden administration.”
    #             6. Replace ambiguous role‑based references (e.g., “the congresswoman,” “the professor,” “the activist”) with explicit entity names, if identifiable from the text.
    #             7. If a reference is generic and not tied to a specific entity (e.g., “voters,” “people,” “a community”), leave it unchanged.
    #             8. For direct quotes: replace every first-person or group pronoun (“I,” “me,” “we,” “our,” “us”) with the explicit speaker name or group name from the attribution.
    #                - Example: Cori Bush says, “I want bold action” → “Cori Bush said Cori Bush wants bold action.”
    #                - Example: Alexandria Ocasio-Cortez says, “We must fight” → “Alexandria Ocasio-Cortez said Alexandria Ocasio-Cortez and the movement must fight.”
    #             9. If multiple consecutive sentences or quotes are by the same speaker, repeat the speaker's name in each one rather than using a pronoun.
    #             10. Do NOT use brackets, parentheses, or explanatory notes. Write the entity names naturally as part of the text.
    #             11. Minor spacing or punctuation corrections are allowed, but do not otherwise rewrite the text.
    #             12. Output only the fully resolved text — with ALL pronouns and ambiguous references replaced in each sentence — and nothing else.
    #             13. You may delete the unnecessay text which is not related to the main theme of the article e.g., links starting with Read more and references.
    #             14. The resolved text strictly must not contain any pronouns at all, only explicit names or noun phrases.
    #             15. Output only the resolved text, nothing else.
    #             16. All first‑person expressions in quotes must be expanded into the explicit speaker name. Example: ‘I am calling it’ → ‘Cori Bush said Cori Bush is calling it.
    #             17. After transformation, audit the text: if ANY pronoun remains, rewrite that part with the explicit entity name. The output must contain zero pronouns.
    #             18. FINAL CHECK: The output must not contain any pronouns at all. If any pronoun remains, rewrite that part with the explicit entity name.
    #             19. Before output, audit: if ANY pronoun remains, rewrite it with the explicit name. The final output must contain no pronouns.
    #             20. Before outputting, re‑scan the text. If ANY pronouns remain (including I, we, us, our, it, this, that, he, she, etc.), rewrite that part until all pronouns are replaced with explicit names.
    #             """