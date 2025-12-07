"""LLM-only recipe assistant using Google Gemini 2.5 Flash Lite."""

import os
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv

from recipebot.crawler import extract_title_from_url, scrape_recipe

# Load environment variables
load_dotenv("gemini.env")

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


def format_recipe_for_llm(url: str, ingredients: list, directions: list[str]) -> str:
    """Format recipe data as text for LLM context."""
    title = extract_title_from_url(url)
    
    recipe_text = f"RECIPE: {title}\n"
    recipe_text += f"URL: {url}\n\n"
    
    recipe_text += "INGREDIENTS:\n"
    for i, ing in enumerate(ingredients, 1):
        parts = []
        if ing.quantity:
            parts.append(ing.quantity)
        if ing.unit:
            parts.append(ing.unit)
        if ing.name:
            parts.append(ing.name)
        if ing.preparation:
            parts.append(f"({ing.preparation})")
        if ing.misc:
            parts.append(ing.misc)
        
        recipe_text += f"{i}. {' '.join(parts)}\n"
    
    recipe_text += "\nDIRECTIONS:\n"
    for i, direction in enumerate(directions, 1):
        recipe_text += f"{i}. {direction}\n"
    
    return recipe_text


SYSTEM_PROMPT = """You are a knowledgeable and friendly culinary assistant designed to help users understand and follow recipes. Your primary role is to interpret recipe information, answer questions, and guide users through the cooking process.

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

3. **Conversational Guidance**: You maintain context throughout the conversation, remember what the user has asked, and provide helpful, contextual responses.

## Interaction Style

- **Be Clear and Concise**: Provide direct answers without unnecessary verbosity
- **Be Helpful**: Offer practical tips, alternatives, and suggestions when relevant
- **Be Accurate**: Base all answers strictly on the recipe information provided
- **Be Friendly**: Maintain a warm, supportive, and encouraging tone
- **Be Proactive**: When appropriate, offer additional helpful information (e.g., "You'll need a large mixing bowl for this step")

## Recipe Information Format

When a recipe is loaded, you will receive:
- Recipe title and URL
- A numbered list of ingredients with quantities, units, names, and preparation notes
- A numbered list of cooking directions/steps

## Answering Guidelines

1. **Ingredient Questions**: 
   - Provide exact quantities and units from the recipe
   - If asked about substitutions, suggest appropriate alternatives based on cooking knowledge
   - Clarify preparation requirements (e.g., "chopped", "diced", "at room temperature")

2. **Step Questions**:
   - Reference specific step numbers when relevant
   - Break down complex steps into simpler explanations if needed
   - Explain cooking techniques that might be unfamiliar

3. **Time and Temperature**:
   - Provide exact values from the recipe when available
   - Explain what to look for if times are approximate (e.g., "until golden brown")

4. **Tools and Equipment**:
   - Identify required tools from step descriptions
   - Suggest alternatives if specific tools aren't available

5. **General Questions**:
   - Use your culinary knowledge to provide helpful context
   - Always ground answers in the recipe when possible
   - If information isn't in the recipe, say so but offer general guidance

## Conversation Management

- Remember the recipe context throughout the conversation
- If the user asks about something not in the recipe, acknowledge this but provide helpful general information
- If a question is ambiguous, ask for clarification
- When appropriate, guide users to the next logical step in the recipe

## Example Interactions

User: "What ingredients do I need?"
You: "Based on the recipe, you'll need: [list ingredients with quantities]"

User: "How long do I cook this?"
You: "According to step X, you should cook for [time]. Look for [visual indicator] to know when it's done."

User: "Can I substitute butter for oil?"
You: "Yes, you can typically substitute butter for oil in this recipe. Use the same amount, but note that butter has a lower smoke point, so adjust the heat slightly if needed."

User: "What does 'fold' mean?"
You: "Folding is a gentle mixing technique used to combine ingredients without deflating them. Use a spatula to cut through the center, scrape along the bottom, and bring the mixture up and over the top. Repeat until combined."

Remember: Your goal is to make cooking accessible and enjoyable. Be patient, clear, and helpful in all your responses."""


class RecipeAssistant:
    """LLM-only recipe assistant using Gemini 2.5 Flash Lite."""
    
    def __init__(self):
        """Initialize the assistant with Gemini model."""
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Initialize Gemini model - try gemini-2.5-flash-lite first, then fallbacks
        model_names = [
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
        ]
        
        self.model = None
        for model_name in model_names:
            try:
                self.model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=SYSTEM_PROMPT
                )
                # Test if model works by checking if it's accessible
                break
            except Exception:
                continue
        
        if self.model is None:
            raise ValueError(f"Could not initialize any Gemini model. Tried: {', '.join(model_names)}")
        
        # Chat session for maintaining conversation history
        self.chat = None
        self.current_recipe: str | None = None
        self.current_recipe_text: str | None = None
    
    def load_recipe(self, url: str) -> str:
        """Load a recipe from URL and return formatted text."""
        try:
            ingredients, directions = scrape_recipe(url)
            if not ingredients or not directions:
                raise ValueError(f"Failed to scrape recipe from {url}")
            
            recipe_text = format_recipe_for_llm(url, ingredients, directions)
            self.current_recipe = url
            self.current_recipe_text = recipe_text
            
            # Start new chat session with recipe context
            self.chat = self.model.start_chat(history=[])
            
            # Send recipe context to the model
            prompt = f"Please load this recipe:\n\n{recipe_text}"
            response = self.chat.send_message(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                ),
            )
            
            acknowledgment = response.text
            return f"Recipe loaded successfully!\n\n{acknowledgment}"
            
        except Exception as e:
            raise ValueError(f"Failed to load recipe: {e}") from e
    
    def ask(self, question: str) -> str:
        """Ask a question about the current recipe."""
        if not self.current_recipe_text or not self.chat:
            return "No recipe loaded. Please provide a recipe URL first."
        
        # Generate response using chat session (maintains history automatically)
        try:
            response = self.chat.send_message(
                question,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                ),
            )
            
            return response.text
            
        except Exception as e:
            return f"Error generating response: {e}"
    
    def reset(self):
        """Reset conversation history and current recipe."""
        self.chat = None
        self.current_recipe = None
        self.current_recipe_text = None

