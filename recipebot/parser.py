"""Parser for recipes."""

from recipebot.model import Direction


class Parser:
    def __init__(self, name: str):
        self.name = name

    def parse(self, text: str) -> Direction:
        raise NotImplementedError("Subclasses must implement this method")


class SemanticParser(Parser):
    def __init__(self, model: str):
        super().__init__("semantic")
        self.model = model

    def parse(self, text: str) -> Direction:
        raise NotImplementedError("Subclasses must implement this method")


class LLMParse(Parser):
    def __init__(self, model: str):
        super().__init__("llm")
        self.model = model

    def parse(self, text: str) -> Direction:
        raise NotImplementedError("Subclasses must implement this method")
