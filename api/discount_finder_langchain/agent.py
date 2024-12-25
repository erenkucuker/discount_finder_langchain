
from discount_finder_langchain.tools import all_tools
from discount_finder_langchain.config import config
from langchain_experimental.plan_and_execute import (
    PlanAndExecute,
    load_chat_planner,
)
from discount_finder_langchain.config import config
from discount_finder_langchain.utils import create_agent_executor
from discount_finder_langchain.prompts import SYSTEM_PROMPT
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


def create_new_discount_finder_agent():
    planner_llm = ChatOpenAI(
        temperature=0,
        openai_api_key=OPENAI_API_KEY,
        model="gpt-4o-mini"
    )
    executor_llm = ChatOpenAI(
        temperature=0,
        openai_api_key=OPENAI_API_KEY,
        model="gpt-4o-mini"
    )

    planner = load_chat_planner(planner_llm, system_prompt=SYSTEM_PROMPT)
    agent_executor = create_agent_executor(
        executor_llm, all_tools, verbose=config.verbose, include_task_in_prompt=True)
    agent = PlanAndExecute(
        planner=planner, executor=agent_executor, verbose=config.verbose, memory=None)
    return agent
