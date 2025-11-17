"""Custom Rasa actions for recipe bot."""

from typing import Any

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet

from recipebot.parser import parse_recipe
from recipebot.search import search_duckduckgo, search_youtube


class ActionFetchRecipe(Action):
    """Fetch and parse recipe from URL."""

    def name(self) -> str:
        return "action_fetch_recipe"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        recipe_url = tracker.get_slot("recipe_url")

        if not recipe_url:
            dispatcher.utter_message(text="Please provide a recipe URL.")
            return []

        try:
            # Parse recipe from URL (includes ingredients, directions, and steps)
            # TODO: change finer granularity of parsing
            recipe_data = parse_recipe(
                recipe_url,
                split_by_atomic_steps=True,
            )

            # Success message
            dispatcher.utter_message(
                text=f"✓ Recipe loaded: {recipe_data.title}\n"
                f"  • {len(recipe_data.ingredients)} ingredients\n"
                f"  • {len(recipe_data.steps)} steps"
            )

            return [
                SlotSet("recipe_data", recipe_data.dict()),
                SlotSet("recipe_title", recipe_data.title),
                SlotSet("total_steps", len(recipe_data.steps)),
                SlotSet("current_step", 0),
            ]

        except Exception as e:
            dispatcher.utter_message(text=f"Error fetching recipe: {e}")
            return []


class ActionShowIngredients(Action):
    """Display recipe ingredients."""

    def name(self) -> str:
        return "action_show_ingredients"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        recipe_data = tracker.get_slot("recipe_data")

        if not recipe_data:
            dispatcher.utter_message(text="No recipe loaded. Please provide a recipe URL first.")
            return []

        ingredients = recipe_data.get("ingredients", [])

        if not ingredients:
            dispatcher.utter_message(text="No ingredients found in this recipe.")
            return []

        message = "📋 Ingredients:\n"
        for i, ing in enumerate(ingredients, 1):
            quantity = ing.get("quantity", "")
            unit = ing.get("unit", "")
            name = ing.get("name", "")
            preparation = ing.get("preparation", "")

            line = f"{i}. "
            if quantity:
                line += f"{quantity} "
            if unit:
                line += f"{unit} "
            line += name
            if preparation:
                line += f", {preparation}"

            message += line + "\n"

        dispatcher.utter_message(text=message)
        return []


class ActionShowSteps(Action):
    """Display all recipe steps."""

    def name(self) -> str:
        return "action_show_steps"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        recipe_data = tracker.get_slot("recipe_data")

        if not recipe_data:
            dispatcher.utter_message(text="No recipe loaded. Please provide a recipe URL first.")
            return []

        steps = recipe_data.get("steps", [])

        if not steps:
            dispatcher.utter_message(text="No steps found in this recipe.")
            return []

        message = f"📝 Recipe Steps ({len(steps)} total):\n\n"
        for step in steps:
            step_num = step.get("step_number", 0)
            description = step.get("description", "")
            message += f"Step {step_num}: {description}\n"

        dispatcher.utter_message(text=message)
        return [SlotSet("current_step", 1)]


class ActionShowCurrentStep(Action):
    """Display the current step."""

    def name(self) -> str:
        return "action_show_current_step"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        recipe_data = tracker.get_slot("recipe_data")
        current_step = tracker.get_slot("current_step")

        if not recipe_data:
            dispatcher.utter_message(text="No recipe loaded.")
            return []

        steps = recipe_data.get("steps", [])

        if not steps or current_step < 1 or current_step > len(steps):
            dispatcher.utter_message(text="Invalid step number.")
            return []

        step = steps[current_step - 1]
        message = self._format_step(step, current_step, len(steps))

        dispatcher.utter_message(text=message)
        return []

    def _format_step(self, step: dict, step_num: int, total: int) -> str:
        """Format step information for display."""
        message = f"📍 Step {step_num}/{total}:\n"
        message += f"{step.get('description', '')}\n"

        # Add time if present
        time_info = step.get("time", {})
        if time_info:
            if "duration" in time_info:
                message += f"⏱️  Time: {time_info['duration']} minutes\n"
            elif "until" in time_info:
                message += f"⏱️  Time: {time_info['until']}\n"

        # Add temperature if present
        temp_info = step.get("temperature", {})
        if temp_info:
            if "value" in temp_info:
                message += f"🌡️  Temperature: {temp_info['value']}°{temp_info.get('unit', 'F')}\n"
            elif "qualitative" in temp_info:
                message += f"🌡️  Heat: {temp_info['qualitative']}\n"

        # Add tools if present
        tools = step.get("tools", [])
        if tools:
            message += f"🔧 Tools: {', '.join(tools)}\n"

        return message


