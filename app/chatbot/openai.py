"""OpenAI-backed chatbot that retrieves relevant Redis doc chunks and generates RAG chat responses."""

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, convert_to_messages
from langchain_openai import ChatOpenAI

from app.prompts.system import SYSTEM_PROMPT
from app.store.pg_vector import PGVectorStore


class ChatBot:
    def __init__(self, vs: PGVectorStore):
        """Store the vector store and initialize the OpenAI chat model."""
        self.llm = ChatOpenAI()
        self.vs = vs

    def generate(
        self,
        system_message: SystemMessage,
        human_message: HumanMessage,
        history_messages: list[BaseMessage] = [],
    ):
        """Invoke the LLM with the system prompt, prior history, and the new message, returning its text reply."""
        messages: list[BaseMessage] = [system_message]
        messages.extend(history_messages)
        messages.append(human_message)
        response = self.llm.invoke(messages)
        return response.content

    def get_chat_function(self):
        """Build and return a Gradio-compatible chat callback that performs retrieval-augmented generation."""
        def redis_chat(message, history):
            """Retrieve relevant doc chunks for the message and generate a context-grounded reply."""
            relevant_chunks = self.vs.get(message)
            context = "\n\n".join(chunk.page_content for chunk in relevant_chunks)
            system_prompt = SYSTEM_PROMPT.format(context=context)
            system_message = SystemMessage(content=system_prompt)
            history_messages = convert_to_messages(history)
            human_message = HumanMessage(content=message)
            return self.generate(system_message, human_message, history_messages)
        return redis_chat
