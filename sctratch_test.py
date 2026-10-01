# from tools import search_listings
# from utils.data_loader import load_listings, get_example_wardrobe, get_empty_wardrobe
# results = search_listings(description="graphic tee")
# print(len(results))
# for r in results:
#     print(r["id"], r["title"])

from tools import suggest_outfit
from utils.data_loader import get_example_wardrobe, load_listings, get_empty_wardrobe
print(suggest_outfit(load_listings()[0], get_example_wardrobe()))