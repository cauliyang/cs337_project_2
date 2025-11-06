from recipebot.crawler import scrape_recipe

# Take user input
user_url = input("Enter the recipe URL: ").strip()

# Scrape the recipe
ingredients, directions = scrape_recipe(user_url)

# Print ingredients
print("Ingredients:")
for item in ingredients:
    print("-", item)

# Print directions
print("\nDirections:")
for i, step in enumerate(directions):
    print(f"Step {i+1}: {step}\n")
