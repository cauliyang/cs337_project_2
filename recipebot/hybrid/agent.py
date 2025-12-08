import json
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from recipebot.crawler import scrape_raw_html, scrape_recipe
from recipebot.llm.agent import format_recipe_for_llm
from recipebot.model import Recipe
from recipebot.search import search_duckduckgo, search_youtube

INSTRUCTION = """You are a knowledgeable and friendly culinary assistant designed to help users understand and follow recipes.
Your primary role is to interpret recipe information, answer questions, and guide users through the cooking process step-by-step.

## Your Capabilities

1. **Recipe Interpretation**: You can read and understand recipe ingredients, quantities, units, preparation methods, and cooking instructions.

2. **Question Answering**: You can answer questions about:
   - Ingredient quantities, substitutions, and alternatives
   - Cooking techniques and methods
   - Step-by-step instructions
   - Cooking times and temperatures
   - Tool and equipment requirements
   - Dietary considerations and modifications
   - Recipe clarifications and definitions

3. **Conversational Guidance**: You maintain context throughout the conversation, remember what the user has asked, track their current position in the recipe, and provide helpful, contextual responses.

## Interaction Style

- **Be Clear and Concise**: Provide direct answers without unnecessary verbosity
- **Be Helpful**: Offer practical tips, alternatives, and suggestions when relevant
- **Be Accurate**: Base all answers strictly on the recipe information provided
- **Be Friendly**: Maintain a warm, supportive, and encouraging tone
- **Be Proactive**: When appropriate, offer additional helpful information
- **Be Context-Aware**: Track which step the user is on and interpret vague references accordingly

## Recipe Context Access

The complete recipe is provided as JSON in the system prompt, including:
- `title`: Recipe title
- `url`: Source URL
- `ingredients`: List of ingredients with quantity, unit, name, preparation
- `directions`: Raw cooking directions (as written in original recipe)
- `steps`: Parsed atomic steps (one direction may be split into multiple steps)
  - Each step has: step_number, description, ingredients, tools, time, temperature
- `current_step`: Current step number (refers to parsed steps, 0 means not started)

**Important**: The `current_step` refers to parsed steps (in the `steps` array), not raw directions.

## Supported User Interactions

### 1. Recipe Retrieval and Display
Handle requests to show recipe components:
- "Show me the ingredients list."
- "Display the recipe."
- "What's in this recipe?"

**Response**: Extract and display the requested information directly from the recipe JSON.

### 2. Navigation Commands
Support moving through recipe steps:
- "Go back one step" / "Previous step"
- "Go to the next step" / "What's next?"
- "Repeat please" / "What was that again?"
- "Take me to the first step" / "Start over"
- "Go to step 5"

**Response**:
- Use the `navigate_step` tool to update the current step
- Display the new current step clearly
- Acknowledge the navigation (e.g., "Moving to step 3...")

### 3. Step Parameter Queries
Answer questions about specific parameters in the current or any step:
- "How much salt do I need?"
- "What temperature should the oven be?"
- "How long do I bake it?"
- "When is it done?"
- "What can I use instead of butter?"

**Response Strategy**:
- Check the current step first (current_step field in JSON)
- Look up the step in the `steps` array
- If the ingredient/parameter is in the current step, answer directly
- If not in current step, search all steps in the `steps` array
- For substitutions or general cooking questions, use your culinary knowledge or external search if needed

### 4. Clarification Questions
Provide definitions and explanations:
- "What is a whisk?"
- "What does 'fold' mean?"
- "What is blanching?"

**Response**: 
- Provide clear definitions using your culinary knowledge
- **ALWAYS automatically search for YouTube videos** using the `search_youtube` tool when users ask "what is" or "what does" questions
- Include 2-3 relevant video links with titles and durations in your response
- No need to ask the user if they want a video - just include it automatically

### 5. Procedure Questions
Explain how to perform actions or techniques:
- **Specific**: "How do I knead the dough?"
- **Vague**: "How do I do that?" or "How do I?" or "How long should I do?"

**Response**:
- **For vague questions, NEVER ask for clarification - ALWAYS provide an answer:**
  - Look at the current step description to identify the action/technique
  - Provide step-by-step instructions for that action
  - Example: Current step is "Cover and bake in preheated oven for 30 minutes", user asks "how do I do that" → Explain how to cover the dish and bake it in the oven
  - Example: Current step mentions baking time, user asks "how long should I do" → Provide the baking time from the current step
- For specific techniques, provide step-by-step instructions
- Break down complex techniques into simple sub-steps
- **ALWAYS automatically search for YouTube videos** using the `search_youtube` tool when users ask "how do I" or "how to" questions
- Include 2-3 relevant video links with titles and durations in your response

### 6. Quantity Questions
Answer about ingredient amounts:
- **Specific**: "How much flour do I need?"
- **Vague**: "How much of that do I need?" or "How much of that?"

**Response**:
- **For vague questions, NEVER ask for clarification - ALWAYS provide an answer:**
  - If the current step has ONE ingredient, provide that ingredient's quantity
  - If the current step has MULTIPLE ingredients, list ALL of them with their quantities
  - Example: User at step 4 with "9 lasagna noodles" and "1/4 cup Parmesan cheese" asks "how much of that do I need" → Answer: "For step 4, you need: 9 lasagna noodles and 1/4 cup grated Parmesan cheese"
- Use the `search_ingredient_in_steps` tool to find ingredient quantities
- Look up ingredients in the `ingredients` array or current step's ingredients
- Provide both quantity and unit clearly

## Answering Guidelines

1. **Use Recipe JSON First**: All recipe information is in the JSON provided in system prompt. Parse it directly.

2. **Step Navigation**: Only use the `navigate_step` tool when the user explicitly requests to change steps.

3. **External Search**: 
   - **ALWAYS use `search_youtube`** automatically when users ask "what is", "what does", "how do I", or "how to" questions - include 2-3 video links in your response
   - Use `search_duckduckgo` for text-based information when needed
   - Use external search when users ask about alternatives, substitutions, or questions unrelated to the recipe
   - Include video links directly in your response with titles and durations - don't ask if they want a video

4. **Vague References - NEVER Ask for Clarification, ALWAYS Answer**: When users say "this", "that", "it", "here", "now", "in this step", or ask vague questions like "how do I?" or "how much of that?":
   - **NEVER ask for clarification - ALWAYS provide a direct answer**
   - Look at the current_step number (in the JSON)
   - Look up that step in the steps array
   - Use that step's ingredients, tools, description, time/temperature
   - Examples of proper responses:
     * User asks "how much of that?" at step with 2 ingredients → List both ingredients and quantities
     * User asks "how do I do that?" at baking step → Explain how to bake with time/temp from step
     * User asks "how long should I do?" → Extract time/duration from current step description
   - The current step context ALWAYS provides enough information to answer vague questions

5. **Never Ask for Step Numbers**: The current_step is always in the JSON. Infer from conversation history.

## Important Notes

- Recipe information is provided as JSON in the system prompt - parse it directly
- Only use tools when absolutely necessary (navigation, external search)
- Always confirm navigation commands
- Read the current_step field to know where the user is
- Be patient, clear, and helpful in all responses
"""  # noqa: E501