class ActionNavigateNext(Action):
    """Navigate to next step."""

    def name(self) -> str:
        return "action_navigate_next"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        recipe_data = tracker.get_slot("recipe_data")
        current_step = tracker.get_slot("current_step") or 0
        tracker.get_slot("total_steps") or 0

        if not recipe_data:
            dispatcher.utter_message(text="No recipe loaded.")
            return []

        steps = recipe_data.get("steps", [])

        if current_step >= len(steps):
            dispatcher.utter_message(text="🎉 You've completed all steps!")
            return []

        new_step = current_step + 1
        step = steps[new_step - 1]

        message = ActionShowCurrentStep()._format_step(step, new_step, len(steps))
        dispatcher.utter_message(text=message)

        return [SlotSet("current_step", new_step)]


class ActionNavigatePrevious(Action):
    """Navigate to previous step."""

    def name(self) -> str:
        return "action_navigate_previous"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        recipe_data = tracker.get_slot("recipe_data")
        current_step = tracker.get_slot("current_step") or 0

        if not recipe_data:
            dispatcher.utter_message(text="No recipe loaded.")
            return []

        if current_step <= 1:
            dispatcher.utter_message(text="You're already at the first step.")
            return []

        steps = recipe_data.get("steps", [])
        new_step = current_step - 1
        step = steps[new_step - 1]

        message = ActionShowCurrentStep()._format_step(step, new_step, len(steps))
        dispatcher.utter_message(text=message)

        return [SlotSet("current_step", new_step)]


class ActionNavigateFirst(Action):
    """Navigate to first step."""

    def name(self) -> str:
        return "action_navigate_first"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        recipe_data = tracker.get_slot("recipe_data")

        if not recipe_data:
            dispatcher.utter_message(text="No recipe loaded.")
            return []

        steps = recipe_data.get("steps", [])
        if not steps:
            dispatcher.utter_message(text="No steps found.")
            return []

        step = steps[0]
        message = ActionShowCurrentStep()._format_step(step, 1, len(steps))
        dispatcher.utter_message(text=message)

        return [SlotSet("current_step", 1)]


class ActionNavigateSpecific(Action):
    """Navigate to specific step number."""

    def name(self) -> str:
        return "action_navigate_specific"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        recipe_data = tracker.get_slot("recipe_data")

        # Extract step number from entities
        step_number = None
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == "step_number":
                try:
                    step_number = int(entity.get("value"))
                except ValueError:
                    continue

        if not recipe_data:
            dispatcher.utter_message(text="No recipe loaded.")
            return []

        if step_number is None:
            dispatcher.utter_message(text="Please specify which step number.")
            return []

        steps = recipe_data.get("steps", [])

        if step_number < 1 or step_number > len(steps):
            dispatcher.utter_message(text=f"Invalid step number. Recipe has {len(steps)} steps.")
            return []

        step = steps[step_number - 1]
        message = ActionShowCurrentStep()._format_step(step, step_number, len(steps))
        dispatcher.utter_message(text=message)

        return [SlotSet("current_step", step_number)]


class ActionAnswerTemperature(Action):
    """Answer temperature-related questions."""

    def name(self) -> str:
        return "action_answer_temperature"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        recipe_data = tracker.get_slot("recipe_data")
        current_step = tracker.get_slot("current_step") or 0

        if not recipe_data or current_step < 1:
            dispatcher.utter_message(text="No active step.")
            return []

        steps = recipe_data.get("steps", [])
        step = steps[current_step - 1]

        temp_info = step.get("temperature", {})

        if not temp_info:
            dispatcher.utter_message(text="No temperature specified for this step.")
            return []

        if "value" in temp_info:
            message = f"🌡️ Set temperature to {temp_info['value']}°{temp_info.get('unit', 'F')}"
        elif "qualitative" in temp_info:
            message = f"🌡️ Use {temp_info['qualitative']} heat"
        else:
            message = "Temperature information not clearly specified."

        dispatcher.utter_message(text=message)
        return []


class ActionAnswerTime(Action):
    """Answer time-related questions."""

    def name(self) -> str:
        return "action_answer_time"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        recipe_data = tracker.get_slot("recipe_data")
        current_step = tracker.get_slot("current_step") or 0

        if not recipe_data or current_step < 1:
            dispatcher.utter_message(text="No active step.")
            return []

        steps = recipe_data.get("steps", [])
        step = steps[current_step - 1]

        time_info = step.get("time", {})

        if not time_info:
            dispatcher.utter_message(text="No time specified for this step.")
            return []

        if "duration" in time_info:
            message = f"⏱️  Cook for {time_info['duration']} minutes"
        elif "range_start" in time_info and "range_end" in time_info:
            message = f"⏱️  Cook for {time_info['range_start']}-{time_info['range_end']} minutes"
        elif "until" in time_info:
            message = f"⏱️  Cook until {time_info['until']}"
        else:
            message = "Time information not clearly specified."

        dispatcher.utter_message(text=message)
        return []


