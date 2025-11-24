"""SpaCy-based NLP utilities for recipe parsing optimization."""

import re

import spacy
from spacy.matcher import Matcher, PhraseMatcher
from spacy.tokens import Doc, Span

# Global spaCy model (lazy loaded)
_nlp = None


def get_nlp() -> spacy.language.Language:
    """Get or initialize the spaCy NLP model.

    Returns:
        Loaded spaCy model
    """
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_md")
        except OSError:
            raise RuntimeError("Failed to load spaCy model. Please ensure it is installed and available.")  # noqa: B904
    return _nlp


def create_time_matcher(nlp: spacy.language.Language) -> Matcher:
    """Create a spaCy matcher for time expressions.

    Args:
        nlp: spaCy language model

    Returns:
        Configured Matcher for time patterns
    """
    matcher = Matcher(nlp.vocab)

    # Pattern: "30 minutes", "2 hours", "5 seconds"
    matcher.add(
        "TIME_DURATION",
        [
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["hour", "hours", "hr", "hrs", "h"]}}],
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["minute", "minutes", "min", "mins", "m"]}}],
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["second", "seconds", "sec", "secs", "s"]}}],
        ],
    )

    # Pattern: "2-3 hours", "30 to 45 minutes"
    matcher.add(
        "TIME_RANGE",
        [
            [
                {"LIKE_NUM": True},
                {"TEXT": {"IN": ["-", "to", "or"]}},
                {"LIKE_NUM": True},
                {
                    "LOWER": {
                        "IN": [
                            "hour",
                            "hours",
                            "hr",
                            "hrs",
                            "minute",
                            "minutes",
                            "min",
                            "mins",
                            "second",
                            "seconds",
                            "sec",
                            "secs",
                        ]
                    }
                },
            ],
        ],
    )

    # Pattern: "for 30 minutes"
    matcher.add(
        "TIME_FOR",
        [
            [
                {"LOWER": "for"},
                {"LIKE_NUM": True},
                {
                    "LOWER": {
                        "IN": [
                            "hour",
                            "hours",
                            "hr",
                            "hrs",
                            "minute",
                            "minutes",
                            "min",
                            "mins",
                            "second",
                            "seconds",
                            "sec",
                            "secs",
                        ]
                    }
                },
            ],
        ],
    )

    # Pattern: "until golden brown", "until tender"
    matcher.add(
        "TIME_UNTIL",
        [
            [{"LOWER": "until"}, {"POS": {"IN": ["ADJ", "VERB", "NOUN"]}, "OP": "+"}],
        ],
    )

    return matcher


def create_temperature_matcher(nlp: spacy.language.Language) -> Matcher:
    """Create a spaCy matcher for temperature expressions.

    Args:
        nlp: spaCy language model

    Returns:
        Configured Matcher for temperature patterns
    """
    matcher = Matcher(nlp.vocab)

    # Pattern: "350 degrees F", "180°C"
    matcher.add(
        "TEMP_NUMERIC",
        [
            [
                {"LIKE_NUM": True},
                {"LOWER": {"IN": ["degree", "degrees", "°"]}, "OP": "?"},
                {"TEXT": {"REGEX": "^[FC]$"}},
            ],
            [{"LIKE_NUM": True}, {"TEXT": {"REGEX": "^°[FC]$"}}],
        ],
    )

    # Pattern: "medium heat", "low heat"
    matcher.add(
        "TEMP_QUALITATIVE",
        [
            [{"LOWER": {"IN": ["low", "medium", "high", "medium-low", "medium-high"]}}, {"LOWER": "heat"}],
        ],
    )

    # Pattern: "preheat to 350"
    matcher.add(
        "TEMP_PREHEAT",
        [
            [
                {"LOWER": {"IN": ["preheat", "preheating"]}},
                {"LOWER": {"IN": ["to", "at"]}, "OP": "?"},
                {"LIKE_NUM": True},
                {"LOWER": {"IN": ["degree", "degrees", "°"]}, "OP": "?"},
                {"TEXT": {"REGEX": "^[FC]$"}, "OP": "?"},
            ],
        ],
    )

    return matcher