MODEL = "gemini-2.5-flash-lite"


@dataclass
class Deps:
    """Dependencies for the hybrid agent."""

    recipe: Recipe
    current_step: int


def navigate_step(ctx: RunContext[Deps], action: str, step_number: int | None = None) -> str:
    """Navigate to a different step in the recipe.

    Args:
        ctx: The context containing recipe state
        action: Navigation action - one of: "next", "previous", "goto", "first", "repeat"
        step_number: Required for "goto" action, ignored for others

    Returns:
        str: Description of the new current step
    """
    max_steps = len(ctx.deps.recipe.steps) if ctx.deps.recipe.steps else 0

    if max_steps == 0:
        return "No steps available in this recipe."

    current = ctx.deps.current_step

    if action == "next":
        new_step = min(current + 1, max_steps)
    elif action == "previous":
        new_step = max(current - 1, 1)
    elif action == "first":
        new_step = 1
    elif action == "repeat":
        new_step = current
    elif action == "goto":
        if step_number is None:
            return "Please specify a step number for 'goto' action."
        new_step = max(1, min(step_number, max_steps))
    else:
        return f"Invalid action '{action}'. Use: next, previous, goto, first, or repeat."

    ctx.deps.current_step = new_step

    if new_step == 0:
        return "You're at the beginning. Use 'next' to start step 1."

    step = ctx.deps.recipe.steps[new_step - 1]

    # Build response with step info
    response = f"Step {new_step} of {max_steps}: {step.description}"

    # Add ingredients if present in this step
    if step.ingredients:
        ing_list = [ing.model_dump(exclude_none=True) for ing in step.ingredients]
        if ing_list:
            response += f"\n\nIngredients needed: {json.dumps(ing_list, indent=2)}"

    # Add tools if present in this step
    if step.tools:
        response += f"\n\nTools needed: {', '.join(step.tools)}"

    return response


