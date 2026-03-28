"""
Simple keyword-based calorie and macro estimator for common foods.
Used for quick meal logging via Telegram when no explicit nutrition data is provided.
"""

# Per 100g or per unit (indicated in comments)
FOOD_DATA = {
    # Proteins
    'курча': {'kcal': 180, 'protein': 25, 'carbs': 0, 'fat': 8, 'unit': '100g'},
    'куря': {'kcal': 180, 'protein': 25, 'carbs': 0, 'fat': 8, 'unit': '100g'},
    'кур': {'kcal': 180, 'protein': 25, 'carbs': 0, 'fat': 8, 'unit': '100g'},
    'груд': {'kcal': 120, 'protein': 23, 'carbs': 0, 'fat': 2, 'unit': '100g'},
    'яйце': {'kcal': 70, 'protein': 6, 'carbs': 0, 'fat': 5, 'unit': 'pcs'},
    'яєц': {'kcal': 70, 'protein': 6, 'carbs': 0, 'fat': 5, 'unit': 'pcs'},
    'омлет': {'kcal': 180, 'protein': 12, 'carbs': 2, 'fat': 14, 'unit': '100g'},
    'яєшн': {'kcal': 150, 'protein': 10, 'carbs': 2, 'fat': 12, 'unit': '100g'},
    'риба': {'kcal': 100, 'protein': 18, 'carbs': 0, 'fat': 3, 'unit': '100g'},
    'лосос': {'kcal': 200, 'protein': 22, 'carbs': 0, 'fat': 12, 'unit': '100g'},
    'тунець': {'kcal': 130, 'protein': 28, 'carbs': 0, 'fat': 1, 'unit': '100g'},
    'стейк': {'kcal': 250, 'protein': 26, 'carbs': 0, 'fat': 16, 'unit': '100g'},
    'м\'ясо': {'kcal': 200, 'protein': 22, 'carbs': 0, 'fat': 12, 'unit': '100g'},
    'мясо': {'kcal': 200, 'protein': 22, 'carbs': 0, 'fat': 12, 'unit': '100g'},
    'свинина': {'kcal': 250, 'protein': 20, 'carbs': 0, 'fat': 18, 'unit': '100g'},
    'яловичина': {'kcal': 200, 'protein': 26, 'carbs': 0, 'fat': 10, 'unit': '100g'},
    'голубці': {'kcal': 180, 'protein': 12, 'carbs': 15, 'fat': 9, 'unit': '100g'},
    'ковбас': {'kcal': 300, 'protein': 12, 'carbs': 2, 'fat': 26, 'unit': '100g'},
    'шинк': {'kcal': 150, 'protein': 18, 'carbs': 1, 'fat': 9, 'unit': '100g'},

    # Carbs
    'рис': {'kcal': 130, 'protein': 2, 'carbs': 28, 'fat': 0, 'unit': '100g'},
    'гречк': {'kcal': 110, 'protein': 4, 'carbs': 22, 'fat': 1, 'unit': '100g'},
    'вівсян': {'kcal': 70, 'protein': 3, 'carbs': 12, 'fat': 2, 'unit': '100g'},
    'овсянк': {'kcal': 70, 'protein': 3, 'carbs': 12, 'fat': 2, 'unit': '100g'},
    'макарон': {'kcal': 140, 'protein': 5, 'carbs': 28, 'fat': 1, 'unit': '100g'},
    'паста': {'kcal': 140, 'protein': 5, 'carbs': 28, 'fat': 1, 'unit': '100g'},
    'хліб': {'kcal': 80, 'protein': 3, 'carbs': 16, 'fat': 1, 'unit': 'pcs'},
    'батон': {'kcal': 90, 'protein': 3, 'carbs': 18, 'fat': 1, 'unit': 'pcs'},
    'тост': {'kcal': 80, 'protein': 2, 'carbs': 14, 'fat': 2, 'unit': 'pcs'},
    'бутербр': {'kcal': 200, 'protein': 7, 'carbs': 22, 'fat': 10, 'unit': 'pcs'},
    'картоп': {'kcal': 80, 'protein': 2, 'carbs': 18, 'fat': 0, 'unit': '100g'},
    'пюре': {'kcal': 100, 'protein': 2, 'carbs': 20, 'fat': 2, 'unit': '100g'},
    'каша': {'kcal': 100, 'protein': 3, 'carbs': 18, 'fat': 2, 'unit': '100g'},

    # Dairy
    'сир': {'kcal': 100, 'protein': 12, 'carbs': 3, 'fat': 5, 'unit': '100g'},
    'творог': {'kcal': 100, 'protein': 12, 'carbs': 3, 'fat': 5, 'unit': '100g'},
    'творіг': {'kcal': 100, 'protein': 12, 'carbs': 3, 'fat': 5, 'unit': '100g'},
    'молоко': {'kcal': 60, 'protein': 3, 'carbs': 5, 'fat': 3, 'unit': '100ml'},
    'кефір': {'kcal': 50, 'protein': 3, 'carbs': 4, 'fat': 2, 'unit': '100ml'},
    'йогурт': {'kcal': 80, 'protein': 5, 'carbs': 8, 'fat': 3, 'unit': '100g'},
    'вершк': {'kcal': 200, 'protein': 2, 'carbs': 3, 'fat': 20, 'unit': '100ml'},
    'сметан': {'kcal': 150, 'protein': 2, 'carbs': 3, 'fat': 15, 'unit': '100g'},
    'масло': {'kcal': 750, 'protein': 1, 'carbs': 0, 'fat': 82, 'unit': '100g'},
    'м\'який сир': {'kcal': 180, 'protein': 10, 'carbs': 2, 'fat': 15, 'unit': '100g'},
    'моцарел': {'kcal': 280, 'protein': 18, 'carbs': 1, 'fat': 22, 'unit': '100g'},
    'пармезан': {'kcal': 380, 'protein': 35, 'carbs': 3, 'fat': 26, 'unit': '100g'},
    'бринза': {'kcal': 180, 'protein': 16, 'carbs': 1, 'fat': 12, 'unit': '100g'},

    # Fruits
    'яблук': {'kcal': 50, 'protein': 0, 'carbs': 12, 'fat': 0, 'unit': 'pcs'},
    'банан': {'kcal': 90, 'protein': 1, 'carbs': 22, 'fat': 0, 'unit': 'pcs'},
    'апельсин': {'kcal': 50, 'protein': 1, 'carbs': 12, 'fat': 0, 'unit': 'pcs'},
    'мандарин': {'kcal': 40, 'protein': 1, 'carbs': 9, 'fat': 0, 'unit': 'pcs'},
    'виноград': {'kcal': 70, 'protein': 1, 'carbs': 17, 'fat': 0, 'unit': '100g'},
    'полуниц': {'kcal': 35, 'protein': 1, 'carbs': 7, 'fat': 0, 'unit': '100g'},
    'чорниц': {'kcal': 35, 'protein': 0, 'carbs': 8, 'fat': 0, 'unit': '100g'},
    'фрукт': {'kcal': 50, 'protein': 0, 'carbs': 12, 'fat': 0, 'unit': '100g'},

    # Vegetables
    'овоч': {'kcal': 25, 'protein': 1, 'carbs': 5, 'fat': 0, 'unit': '100g'},
    'салат': {'kcal': 20, 'protein': 1, 'carbs': 3, 'fat': 0, 'unit': '100g'},
    'огірок': {'kcal': 15, 'protein': 1, 'carbs': 2, 'fat': 0, 'unit': 'pcs'},
    'помідор': {'kcal': 20, 'protein': 1, 'carbs': 4, 'fat': 0, 'unit': 'pcs'},
    'томат': {'kcal': 20, 'protein': 1, 'carbs': 4, 'fat': 0, 'unit': 'pcs'},
    'морква': {'kcal': 25, 'protein': 1, 'carbs': 6, 'fat': 0, 'unit': 'pcs'},
    'капуста': {'kcal': 25, 'protein': 1, 'carbs': 5, 'fat': 0, 'unit': '100g'},
    'брокол': {'kcal': 35, 'protein': 3, 'carbs': 6, 'fat': 0, 'unit': '100g'},
    'шпинат': {'kcal': 25, 'protein': 3, 'carbs': 4, 'fat': 0, 'unit': '100g'},
    'цибул': {'kcal': 40, 'protein': 1, 'carbs': 9, 'fat': 0, 'unit': '100g'},
    'часник': {'kcal': 150, 'protein': 6, 'carbs': 30, 'fat': 0, 'unit': '100g'},
    'гриб': {'kcal': 25, 'protein': 3, 'carbs': 4, 'fat': 0, 'unit': '100g'},
    'кукурудза': {'kcal': 90, 'protein': 3, 'carbs': 19, 'fat': 2, 'unit': '100g'},

    # Drinks
    'кава': {'kcal': 5, 'protein': 0, 'carbs': 0, 'fat': 0, 'unit': 'cup'},
    'чай': {'kcal': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'unit': 'cup'},
    'сік': {'kcal': 50, 'protein': 0, 'carbs': 12, 'fat': 0, 'unit': '100ml'},
    'компот': {'kcal': 40, 'protein': 0, 'carbs': 10, 'fat': 0, 'unit': '100ml'},
    'вода': {'kcal': 0, 'protein': 0, 'carbs': 0, 'fat': 0, 'unit': '100ml'},

    # Fats & Nuts
    'горіх': {'kcal': 600, 'protein': 15, 'carbs': 15, 'fat': 55, 'unit': '100g'},
    'насінн': {'kcal': 550, 'protein': 20, 'carbs': 15, 'fat': 45, 'unit': '100g'},
    'олія': {'kcal': 900, 'protein': 0, 'carbs': 0, 'fat': 100, 'unit': 'tbsp'},
    'маслин': {'kcal': 200, 'protein': 1, 'carbs': 6, 'fat': 19, 'unit': '100g'},

    # Meals
    'борщ': {'kcal': 100, 'protein': 4, 'carbs': 14, 'fat': 3, 'unit': '250ml'},
    'суп': {'kcal': 80, 'protein': 4, 'carbs': 10, 'fat': 3, 'unit': '250ml'},
    'бульйон': {'kcal': 30, 'protein': 2, 'carbs': 2, 'fat': 1, 'unit': '250ml'},
    'плов': {'kcal': 180, 'protein': 10, 'carbs': 22, 'fat': 6, 'unit': '100g'},
    'пельмені': {'kcal': 230, 'protein': 10, 'carbs': 24, 'fat': 11, 'unit': '100g'},
    'вареник': {'kcal': 180, 'protein': 6, 'carbs': 22, 'fat': 8, 'unit': '100g'},
    'локшин': {'kcal': 130, 'protein': 4, 'carbs': 24, 'fat': 2, 'unit': '100g'},
    'рол': {'kcal': 200, 'protein': 8, 'carbs': 26, 'fat': 7, 'unit': '100g'},
    'піца': {'kcal': 250, 'protein': 10, 'carbs': 28, 'fat': 11, 'unit': '100g'},
    'бургер': {'kcal': 300, 'protein': 15, 'carbs': 30, 'fat': 14, 'unit': 'pcs'},
    'снеки': {'kcal': 500, 'protein': 5, 'carbs': 50, 'fat': 30, 'unit': '100g'},
    'чіпси': {'kcal': 550, 'protein': 5, 'carbs': 50, 'fat': 35, 'unit': '100g'},
    'шоколад': {'kcal': 550, 'protein': 5, 'carbs': 55, 'fat': 35, 'unit': '100g'},
    'морозиво': {'kcal': 200, 'protein': 4, 'carbs': 22, 'fat': 11, 'unit': '100g'},
    'мед': {'kcal': 300, 'protein': 0, 'carbs': 75, 'fat': 0, 'unit': 'tbsp'},
    'цукор': {'kcal': 40, 'protein': 0, 'carbs': 10, 'fat': 0, 'unit': 'tsp'},
}