def create_tool_phrase_matcher(nlp: spacy.language.Language, tools: set[str]) -> PhraseMatcher:
    """Create a PhraseMatcher for kitchen tools.

    Args:
        nlp: spaCy language model
        tools: Set of tool names to match

    Returns:
        Configured PhraseMatcher for tools
    """
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(tool) for tool in tools]
    matcher.add("TOOL", patterns)
    return matcher


def create_method_phrase_matcher(nlp: spacy.language.Language, methods: set[str]) -> PhraseMatcher:
    """Create a PhraseMatcher for cooking methods.

    Args:
        nlp: spaCy language model
        methods: Set of method names to match

    Returns:
        Configured PhraseMatcher for methods
    """
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(method) for method in methods]
    matcher.add("METHOD", patterns)
    return matcher


def extract_time_with_spacy(doc: Doc, time_matcher: Matcher) -> dict[str, str | int]:
    """Extract time information using spaCy matcher.

    Args:
        doc: spaCy Doc object
        time_matcher: Configured time matcher

    Returns:
        Dictionary with time information
    """
    time_info: dict[str, str | int] = {}
    matches = time_matcher(doc)

    for match_id, start, end in matches:
        span = doc[start:end]
        match_type = doc.vocab.strings[match_id]

        if match_type == "TIME_RANGE":
            # Extract min and max values
            numbers = [token for token in span if token.like_num]
            if len(numbers) >= 2:
                time_info["duration_min"] = int(float(numbers[0].text))
                time_info["duration_max"] = int(float(numbers[1].text))
                # Extract unit
                for token in span:
                    if token.lower_ in ["hour", "hours", "hr", "hrs"]:
                        time_info["unit"] = "hour"
                        break
                    elif token.lower_ in ["minute", "minutes", "min", "mins"]:
                        time_info["unit"] = "minute"
                        break
                    elif token.lower_ in ["second", "seconds", "sec", "secs"]:
                        time_info["unit"] = "second"
                        break
                return time_info

        elif match_type in ["TIME_DURATION", "TIME_FOR"]:
            # Extract single value
            for token in span:
                if token.like_num:
                    time_info["duration"] = int(float(token.text))
                elif token.lower_ in ["hour", "hours", "hr", "hrs"]:
                    time_info["unit"] = "hour"
                elif token.lower_ in ["minute", "minutes", "min", "mins"]:
                    time_info["unit"] = "minute"
                elif token.lower_ in ["second", "seconds", "sec", "secs"]:
                    time_info["unit"] = "second"

            if time_info:
                return time_info

        elif match_type == "TIME_UNTIL":
            # Qualitative time
            time_info["duration"] = span.text
            time_info["type"] = "qualitative"
            return time_info

    return time_info


def extract_temperature_with_spacy(doc: Doc, temp_matcher: Matcher) -> dict[str, str]:
    """Extract temperature information using spaCy matcher.

    Args:
        doc: spaCy Doc object
        temp_matcher: Configured temperature matcher

    Returns:
        Dictionary with temperature information
    """
    temp_info: dict[str, str] = {}
    matches = temp_matcher(doc)

    for match_id, start, end in matches:
        span = doc[start:end]
        match_type = doc.vocab.strings[match_id]

        if match_type in ["TEMP_NUMERIC", "TEMP_PREHEAT"]:
            # Extract numeric temperature
            temp = None
            unit = "F"  # Default to Fahrenheit

            for token in span:
                if token.like_num:
                    temp = token.text
                elif token.text in ["F", "C"]:
                    unit = token.text
                elif token.text in ["°F", "°C"]:
                    unit = token.text[1]

            if temp:
                temp_info["oven"] = f"{temp}°{unit}"
                return temp_info

        elif match_type == "TEMP_QUALITATIVE":
            # Qualitative heat
            temp_info["heat"] = span.text
            return temp_info

    return temp_info


