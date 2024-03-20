import re

import torch
import transformers
from langchain_community.embeddings.sentence_transformer import \
    SentenceTransformerEmbeddings
from langchain_community.llms import HuggingFacePipeline
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.vectorstores import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from transformers import (AutoModelForCausalLM, AutoTokenizer,
                          BitsAndBytesConfig, pipeline)

from neutron import utilities

transformers.logging.set_verbosity_error()


class InteractiveModel:
    def __init__(self):
        # Device configuration

        utilities.check_new_pypi_version()
        utilities.ensure_model_folder_exists("neutron_model")
        utilities.ensure_model_folder_exists("neutron_chroma.db")
        # Model and tokenizer configuration
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            utilities.return_path("neutron_model"),
            model_max_length=8192,
            low_cpu_mem_usage=True,
        )
        total_memory_gb = 0
        if torch.cuda.is_available():
            total_memory_gb = torch.cuda.get_device_properties(0).total_memory / (
                1024**3
            )  # Convert bytes to GB
            print(f"total GPU memory available {total_memory_gb}")
            if total_memory_gb < 24:
                print("There isnt enough GPU memory, will use CPU")

        if total_memory_gb >= 24:
            self.model = AutoModelForCausalLM.from_pretrained(
                utilities.return_path("neutron_model"),
                quantization_config=bnb_config,
                device_map={"": 0},
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                utilities.return_path("neutron_model"),
                low_cpu_mem_usage=True,
                quantization_config=bnb_config,
            )
        # Pipeline configuration
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=7000,
            repetition_penalty=1.2,
            use_fast=True,
        )
        self.search_results = ""
        self.search = DuckDuckGoSearchRun()
        # Components for LangChain
        self.llm = HuggingFacePipeline(pipeline=self.pipe)
        self.embeddings_model = SentenceTransformerEmbeddings(
            model_name="all-MiniLM-L12-v2"
        )
        self.db = Chroma(
            embedding_function=self.embeddings_model,
            persist_directory="neutron_chroma.db",
        )
        self.retriever = self.db.as_retriever(search_type="mmr")
        # self.retriever = self.db.as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold": 1.0})

        self.template = ChatPromptTemplate.from_template(
            """
            As a penetration testing assistant, provide a response based on your knowledge and the provided 'context',and 'context2. 
            Ensure the response is directly relevant to the inputs, focusing particularly on elements common to both 'context' and 'context2'. 
            Revise your responses to maintain a consistent context throughout and do not alter commands returned in the contexts, but you can modify surrounding statements. all commands should be formatted using backticks. Eliminate any sections that diverge from or do not fit within this established context.
            Given contexts:
            - Context: {context}
            - Context2: {context2}
            Question: {question}
            Answer:
            """
        )

        self.current_mode = "retrieval"  # Default mode
        self.search_results = ""
        self.search = DuckDuckGoSearchRun()

        self.chain = (
            {
                "context": self.retriever,
                "context2": lambda x: self.search_results,
                "question": RunnablePassthrough(),
            }
            | self.template
            | self.llm
            | StrOutputParser()
        )

    def invoke(self, question: str):
        self.search_results = self.search.run(question)
        # print(self.search_results)
        return self.chain.invoke(question)

    def search_duck(self, question: str):
        # Perform the search
        result = self.search(question)
        # This regular expression replaces periods followed by a space (and not preceded by a digit) with a period followed by two newlines and a space.
        # It also adds two newlines before numbers followed by a period and a space (e.g., in numbered lists).
        formatted_result = re.sub(
            r"(?<!\d)\. ", ".\n\n ", result
        )  # Add newlines after sentences not in numbered lists.
        formatted_result = re.sub(
            r"(\n|^)(\d+\.) ", r"\1\n\n\2 ", formatted_result
        )  # Add newlines before numbered list items.
        return formatted_result
