"""LLM-only recipe assistant module."""

from recipebot.llm.agent import RecipeAssistant

from . import cli

__all__ = ["RecipeAssistant", "cli"]
