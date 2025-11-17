from rich import print

from recipebot.parser import extract_tools_from_text


def test_tool_extraction(directions):
    for test in directions:
        tools = extract_tools_from_text(test)
        print(f"\nText: {test}")
        print(f"Tools: {', '.join(tools) if tools else 'None'}")
