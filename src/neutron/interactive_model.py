import re
import torch
import transformers
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline

from neutron import utilities
import sys
transformers.logging.set_verbosity_error()


class InteractiveModel:
    def __init__(self, cache_dir, model_name: str = "deepseek-ai/DeepSeek-R1-Distill-Llama-8B", use_search: bool = True):
        # Device configuration
        if not torch.cuda.is_available():
            raise Exception("No GPUs available")
 
        utilities.check_new_pypi_version()

        # Model and tokenizer configuration for 8-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_8bit=True
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            model_max_length=8192,
            low_cpu_mem_usage=True,
            cache_dir=cache_dir
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            low_cpu_mem_usage=True,
            quantization_config=bnb_config,
            device_map="auto",
            cache_dir=cache_dir
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
        self.use_search = use_search
        if self.use_search:
            self.search = DuckDuckGoSearchRun()

        # Components for LangChain using the new HuggingFacePipeline
        self.llm = HuggingFacePipeline(pipeline=self.pipe)

        # Create a prompt template and build the chain.
        self.template = ChatPromptTemplate.from_template(
            """
            As a penetration testing assistant, provide a response based on your knowledge and the provided context and context2. 
            Ensure the response is directly relevant to the inputs, focusing particularly on elements common to both context and context2. 
            Revise your responses to maintain a consistent context throughout and do not alter commands returned in the contexts, but you can modify surrounding statements. All commands should be formatted using backticks. Eliminate any sections that diverge from or do not fit within this established context.
            Given contexts:
            - Context: {context}
            - Context2: {context2}
            Question: {question}
            Answer:
            """
        )

        self.chain = (
            {
                "context": lambda _: "",  # Changed from a plain string to a callable returning an empty string.
                "context2": lambda x: self.search_results if self.use_search else "",
                "question": RunnablePassthrough(),
            }
            | self.template
            | self.llm
            | StrOutputParser()
        )

    def invoke(self, question: str):
        if self.use_search:
            self.search_results = self.search.run(question)
        return self.chain.invoke(question)

    def search_duck(self, question: str):
        if not self.use_search:
            return ""
        # Perform the search and format the result
        result = self.search.run(question)
        formatted_result = re.sub(r"(?<!\d)\. ", ".\n\n ", result)
        formatted_result = re.sub(r"(\n|^)(\d+\.) ", r"\1\n\n\2 ", formatted_result)
        return formatted_result
