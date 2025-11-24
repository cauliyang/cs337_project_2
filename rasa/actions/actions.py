"""Custom Rasa actions for recipe bot with spaCy-enhanced parsing."""

from typing import Any

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet

from recipebot.parser import parse_recipe
from recipebot.search import search_duckduckgo, search_youtube


def clean_url(url: str) -> str:
    """Clean URL from Slack formatting and other issues."""
    if not url:
        return url

    # Remove Slack's angle bracket formatting: <url> or <url|text>
    if url.startswith("<") and url.endswith(">"):
        url = url[1:-1]

    # Remove Slack's pipe separator and display text: <url|text>
    if "|" in url:
        url = url.split("|")[0]

    # Strip whitespace
    url = url.strip()

    return url


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

        # Clean URL from Slack formatting
        recipe_url = clean_url(recipe_url)

        if not recipe_url:
            dispatcher.utter_message(text="Invalid URL format.")
            return []

        try:
            # Parse recipe from URL using spaCy-enhanced parser
            # The parser now automatically uses spaCy for better accuracy
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

    def _format_time_info(self, time_info: dict) -> str:
        """Format time information in a generalized way.

        Args:
            time_info: Time dictionary from spaCy parser

        Returns:
            Formatted time string
        """
        if not time_info:
            return ""

        # Normalize unit abbreviations to full names for consistent handling
        def normalize_unit(unit: str) -> str:
            """Normalize unit to full name, handling abbreviations."""
            if not unit:
                return "minute"
            unit_lower = unit.lower()
            # Map abbreviations to full names
            unit_map = {
                "hr": "hour",
                "hrs": "hour",
                "h": "hour",
                "min": "minute",
                "mins": "minute",
                "m": "minute",
                "sec": "second",
                "secs": "second",
                "s": "second",
            }
            # Get full name or use as-is if already full name
            normalized = unit_map.get(unit_lower, unit_lower)
            # Pluralize if needed
            if normalized == "hour":
                return "hours"
            elif normalized == "minute":
                return "minutes"
            elif normalized == "second":
                return "seconds"
            # If already plural, return as-is
            return normalized

        # Handle time range
        if "duration_min" in time_info and "duration_max" in time_info:
            unit = time_info.get("unit", "minute")
            unit_display = normalize_unit(unit)
            return f"{time_info['duration_min']}-{time_info['duration_max']} {unit_display}"

        # Handle single duration
        if "duration" in time_info:
            duration = time_info["duration"]
            if time_info.get("type") == "qualitative":
                # Qualitative time (e.g., "until golden brown")
                return str(duration)
            else:
                # Numeric duration
                unit = time_info.get("unit", "minute")
                unit_display = normalize_unit(unit)
                return f"{duration} {unit_display}"

        # Fallback: show all key-value pairs
        parts = []
        for key, value in time_info.items():
            if key not in ["type", "unit"]:  # Skip metadata keys
                parts.append(f"{value}")
        return ", ".join(parts) if parts else ""

    def _format_step(self, step: dict, step_num: int, total: int) -> str:
        """Format step information for display (compatible with spaCy-enhanced parser)."""
        message = f"📍 Step {step_num}/{total}:\n"
        message += f"{step.get('description', '')}\n"

        # Add time if present (generalized for any spaCy parser output)
        time_info = step.get("time", {})
        if time_info:
            # Format time based on available keys
            time_str = self._format_time_info(time_info)
            if time_str:
                message += f"⏱️  Time: {time_str}\n"

        # Add temperature if present (generalized for any spaCy parser output)
        # Use validation to filter out invalid temperatures
        temp_info = step.get("temperature", {})
        if temp_info:
            import re

            for temp_key, temp_value in temp_info.items():
                # Validate temperature before displaying
                is_valid = False
                try:
                    temp_str = str(temp_value)
                    match = re.search(r"(\d+)", temp_str)
                    if match:
                        temp_num = int(match.group(1))
                        # Valid cooking temperature range: 50-600°F
                        if 50 <= temp_num <= 600:
                            is_valid = True
                except (ValueError, AttributeError):
                    # Check if it's qualitative (e.g., "medium heat")
                    if temp_value and len(str(temp_value)) > 2:
                        is_valid = True

                # Only show valid temperatures
                if is_valid:
                    display_key = temp_key.replace("_", " ").title()
                    message += f"🌡️  {display_key}: {temp_value}\n"

        # Add tools if present
        tools = step.get("tools", [])
        if tools:
            message += f"🔧 Tools: {', '.join(tools)}\n"

        # Add cooking methods if present
        methods = step.get("methods", [])
        if methods:
            message += f"👨‍🍳 Methods: {', '.join(methods[:3])}\n"  # Show first 3 methods

        # Add step classification info if present
        if step.get("is_prepared"):
            message += "📦 (Preparation step for later use)\n"
        if step.get("info_type") == "warning":
            message += "⚠️  Important note\n"
        elif step.get("info_type") == "advice":
            message += "💡 Tip\n"

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
        message_text = tracker.latest_message.get("text", "").lower()

        # Check if asking "what is X?" - this should trigger external search
        if any(phrase in message_text for phrase in ["what is", "what's", "define"]):
            # This is a definition question, not a parameter query
            # Redirect to external search
            return []  # Let fallback or external search handle it

        if not recipe_data or current_step < 1:
            dispatcher.utter_message(text="No active step.")
            return []

        steps = recipe_data.get("steps", [])
        step = steps[current_step - 1]

        temp_info = step.get("temperature", {})

        if not temp_info:
            dispatcher.utter_message(text="No temperature specified for this step.")
            return []

        # Filter out invalid temperatures (< 50°F or > 600°F are likely parsing errors)
        valid_temps = {}
        for temp_key, temp_value in temp_info.items():
            # Try to extract numeric value
            try:
                # Handle formats like "350°F", "350 degrees", "350"
                temp_str = str(temp_value)
                # Extract first number
                import re

                match = re.search(r"(\d+)", temp_str)
                if match:
                    temp_num = int(match.group(1))
                    # Validate temperature range
                    if 50 <= temp_num <= 600:
                        valid_temps[temp_key] = temp_value
            except (ValueError, AttributeError):
                # If we can't parse it, include it anyway (might be qualitative)
                if temp_value and len(str(temp_value)) > 2:
                    valid_temps[temp_key] = temp_value

        if not valid_temps:
            dispatcher.utter_message(text="No temperature specified for this step.")
            return []

        # Generalized handling for any temperature keys from spaCy parser
        message_parts = []
        for temp_key, temp_value in valid_temps.items():
            display_key = temp_key.replace("_", " ").title()
            message_parts.append(f"🌡️ {display_key}: {temp_value}")

        if message_parts:
            message = "\n".join(message_parts)
        else:
            message = "Temperature information not clearly specified."

        dispatcher.utter_message(text=message)
        return []