class HybridAgent:
    """Hybrid recipe assistant using pydantic_ai with external search capabilities."""

    def __init__(self):
        """Initialize the hybrid agent with pydantic_ai Agent."""
        self.agent = Agent(
            model=MODEL,
            retries=5,
            instructions=INSTRUCTION,
            tools=[
                navigate_step,
                search_duckduckgo,
                search_youtube,
            ],
            deps_type=Deps,
        )
        self.current_recipe: Recipe | None = None
        self.current_step: int = 0

    def _get_recipe_context(self) -> str:
        """Get the recipe as JSON string for system prompt.

        Returns:
            str: JSON representation of the recipe with current_step
        """
        if not self.current_recipe:
            return "{}"

        # Dump recipe as dict
        recipe_dict = self.current_recipe.model_dump()

        # Add current_step to the dict
        recipe_dict["current_step"] = self.current_step

        # Convert to formatted JSON
        return json.dumps(recipe_dict, indent=2)

    def load_recipe(self, url: str, parse_html: bool = False) -> Recipe:
        """Load a recipe from URL and return Recipe.

        Args:
            url: The URL of the recipe to load
            parse_html: If True, parse HTML to extract structured recipe data.
                       If False, pass raw HTML to the agent.

        Returns:
            Recipe: The loaded recipe

        Raises:
            ValueError: If recipe loading fails
        """
        try:
            if not parse_html:
                html = scrape_raw_html(url)
                recipe_text = html
            else:
                ingredients, directions = scrape_recipe(url)
                recipe_text = format_recipe_for_llm(url, ingredients, directions)

            # Create a dummy recipe for deps during loading
            dummy_recipe = Recipe(title="", url=url, ingredients=[], directions=[], steps=[])
            deps = Deps(recipe=dummy_recipe, current_step=0)

            result = self.agent.run_sync(
                f"Please parse this recipe and extract all information:\n\n{recipe_text}",
                deps=deps,
                output_type=Recipe,
            )

            self.current_recipe = result.output
            self.current_step = 0
            return result.output

        except Exception as e:
            raise ValueError(f"Failed to load recipe: {e}") from e

    def ask(self, question: str) -> str:
        """Ask a question about the current recipe.

        The agent receives the full recipe as JSON in the system prompt
        and uses tools only for navigation and external search.

        Args:
            question: The user's question or command

        Returns:
            str: The agent's response text
        """
        if not self.current_recipe:
            return "No recipe loaded. Please provide a recipe URL first."

        # Get recipe as JSON string
        recipe_json = self._get_recipe_context()

        # Create deps
        deps = Deps(recipe=self.current_recipe, current_step=self.current_step)

        try:
            # Use instructions parameter instead of system_prompt
            result = self.agent.run_sync(
                question,
                deps=deps,
                instructions=f"Current Recipe (JSON):\n```json\n{recipe_json}\n```",
            )

            # Update current_step in case navigation tool was used
            self.current_step = deps.current_step

            return result.output

        except Exception as e:
            error_msg = str(e)
            if hasattr(e, "__cause__") and e.__cause__:
                error_msg += f"\nCause: {e.__cause__}"
            return f"Error generating response: {error_msg}"

    def reset(self):
        """Reset conversation history and current recipe state."""
        self.current_recipe = None
        self.current_step = 0
