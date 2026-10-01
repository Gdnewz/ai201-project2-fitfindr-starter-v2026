from tools import create_fit_card, suggest_outfit
from utils.data_loader import load_listings, get_example_wardrobe

item = load_listings()[0]
outfit = suggest_outfit(item, get_example_wardrobe())
print(create_fit_card(outfit, item))
print("---")
print(create_fit_card("", item))