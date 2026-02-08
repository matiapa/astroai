#!/usr/bin/env python3
"""
Observation Planner - An AI-powered astronomical observation planning agent.

This agent helps users plan optimal observation sessions by combining 
astronomical data (twilight, moon phase, object visibility) with AI intelligence
to create personalized, time-ordered observation plans.
"""

from google.adk.tools.google_search_tool import GoogleSearchTool
import os
import sys
import re
from pathlib import Path
from datetime import datetime, timezone
from google.adk.tools.function_tool import FunctionTool

# Add project root to path so we can import from src
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from google.adk.agents import Agent
from src.tools.observation_planning.conditions import get_observation_conditions
from src.tools.observation_planning.catalog_search import search_observable_objects
from src.tools.observation_planning.visibility import calculate_object_visibility

# Observation planning tools
obs_conditions_tool = FunctionTool(func=get_observation_conditions)
catalog_search_tool = FunctionTool(func=search_observable_objects)
visibility_tool = FunctionTool(func=calculate_object_visibility)

search_tool = GoogleSearchTool(bypass_multi_tools_limit=True)

# Read the prompt from the markdown file
with open("./agents/observation_planner/prompt.md", "r") as f:
    prompt = f.read()
    prompt = re.sub(r"<!--.*?-->", "", prompt, flags=re.DOTALL)
    prompt = prompt.replace("{{current_utc_date}}", datetime.now(timezone.utc).strftime("%Y-%m-%d"))

# Define the root agent
root_agent = Agent(
    model="gemini-3-flash-preview",
    name="observation_planner",
    description="Un planificador de observaciones astronómicas que ayuda a los usuarios a crear planes de observación personalizados basados en su ubicación, equipo e intereses.",
    instruction=prompt,
    tools=[
        search_tool,
        obs_conditions_tool,
        catalog_search_tool,
        visibility_tool,
    ],
)