class ActionAnswerTime(Action):
    """Answer time-related questions including 'when is it done?' queries."""

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
        message_text = tracker.latest_message.get("text", "").lower()

        # Check if asking "what is X?" - this should trigger external search
        if any(phrase in message_text for phrase in ["what is", "what's", "define"]):
            # This is a definition question, not a parameter query
            # Redirect to external search
            return []  # Let fallback or external search handle it

        if not recipe_data or current_step < 1:
            dispatcher.utter_message(text="No active step.")
            return []

        steps = recipe_data.get("steps", [])
        step = steps[current_step - 1]

        time_info = step.get("time", {})

        # Check if asking "when is it done?" - look for done indicators
        is_done_question = any(
            phrase in message_text
            for phrase in ["when is it done", "how do i know", "when done", "is it ready", "how will i know"]
        )

        if is_done_question:
            # Look for done indicators in step description
            description = step.get("description", "").lower()
            done_indicators = []

            # Common done indicators
            if "until" in description:
                # Extract text after "until"
                until_idx = description.find("until")
                until_text = description[until_idx:].split(".")[0]
                done_indicators.append(until_text)

            if "golden" in description or "brown" in description:
                done_indicators.append("until golden brown")

            if "tender" in description:
                done_indicators.append("until tender")

            if "bubbl" in description:  # bubbling, bubbly
                done_indicators.append("until bubbling")

            if "thick" in description:
                done_indicators.append("until thickened")

            if "soft" in description:
                done_indicators.append("until soft")

            if "crisp" in description:
                done_indicators.append("until crispy")

            if done_indicators:
                message = f"✅ You'll know it's done: {', '.join(done_indicators)}"
                if time_info:
                    time_str = ActionShowCurrentStep()._format_time_info(time_info)
                    if time_str:
                        message += f"\n⏱️  Time: {time_str}"
                dispatcher.utter_message(text=message)
                return []
            else:
                # No indicators found, provide step description
                dispatcher.utter_message(
                    text=f"ℹ️  Step description: {step.get('description', 'No specific done indicator mentioned.')}"
                )
                return []

        # Standard time query
        if not time_info:
            # Check description for time clues
            description = step.get("description", "")
            if "until" in description.lower():
                dispatcher.utter_message(text=f"⏱️  No specific time, but the step says: {description}")
            else:
                dispatcher.utter_message(text="⏱️  No time specified for this step.")
            return []

        # Use generalized time formatting
        time_str = ActionShowCurrentStep()._format_time_info(time_info)
        if time_str:
            message = f"⏱️  Cook for {time_str}" if not time_str.startswith("until") else f"⏱️  {time_str}"
        else:
            message = "Time information not clearly specified."

        dispatcher.utter_message(text=message)
        return []