def split_into_sentences_with_spacy(text: str, nlp: spacy.language.Language) -> list[str]:
    """Split text into sentences using spaCy's sentence segmentation.

    Args:
        text: Text to split
        nlp: spaCy language model

    Returns:
        List of sentence strings
    """
    doc = nlp(text)
    sentences = []

    for sent in doc.sents:
        sent_text = sent.text.strip()
        # Additional splitting for cooking-specific patterns
        # Split on ", then" and similar conjunctions
        if ", then" in sent_text.lower() or ", and then" in sent_text.lower():
            parts = re.split(r",\s+(and\s+)?then\s+", sent_text, flags=re.IGNORECASE)
            for i, part in enumerate(parts):
                if i > 0 and not part[0].isupper():
                    part = part[0].upper() + part[1:]
                if part.strip() and part.lower() not in ["then", "and then"]:
                    sentences.append(part.strip())
        else:
            sentences.append(sent_text)

    return sentences


def extract_verb_phrases(doc: Doc) -> list[Span]:
    """Extract verb phrases from a spaCy Doc.

    Args:
        doc: spaCy Doc object

    Returns:
        List of verb phrase spans
    """
    verb_phrases = []

    for token in doc:
        if token.pos_ == "VERB":
            # Get the subtree of the verb
            start = token.i
            end = token.i + 1

            # Extend to include direct objects and particles
            for child in token.children:
                if child.dep_ in ["dobj", "prt", "prep", "advmod"]:
                    if child.i < start:
                        start = child.i
                    if child.i + 1 > end:
                        end = child.i + 1

            verb_phrases.append(doc[start:end])

    return verb_phrases


def match_ingredient_with_spacy(ingredient_name: str, doc: Doc, nlp: spacy.language.Language) -> bool:
    """Check if an ingredient is mentioned in a Doc using semantic similarity.

    Args:
        ingredient_name: Name of ingredient to find
        doc: spaCy Doc to search in
        nlp: spaCy language model

    Returns:
        True if ingredient is found, False otherwise
    """
    ingredient_doc = nlp(ingredient_name.lower())
    doc_lower = doc.text.lower()

    # First try exact match
    if ingredient_name.lower() in doc_lower:
        return True

    # Try lemma-based matching
    ingredient_lemmas = set(token.lemma_ for token in ingredient_doc if not token.is_stop)

    for token in doc:
        if token.lemma_ in ingredient_lemmas and not token.is_stop:
            return True

    # Check noun chunks
    for chunk in doc.noun_chunks:
        chunk_lemmas = set(token.lemma_ for token in chunk if not token.is_stop)
        if chunk_lemmas & ingredient_lemmas:  # Intersection
            return True

    return False


def get_action_verbs(doc: Doc) -> list[str]:
    """Extract action verbs from a Doc.

    Args:
        doc: spaCy Doc object

    Returns:
        List of action verb lemmas
    """
    return [token.lemma_ for token in doc if token.pos_ == "VERB" and not token.is_stop]


def is_imperative_sentence(doc: Doc) -> bool:
    """Check if a sentence is in imperative mood (command).

    Args:
        doc: spaCy Doc object

    Returns:
        True if imperative, False otherwise
    """
    if len(doc) == 0:
        return False

    # Imperative sentences typically start with a verb (base form)
    first_token = doc[0]
    if first_token.pos_ == "VERB" and first_token.tag_ in ["VB", "VBP"]:
        return True

    # Check for common imperative patterns
    imperative_starters = {"add", "mix", "stir", "cook", "bake", "heat", "pour", "place", "remove"}
    if first_token.lemma_.lower() in imperative_starters:
        return True

    return False
