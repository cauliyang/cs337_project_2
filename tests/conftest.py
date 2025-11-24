import pytest

from recipebot.model import Ingredient


@pytest.fixture
def directions():
    return [
        "Preheat the oven to 375 degrees F (190 degrees C).",
        "Make the sauce: Heat oil in a large saucepan over medium-high heat. Add onion and garlic; cook and stir until translucent, about 5 minutes. Add ground beef and garlic powder; cook and stir until browned and crumbly, 5 to 7 minutes. Drain and discard grease.  Add spaghetti sauce, tomato sauce, and oregano; cover and simmer for 15 to 20 minutes.",  # noqa: E501
        "Make the lasagna: Mix mozzarella and provolone together in a medium bowl. Mix ricotta, milk, eggs, and oregano together in another bowl.",  # noqa: E501
        "Ladle sauce (just enough to cover) into the bottom of a 9x13-inch baking dish.  Layer sauce with three lasagna noodles, more sauce, ricotta mixture, and mozzarella mixture; repeat once more using all of remaining cheese mixtures. Layer with remaining three lasagna noodles and remaining sauce, then sprinkle Parmesan over top.",  # noqa: E501
        "Cover and bake in the preheated oven for 30 minutes. Uncover and continue to bake until cheese is melted and top is golden, about 15 minutes longer.",  # noqa: E501
    ]


@pytest.fixture
def ingredients():
    return [
        Ingredient(name="flour", quantity="2", unit="cups"),
        Ingredient(name="sugar", quantity="1", unit="cup"),
        Ingredient(name="salt", quantity="1", unit="teaspoon"),
        Ingredient(name="onions", quantity="2", unit=None),
        Ingredient(name="butter", quantity="1/2", unit="cup"),
        Ingredient(name="ground beef", quantity="1", unit="pound"),
        Ingredient(name="spaghetti sauce", quantity="1", unit="jar"),
        Ingredient(name="tomato sauce", quantity="1", unit="jar"),
        Ingredient(name="oregano", quantity="1", unit="teaspoon"),
        Ingredient(name="mozzarella", quantity="1", unit="cup"),
        Ingredient(name="provolone", quantity="1", unit="cup"),
        Ingredient(name="ricotta", quantity="1", unit="cup"),
    ]


@pytest.fixture
def urls() -> dict[str, list[str]]:
    return {
        "allrecipes": ["https://www.allrecipes.com/recipe/24074/alysias-basic-meat-lasagna/"],
        "seriouseats": ["https://www.seriouseats.com/pecan-pie-cheesecake-recipe-11843450"],
    }


@pytest.fixture
def allrecipes_url(urls) -> list[str]:
    return urls["allrecipes"]


@pytest.fixture
def seriouseats_url(urls) -> list[str]:
    return urls["seriouseats"]