class ActionAnswerQuantity(Action):
    """Answer ingredient quantity questions with context-aware vague reference resolution."""

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
        current_step = tracker.get_slot("current_step") or 0

        if not recipe_data:
            dispatcher.utter_message(text="No recipe loaded.")
            return []

        # Extract ingredient from entities
        ingredient_name = None
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == "ingredient":
                ingredient_name = entity.get("value")
                break

        # Handle vague references: "that", "it", "this"
        if not ingredient_name or ingredient_name in ["that", "it", "this"]:
            # Try to resolve from current step context
            if current_step > 0:
                steps = recipe_data.get("steps", [])
                if current_step <= len(steps):
                    step = steps[current_step - 1]
                    step_ingredients = step.get("ingredients", [])

                    if step_ingredients:
                        # Use the first/most relevant ingredient from current step
                        ingredient_name = step_ingredients[0].get("name", "")
                        if ingredient_name:
                            dispatcher.utter_message(
                                text=f"I'll assume you're asking about {ingredient_name} from the current step."
                            )

            # If still no ingredient, check last mentioned
            if not ingredient_name or ingredient_name in ["that", "it", "this"]:
                last_mentioned = tracker.get_slot("last_mentioned_ingredient")
                if last_mentioned:
                    ingredient_name = last_mentioned
                    dispatcher.utter_message(text=f"I'll assume you mean {ingredient_name}.")
                else:
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
        preparation = found.get("preparation", "")

        message = f"📏 {name}: "
        if quantity:
            message += f"{quantity} "
        if unit:
            message += unit
        else:
            message += "to taste"

        if preparation:
            message += f" ({preparation})"

        dispatcher.utter_message(text=message)
        return [SlotSet("last_mentioned_ingredient", name)]


class ActionAnswerTool(Action):
    """Answer tool-related questions for current or specific step."""

    def name(self) -> str:
        return "action_answer_tool"

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
            dispatcher.utter_message(text="No recipe loaded. Please provide a recipe URL first.")
            return []

        # Extract step number if specified
        step_number = None
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == "step_number":
                try:
                    step_number = int(entity.get("value"))
                except ValueError:
                    continue

        # Use specified step or current step
        target_step = step_number if step_number else current_step

        if target_step < 1:
            dispatcher.utter_message(text="Please specify which step, or navigate to a step first.")
            return []

        steps = recipe_data.get("steps", [])
        if target_step > len(steps):
            dispatcher.utter_message(text=f"Step {target_step} doesn't exist. Recipe has {len(steps)} steps.")
            return []

        step = steps[target_step - 1]
        tools = step.get("tools", [])

        if tools:
            message = f"🔧 Tools needed for step {target_step}:\n"
            for i, tool in enumerate(tools, 1):
                message += f"  {i}. {tool}\n"
            dispatcher.utter_message(text=message)
        else:
            dispatcher.utter_message(text=f"No specific tools are required for step {target_step}.")

        return []


