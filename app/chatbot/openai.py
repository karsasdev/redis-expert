from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage, convert_to_messages
from langchain_openai import ChatOpenAI

from app.prompts.system import SYSTEM_PROMPT
from app.store.pg_vector import PGVectorStore


class ChatBot:
    def __init__(self, vs: PGVectorStore):
        self.llm = ChatOpenAI()
        self.vs = vs

    def generate(self, system_message: SystemMessage, human_message: HumanMessage, history_messages: list[BaseMessage] = []):
        messages: list[BaseMessage] = [system_message]
        messages.extend(history_messages)
        messages.append(human_message)
        response = self.llm.invoke(messages)
        return response.content

    def get_chat_function(self):
        def redis_chat(message, history):
            relevant_chunks = self.vs.get(message)
            context = "\n\n".join(chunk.page_content for chunk in relevant_chunks)
            system_prompt = SYSTEM_PROMPT.format(context=context)
            system_message = SystemMessage(content=system_prompt)
            history_messages = convert_to_messages(history)
            human_message = HumanMessage(content=message)
            return self.generate(system_message, human_message, history_messages)
        return redis_chat