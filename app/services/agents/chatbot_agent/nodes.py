from datetime import datetime
import json
from typing import List, Dict, Any, cast

from langchain_core.messages import SystemMessage
from langgraph.types import Command
from langgraph.store.base import BaseStore, Item
from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model

from app.services.agents.chatbot_agent.tools import all_tools
from app.core.logging import logger
from app.core.config import settings
from app.services.agents.chatbot_agent.states import ChatbotState
from app.utils._prompts import (
    CHATBOT_SYSTEM_INSTRUCTION,
    EPISODIC_MEMORY_PROMPT,
    SEMANTIC_MEMORY_PROMPT,
)
from app.utils.common import clean_and_parse_ai_output


llm = init_chat_model(model="google_genai:gemini-2.0-flash", temperature=0.6)
model_with_tools = llm.bind_tools(all_tools)
namespace_for_memory = ("auth", "user")


def context_update(
    state: ChatbotState, store: BaseStore, config: RunnableConfig
) -> Command:

    # Get memory update counter from state
    memory_update_counter: int = state.memory_update_counter
    if memory_update_counter == 0:
        # Data extraction from config
        configurable: Dict[str, Any] | None = config.get("configurable")
        if configurable:
            username: str = configurable.get("username", "satyam")
            # thread_id = config["configurable"].get("thread_id", "test_thread")

            semantic_memory_key = f"user-semantic-memory:{username}"
            episodic_memory_key = f"user-episodic-memory:{username}"

            # Get past memory
            semantic_memory: Item | None = store.get(
                namespace=namespace_for_memory, key=semantic_memory_key
            )
            episodic_memory: Item | None = store.get(
                namespace=namespace_for_memory, key=episodic_memory_key
            )

            if semantic_memory and episodic_memory:
                llm = init_chat_model(
                    model="google_genai:gemini-1.5-flash", temperature=0.5
                )
                # Call LLM if semantic memory is available
                # update data
                updated_semantic_memory = llm.invoke(
                    SEMANTIC_MEMORY_PROMPT.replace(
                        "{data}", json.dumps(semantic_memory.value, ensure_ascii=False)
                    ).replace(
                        "{context}", str(state.messages) if state.messages else ""
                    )
                )

                logger.debug(
                    f"updated_semantic_memory : {updated_semantic_memory.content}"
                )
                logger.debug(
                    f"type of updated_semantic_memory : {type(updated_semantic_memory.content)}"
                )
                # updated_semantic_memory = clean_and_parse_ai_output(
                #     updated_semantic_memory.content
                # )
                # print("Updated Semantic Memory:", updated_semantic_memory)

                # store updated semantic memory
                store.put(
                    namespace=namespace_for_memory,
                    key=semantic_memory_key,
                    value=updated_semantic_memory.content,  # type: ignore
                )

                updated_episodic_memory = llm.invoke(
                    EPISODIC_MEMORY_PROMPT.replace(
                        "{data}", json.dumps(episodic_memory.value, ensure_ascii=False)
                    ).replace(
                        "{context}",
                        str(state.messages) if state.messages else "",
                    )
                )

                # store updated episodic memory
                store.put(
                    namespace=namespace_for_memory,
                    key=episodic_memory_key,
                    value=updated_episodic_memory.content,  # type: ignore
                )

                return Command(
                    update={
                        "semantic_memory": (
                            updated_semantic_memory if updated_semantic_memory else ""
                        ),
                        "episodic_memory": (
                            updated_episodic_memory if updated_episodic_memory else ""
                        ),
                        "memory_update_counter": 3,
                    }
                )
        else:
            logger.warning(
                f"Chat Agent Graph doesn't seems to have RunnableConfig, check Websocket api module for errors.",
                exc_info=True,
            )
            return Command()

    return Command(update={"memory_update_counter": memory_update_counter - 1})


def chatbot(state: ChatbotState, store: BaseStore, config: RunnableConfig) -> Command:

    # If job scheduler is running, get the mail data pre-fetched by background task and stored in redis store
    unread_mail_data_list: list = []
    unread_mails_count: int = 0
    if settings.RUN_JOB_SCHEDULER:
        # get username and thread_id from chat config
        configurable: Dict[str, Any] | None = config.get("configurable")

        if configurable:
            username = configurable.get("username")
            thread_id = configurable.get("thread_id")

            # create unqiue key to get the data
            data_key = f"user-data:{username}:{thread_id}"
            unread_key = f"user-unread_mails:{username}:{thread_id}"

            # get data from store
            mail_data_item: Item | None = store.get(
                namespace=namespace_for_memory, key=data_key
            )
            unread_mails_item: Item | None = store.get(
                namespace=namespace_for_memory, key=unread_key
            )

            # Extract values or set defaults
            if mail_data_item and unread_mails_item:
                mail_data_list: List[Dict[str, Any]] = cast(
                    List[Dict[str, Any]], mail_data_item.value
                )
                unread_mails_count: int = cast(int, unread_mails_item.value)

                for i in mail_data_list:
                    if i.get("unread"):
                        # print(f"Skipping read mail: {i.get('unread')}")
                        unread_mail_data_list.append(i)
                logger.debug(f"Unread mail data list: {unread_mail_data_list}")
                logger.debug(f"Unread mails: {unread_mails_count}")
            else:
                logger.info(
                    f"No Unread Mail data found, because background process not running for user: {username}."
                )
        else:
            logger.warning(
                f"Chat Agent Graph doesn't seems to have RunnableConfig, check Websocket api module for errors.",
                exc_info=True,
            )

    # Retrive memory from state
    semantic_memory: str = state.semantic_memory
    episodic_memory: str = state.episodic_memory

    system_instruction = CHATBOT_SYSTEM_INSTRUCTION.format(
        unread_mails_count=(
            unread_mails_count
            if (settings.RUN_JOB_SCHEDULER and unread_mails_count)
            else 0
        ),
        mail_data_list=(
            unread_mail_data_list
            if (settings.RUN_JOB_SCHEDULER and unread_mail_data_list)
            else []
        ),
        semantic_memory=semantic_memory if semantic_memory else "",
        episodic_memory=episodic_memory if episodic_memory else "",
        CURRENT_DATE=datetime.now().strftime("%Y-%m-%d"),
        CURRENT_TIME=datetime.now().strftime("%H:%M %p"),
        TIMEZONE=datetime.now().astimezone().tzname(),
    )

    messages = [
        SystemMessage(content=system_instruction),
    ] + state.messages

    # tool llm model call
    message = model_with_tools.invoke(messages)
    if isinstance(message, dict):
        message = message.get("messages")
        message = message[-1] if message else None
    return Command(update={"messages": [message]})
