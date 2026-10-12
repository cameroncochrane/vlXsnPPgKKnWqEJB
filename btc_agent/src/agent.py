# This script will contain the LLM and agentic functionality.

# Base imports
import os
import asyncio 
from agents import Agent, Runner
from openai import AsyncOpenAI

OPENAI_TOKEN = os.getenv("OPENAI_API_KEY")
# run 'source ~/.zshrc' in terminal after changes to env to refresh changes.

