from rich import print

from recipebot.search import search_duckduckgo, search_youtube


def test_search_youtube():
    # Example usage
    results = search_youtube("how to make salad", max_results=3)
    for video in results:
        print(video)


def test_search_web():
    result = search_duckduckgo("how to make salad", search_type="videos", max_results=5)
    print(result)
