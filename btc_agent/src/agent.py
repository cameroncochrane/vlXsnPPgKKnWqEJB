# This script will contain the LLM and agentic functionality.

# What functionality will the agent require to be able to trade?:
    # - Update trading.db
    # - Send notifications using Telegram when a trade is executed
    # - Update agent_log.db (.json) with a log of chat history / its own actions

# Base imports
import os
import asyncio 
from agents import Agent, Runner
from openai import AsyncOpenAI

OPENAI_TOKEN = os.getenv("OPENAI_API_KEY")
# run 'source ~/.zshrc' in terminal after changes to env to refresh changes.

def run_agent(api_token=OPENAI_TOKEN,context=None):
    """
    This will be an importable function that can be called in main.py.

    It needs to know context and also know that it may have been operating before i.e. it may see actions that it carried out but not remember.
    """
    return None