class ActionAnswerMethod(Action):
    """Answer cooking method questions for current or specific step."""

    def name(self) -> str:
        return "action_answer_method"

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
            dispatcher.utter_message(text="No recipe loaded. Please provide a recipe URL first.")
            return []

        # Extract step number if specified
        step_number = None
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == "step_number":
                try:
                    step_number = int(entity.get("value"))
                except ValueError:
                    continue

        # Use specified step or current step
        target_step = step_number if step_number else current_step

        if target_step < 1:
            dispatcher.utter_message(text="Please specify which step, or navigate to a step first.")
            return []

        steps = recipe_data.get("steps", [])
        if target_step > len(steps):
            dispatcher.utter_message(text=f"Step {target_step} doesn't exist. Recipe has {len(steps)} steps.")
            return []

        step = steps[target_step - 1]
        methods = step.get("methods", [])

        if methods:
            message = f"👨‍🍳 Cooking methods for step {target_step}:\n"
            for i, method in enumerate(methods, 1):
                message += f"  {i}. {method}\n"
            dispatcher.utter_message(text=message)
        else:
            dispatcher.utter_message(text=f"No specific cooking methods identified for step {target_step}.")

        return []


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
        recipe_data = tracker.get_slot("recipe_data")

        # Extract ingredient from entities
        ingredient_name = None
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == "ingredient":
                ingredient_name = entity.get("value")
                break

        if not ingredient_name:
            dispatcher.utter_message(text="Which ingredient do you want to substitute?")
            return []

        # First, check if ingredient exists in current recipe
        if recipe_data:
            ingredients = recipe_data.get("ingredients", [])
            found_in_recipe = False
            for ing in ingredients:
                if ingredient_name.lower() in ing.get("name", "").lower():
                    found_in_recipe = True
                    ingredient_name = ing.get("name", ingredient_name)  # Use exact name from recipe
                    break

            if found_in_recipe:
                dispatcher.utter_message(
                    text=f"Looking for substitution options for {ingredient_name} from your recipe..."
                )

        # External search for substitutions
        search_term = ingredient_name.strip().replace(" ", "+")
        youtube_results = search_youtube(search_term, max_results=3)
        duckduckgo_results = search_duckduckgo(search_term, search_type="text", max_results=3)

        message_parts = []
        if youtube_results:
            message_parts.append(f"🔍 For substitutions of {ingredient_name}:\n• YouTube: {youtube_results[0].url}")
        if duckduckgo_results:
            message_parts.append(f"• Web search: {duckduckgo_results[0].url}")

        if message_parts:
            dispatcher.utter_message(text="\n".join(message_parts))
        else:
            dispatcher.utter_message(text=f"Couldn't find substitution information for {ingredient_name}.")

        return []


