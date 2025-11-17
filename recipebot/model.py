from typing import Literal

from pydantic import BaseModel, Field


class Ingredient(BaseModel):
    name: str = Field(..., description="The name of the ingredient")
    quantity: str = Field(..., description="The quantity of the ingredient")
    unit: str | None = Field(default=None, description="The unit of the ingredient")
    preparation: str | None = Field(default=None, description="The preparation of the ingredient")
    misc: str | None = Field(default=None, description="Any additional information about the ingredient")


# {
#     "step_number": int,
#     "description": str,
#     "ingredients": [list of ingredient names],
#     "tools": [list of tools],
#     "methods": [list of methods],
#     "time": {
#         "duration": str or dict of sub-times,
#     },
#     "temperature": {
#         "oven": str (optional),
#         "<ingredient>": str (optional)
#     }
# }


class Step(BaseModel):
    step_number: int = Field(..., description="The step number")
    description: str = Field(..., description="The description of the step")
    ingredients: list[Ingredient] = Field(default_factory=list, description="The ingredients used in the step")
    tools: list[str] = Field(default_factory=list, description="The tools used in the step")
    methods: list[str] = Field(default_factory=list, description="The methods used in the step")
    time: dict[str, str | int] = Field(default_factory=dict, description="The time required for the step")
    temperature: dict[str, str] = Field(default_factory=dict, description="The temperature required for the step")
    actionable: bool = Field(default=True, description="Whether the method is actionable or advices")
    is_prepared: bool = Field(default=False, description="Whether the step is use to prepare something for next step")
    info_type: Literal["warning", "advice", "observation"] | None = Field(
        default=None, description="The type of the step"
    )


class Recipe(BaseModel):
    title: str = Field(..., description="The title of the recipe")
    ingredients: list[Ingredient] = Field(..., description="The ingredients of the recipe")
    directions: list[str] = Field(..., description="The directions of the recipe")
    steps: list[Step] = Field(..., description="The steps parsed from directions of the recipe")


class Query(BaseModel):
    description: str = Field(..., description="The input query")
    query_type: Literal["Action", "Object", "Modifier", "Context"] = Field(..., description="The type of the query")


class Visitor:
    def __init__(self, recipe: Recipe):
        self.recipe = recipe
        self.current_step = 0

    def show_ingredients(self):
        pass

    def show_directions(self):
        pass

    def show_current_step(self):
        pass

    def move_to_next_step(self):
        self.current_step += 1
        self.show_current_step()

    def move_to_previous_step(self):
        self.current_step -= 1
        self.show_current_step()

    def show_recipe(self):
        self.show_ingredients()
        self.show_directions()