class ActionAnswerQuantity(Action):
    """Answer ingredient quantity questions."""

    def name(self) -> str:
        return "action_answer_quantity"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        recipe_data = tracker.get_slot("recipe_data")

        # Extract ingredient from entities
        ingredient_name = None
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == "ingredient":
                ingredient_name = entity.get("value")
                break

        if not recipe_data:
            dispatcher.utter_message(text="No recipe loaded.")
            return []

        if not ingredient_name:
            dispatcher.utter_message(text="Which ingredient are you asking about?")
            return []

        # Search for ingredient in recipe
        ingredients = recipe_data.get("ingredients", [])
        found = None

        for ing in ingredients:
            if ingredient_name.lower() in ing.get("name", "").lower():
                found = ing
                break

        if not found:
            dispatcher.utter_message(text=f"I couldn't find {ingredient_name} in this recipe.")
            return [SlotSet("last_mentioned_ingredient", ingredient_name)]

        quantity = found.get("quantity", "")
        unit = found.get("unit", "")
        name = found.get("name", "")

        message = f"📏 {name}: "
        if quantity:
            message += f"{quantity} "
        if unit:
            message += unit
        else:
            message += "to taste"

        dispatcher.utter_message(text=message)
        return [SlotSet("last_mentioned_ingredient", name)]


class ActionAnswerSubstitution(Action):
    """Answer ingredient substitution questions."""

    def name(self) -> str:
        return "action_answer_substitution"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        # Extract ingredient from entities
        ingredient_name = None
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == "ingredient":
                ingredient_name = entity.get("value")
                break

        if not ingredient_name:
            dispatcher.utter_message(text="Which ingredient do you want to substitute?")
            return []

        search_term = ingredient_name.strip().replace(" ", "+")
        youtube_results = search_youtube(search_term, max_results=3)
        duckduckgo_results = search_duckduckgo(search_term, search_type="text", max_results=3)

        if youtube_results:
            message = f"🔍 For substitutions of {ingredient_name}, check:\n• YouTube: {youtube_results[0].url}"
            dispatcher.utter_message(text=message)
        if duckduckgo_results:
            message = f"\n• Web search: {duckduckgo_results[0].url}"
            dispatcher.utter_message(text=message)

        dispatcher.utter_message(text=message)
        return []


class ActionExternalSearch(Action):
    """Handle how-to and definition questions with external search."""

    def name(self) -> str:
        return "action_external_search"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        # Extract search term from entities
        search_term = None
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == "search_term":
                search_term = entity.get("value")
                break

        # TODO: improve the extraction of search term from message
        # If no entity, try to extract from message
        if not search_term:
            message_text = tracker.latest_message.get("text", "")
            # Simple extraction: remove common question words
            search_term = message_text.replace("how do I ", "").replace("how to ", "")
            search_term = search_term.replace("what is ", "").replace("what's ", "")
            search_term = search_term.strip("?")

        if not search_term:
            dispatcher.utter_message(text="What would you like to learn about?")
            return []

        search_term = search_term.strip().replace(" ", "+")
        results = search_youtube(search_term, max_results=3)
        if results:
            message = f"🔍 To learn about '{search_term}':\n• YouTube tutorial: {results[0].url}"
            dispatcher.utter_message(text=message)

        results = search_duckduckgo(search_term, search_type="text", max_results=3)
        if results:
            message = f"\n• Web search: {results[0].url}"
            dispatcher.utter_message(text=message)

        return []


class ActionUpdateContext(Action):
    """Update conversation context based on current step."""

    def name(self) -> str:
        return "action_update_context"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        recipe_data = tracker.get_slot("recipe_data")
        current_step = tracker.get_slot("current_step") or 0

        if not recipe_data or current_step < 1:
            return []

        steps = recipe_data.get("steps", [])
        if current_step > len(steps):
            return []

        step = steps[current_step - 1]

        # Extract context information from step
        methods = step.get("methods", [])
        tools = step.get("tools", [])

        # Store last action and tool for vague reference resolution
        last_action = methods[0] if methods else None
        last_tool = tools[0] if tools else None

        return [
            SlotSet("last_action", last_action),
            SlotSet("last_tool", last_tool),
        ]


class ValidateRecipeUrlForm(Action):
    """Validate recipe URL form."""

    def name(self) -> str:
        return "validate_recipe_url_form"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        recipe_url = tracker.get_slot("recipe_url")

        if not recipe_url:
            return [SlotSet("recipe_url", None)]

        # Basic URL validation
        if not recipe_url.startswith("http"):
            dispatcher.utter_message(text="Please provide a valid URL starting with http or https.")
            return [SlotSet("recipe_url", None)]

        # Check if it's an AllRecipes URL
        if "allrecipes.com" not in recipe_url.lower():
            dispatcher.utter_message(text="Currently only AllRecipes.com URLs are supported.")
            return [SlotSet("recipe_url", None)]

        return [SlotSet("recipe_url", recipe_url)]
