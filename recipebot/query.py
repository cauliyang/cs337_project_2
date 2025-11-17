from enum import Enum

from pydantic import BaseModel

from recipebot.model import Query


class QuestionCategory(str, Enum):
    """High-level intents the chatbot understands."""

    RECIPE_DISPLAY = "recipe_display"
    NAVIGATION = "navigation"
    STEP_PARAMETER = "step_parameter"
    CLARIFICATION = "clarification"
    PROCEDURE = "procedure"
    QUANTITY = "quantity"
    UNKNOWN = "unknown"


# Hard-coded phrase snippets for each category.
_CATEGORY_PATTERNS: dict[QuestionCategory, tuple[str, ...]] = {
    QuestionCategory.RECIPE_DISPLAY: (
        "show me the ingredients",
        "show the ingredients",
        "display the recipe",
        "show me the recipe",
        "ingredients list",
        "list the ingredients",
        "show ingredients",
        "show the directions",
        "show me the steps",
    ),
    QuestionCategory.NAVIGATION: (
        "go back one step",
        "go back",
        "previous step",
        "go to the next step",
        "next step",
        "what’s next",
        "what's next",
        "repeat please",
        "repeat that",
        "what was that again",
        "take me to the first step",
        "start over",
        "begin again",
    ),
    QuestionCategory.STEP_PARAMETER: (
        "how much salt do i need",
        "what temperature should the oven be",
        "how long do i bake",
        "how long do i cook",
        "when is it done",
        "what can i use instead of",
        "is there a substitute",
        "what should the oven be",
        "what temperature",
        "how long should i",
    ),
    QuestionCategory.CLARIFICATION: (
        "what is a",
        "what does it mean",
        "what is an",
        "what is the meaning of",
        "what does that mean",
        "what is a whisk",
        "what is an immersion blender",
    ),
    QuestionCategory.PROCEDURE: (
        "how do i knead",
        "how do i mix",
        "how do i fold",
        "how do i chop",
        "how do i do that",
        "how do i do this",
        "how should i do that",
        "how should i do this",
        "how do i perform",
    ),
    QuestionCategory.QUANTITY: (
        "how much flour do i need",
        "how much sugar do i need",
        "how much of that do i need",
        "how much should i use",
        "how much butter",
        "how many eggs",
        "how many cups",
    ),
}


class ClassifiedQuestion(BaseModel):
    """Simple container for classifier output."""

    category: QuestionCategory
    query: Query


_CATEGORY_TO_QUERY_TYPE: dict[QuestionCategory, str] = {
    QuestionCategory.RECIPE_DISPLAY: "Object",
    QuestionCategory.NAVIGATION: "Action",
    QuestionCategory.STEP_PARAMETER: "Modifier",
    QuestionCategory.CLARIFICATION: "Context",
    QuestionCategory.PROCEDURE: "Action",
    QuestionCategory.QUANTITY: "Modifier",
    QuestionCategory.UNKNOWN: "Context",
}


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def classify_question(question: str) -> ClassifiedQuestion:
    """Classify a raw user utterance into a known category.

    Args:
        question: The raw user utterance.

    Returns:
        A ``ClassifiedQuestion`` containing the detected category and a
        ``Query`` instance describing the normalized question.
    """

    normalized = _normalize(question)

    for category, patterns in _CATEGORY_PATTERNS.items():
        if any(pattern in normalized for pattern in patterns):
            query_type = _CATEGORY_TO_QUERY_TYPE[category]
            return ClassifiedQuestion(
                category=category,
                query=Query(description=question, query_type=query_type),
            )

    # Default fallback when nothing matches.
    return ClassifiedQuestion(
        category=QuestionCategory.UNKNOWN,
        query=Query(
            description=question,
            query_type=_CATEGORY_TO_QUERY_TYPE[QuestionCategory.UNKNOWN],
        ),
    )