# Portion sizes per unit
PORTION_MULTIPLIERS = {
    'pcs': 150,      # ~150g per piece (chicken breast, bread, etc.)
    '100g': 100,     # already in 100g
    '100ml': 200,    # ~200ml for drinks
    'tbsp': 15,      # ~15g for fats
    'tsp': 5,        # ~5g for sugar
    'cup': 250,      # ~250ml for drinks
    '250ml': 250,    # soup portion
}

DEFAULT_PORTION = 100  # default 100g if unknown


def estimate_food(description: str) -> dict:
    """
    Parse food description and estimate calories + macros.
    Returns dict with kcal, protein, carbs, fat, and portion description.
    """
    text = description.lower()
    total_kcal = 0
    total_protein = 0
    total_carbs = 0
    total_fat = 0
    matched_foods = []

    for keyword, data in FOOD_DATA.items():
        if keyword in text:
            multiplier = PORTION_MULTIPLIERS.get(data['unit'], DEFAULT_PORTION)
            # Scale to actual portion
            scale = multiplier / 100.0 if data['unit'] in ('100g', '100ml') else multiplier / 100.0
            kcal = round(data['kcal'] * scale)
            protein = round(data['protein'] * scale)
            carbs = round(data['carbs'] * scale)
            fat = round(data['fat'] * scale)

            # Avoid double-counting the same food
            if keyword not in [kw for kw, _ in matched_foods]:
                total_kcal += kcal
                total_protein += protein
                total_carbs += carbs
                total_fat += fat
                matched_foods.append((keyword, data['unit']))

    if not matched_foods:
        # Default estimate for unknown food: ~150 kcal per "meal"
        return {
            'kcal': 150,
            'protein': 8,
            'carbs': 18,
            'fat': 5,
            'matched': False,
            'note': 'Приблизна оцінка',
        }

    return {
        'kcal': total_kcal,
        'protein': total_protein,
        'carbs': total_carbs,
        'fat': total_fat,
        'matched': True,
        'foods': [f[0] for f in matched_foods],
    }