class ActionExternalSearch(Action):
    """Handle how-to and definition questions - check recipe first, then external search."""

    def name(self) -> str:
        return "action_external_search"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the action."""
        recipe_data = tracker.get_slot("recipe_data")
        current_step = tracker.get_slot("current_step") or 0
        message_text = tracker.latest_message.get("text", "").lower()

        # Check if "how to" question - these should always get external tutorials
        is_how_to_question = any(phrase in message_text for phrase in ["how to", "how do i", "how can i"])

        # Handle vague procedure questions: "how do I do that?" "how should I do this?"
        is_vague_procedure = any(phrase in message_text for phrase in ["do that", "do this", "do it"])
        resolved_method = None

        if is_vague_procedure and is_how_to_question and recipe_data and current_step > 0:
            # Resolve "that/this/it" from current step's main action
            steps = recipe_data.get("steps", [])
            if current_step <= len(steps):
                step = steps[current_step - 1]
                methods = step.get("methods", [])

                if methods:
                    # Use the primary method from current step
                    resolved_method = methods[0]
                    dispatcher.utter_message(
                        text=f"I'll search for how to {resolved_method} (from your current step)..."
                    )

        # If it's a "how to" question, skip recipe check and go straight to external search
        # Users asking "how to" want detailed tutorials, not just method names
        if not is_how_to_question and recipe_data and current_step > 0:
            steps = recipe_data.get("steps", [])
            if current_step <= len(steps):
                step = steps[current_step - 1]

                # Check if asking about tools (but not "how to" questions)
                if any(
                    word in message_text
                    for word in ["tool", "tools", "equipment", "utensil", "what tool", "which tool"]
                ):
                    tools = step.get("tools", [])
                    if tools:
                        message = f"🔧 For step {current_step}, you'll need:\n"
                        for i, tool in enumerate(tools, 1):
                            message += f"  {i}. {tool}\n"
                        dispatcher.utter_message(text=message)
                        return []
                    else:
                        # No tools found in step, but still answer from recipe context
                        dispatcher.utter_message(
                            text=f"No specific tools mentioned in step {current_step}. Check the step description for details."  # noqa: E501
                        )
                        return []

                # Check if asking about methods/techniques (but not "how to" questions)
                if any(
                    word in message_text
                    for word in ["method", "technique", "what method", "which method", "what technique"]
                ):
                    methods = step.get("methods", [])
                    if methods:
                        message = f"👨‍🍳 Methods used in step {current_step}:\n"
                        for i, method in enumerate(methods, 1):
                            message += f"  {i}. {method}\n"
                        message += f"\nStep description: {step.get('description', '')}"
                        dispatcher.utter_message(text=message)
                        return []
                    else:
                        # No methods found, but still answer from recipe context
                        dispatcher.utter_message(
                            text=f"No specific methods identified in step {current_step}. Check the step description for details."  # noqa: E501
                        )
                        return []

                # Check if asking about ingredients in current step
                if any(
                    word in message_text
                    for word in ["ingredient", "ingredients", "what ingredient", "which ingredient"]
                ):
                    step_ingredients = step.get("ingredients", [])
                    if step_ingredients:
                        message = f"🥘 Ingredients used in step {current_step}:\n"
                        for i, ing in enumerate(step_ingredients, 1):
                            name = ing.get("name", "")
                            quantity = ing.get("quantity", "")
                            unit = ing.get("unit", "")
                            if quantity or unit:
                                ing_str = f"{quantity} {unit}".strip() if unit else quantity
                                message += f"  {i}. {name} ({ing_str})\n"
                            else:
                                message += f"  {i}. {name}\n"
                        dispatcher.utter_message(text=message)
                        return []
                    else:
                        # No ingredients found in step
                        dispatcher.utter_message(
                            text=f"No specific ingredients mentioned in step {current_step}. Check the step description for details."  # noqa: E501
                        )
                        return []

        # If not found in recipe data, fall back to external search
        # Use resolved method if available (from vague reference)
        search_term = resolved_method if resolved_method else None

        # Extract search term from entities if not already resolved
        if not search_term:
            for entity in tracker.latest_message.get("entities", []):
                if entity.get("entity") == "search_term":
                    search_term = entity.get("value")
                    break

        # If no entity, try to extract from message
        if not search_term:
            # Simple extraction: remove common question words
            search_term = message_text.replace("how do i ", "").replace("how to ", "")
            search_term = search_term.replace("what is ", "").replace("what's ", "")
            search_term = search_term.replace("which ", "").replace("what ", "")
            search_term = search_term.strip("?").strip()

        if not search_term or len(search_term) < 3:
            dispatcher.utter_message(text="What would you like to learn about?")
            return []

        # Perform external search
        dispatcher.utter_message(text=f"🔍 Searching for information about '{search_term}'...")
        search_term_encoded = search_term.replace(" ", "+")

        message_parts = []
        results = search_youtube(search_term_encoded, max_results=3)
        if results:
            message_parts.append(f"• YouTube tutorial: {results[0].url}")

        results = search_duckduckgo(search_term_encoded, search_type="text", max_results=3)
        if results:
            message_parts.append(f"• Web search: {results[0].url}")

        if message_parts:
            dispatcher.utter_message(text="\n".join(message_parts))
        else:
            dispatcher.utter_message(text="Sorry, couldn't find relevant information.")

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
        step_ingredients = step.get("ingredients", [])

        # Store last action, tool, and ingredient for vague reference resolution
        last_action = methods[0] if methods else None
        last_tool = tools[0] if tools else None
        last_ingredient = step_ingredients[0].get("name") if step_ingredients else None

        return [
            SlotSet("last_action", last_action),
            SlotSet("last_tool", last_tool),
            SlotSet("last_mentioned_ingredient", last_ingredient),
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

        # Clean URL from Slack formatting
        recipe_url = clean_url(recipe_url)

        if not recipe_url:
            dispatcher.utter_message(text="Invalid URL format.")
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
