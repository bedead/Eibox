import asyncio
from .states import ManagerState
from ..chatbot_agent import ChatbotState, ChatAgent
from ..email_agent import EmailState, EmailAgent
from langgraph.config import RunnableConfig
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage


class AgentManagerWithAioconsole:
    def __init__(self, config: RunnableConfig):
        self.state = ManagerState(
            messages=[],
            pending_email=False,
            email_summary=None,
            response_draft=None,
        )
        self.config = config
        self.lock = asyncio.Lock()

    async def call_chatbotAgent(self, user_input: str):
        async with self.lock:
            self.state["messages"].append(HumanMessage(content=user_input))
            input_state = {"messages": self.state["messages"]}

        print("Chatbot Agent called")
        async for chunk in ChatAgent.astream(
            input=input_state, config=self.config, stream_mode="values"
        ):
            new_messages = chunk.get("messages", [])

            # Only care about newly added messages
            async with self.lock:
                for msg in new_messages:
                    if isinstance(msg, AIMessage):
                        # Add only if not already in state
                        already_exists = any(
                            isinstance(existing, AIMessage)
                            and existing.content == msg.content
                            for existing in self.state["messages"]
                        )
                        if not already_exists:
                            self.state["messages"].append(msg)
                            print(f"AI: {msg.content}")

    async def call_emailAgent(self):
        async with self.lock:
            pending_email = self.state.get("pending_email")

        if not pending_email:
            print(f"EmailAgent called")
            response = await EmailAgent.ainvoke(
                input={"pending_email": pending_email}, config=self.config
            )

            async with self.lock:
                self.state["pending_email"] = response.get("is_response_needed", False)
                self.state["email_summary"] = response.get("email_summary")
                self.state["response_draft"] = response.get("response_email_draft")

                print("\n[EmailAgent Response]")
                print(f"Summary: {self.state['email_summary']}")
                print(f"Draft: {self.state['response_draft']}")

    async def run(self):
        """
        This version requires: pip install aioconsole
        """
        try:
            import aioconsole
        except ImportError:
            print("aioconsole not installed. Please run: pip install aioconsole")
            return

        print("Welcome to Multi-Agent CLI. Type 'exit' to quit.")

        while True:
            try:
                # Truly async input
                user_input = await aioconsole.ainput("You: ")

                if user_input.lower() in {"exit", "quit"}:
                    break

                # Run both agents concurrently
                await asyncio.gather(
                    self.call_chatbotAgent(user_input), self.call_emailAgent()
                )
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
                continue
