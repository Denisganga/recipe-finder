import requests
import google.generativeai as genai
from django.conf import settings
import json
import re


class GeminiService:
    """Service for interacting with Google Gemini API"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    def parse_ingredients(self, ingredient_text):
        """
        Parse natural language ingredient input using Gemini AI
        Returns structured ingredient data
        """
        prompt = f"""
        Parse the following ingredient text and extract individual ingredients with their quantities.
        Return the result as a JSON array where each item has 'name' and 'quantity' fields.
        If no quantity is specified, use an empty string for quantity.
        
        Ingredient text: "{ingredient_text}"
        
        Example format:
        [
            {{"name": "tomatoes", "quantity": "2 large"}},
            {{"name": "onion", "quantity": "1 medium"}},
            {{"name": "garlic", "quantity": ""}}
        ]
        
        Only return the JSON array, no other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            print(f"Gemini API error: {e}")
            return []
    
    def suggest_recipes_from_ingredients(self, ingredients, preferences=None):
        """
        Get recipe suggestions based on available ingredients using Gemini AI
        """
        ingredients_str = ", ".join(ingredients)
        
        preference_text = ""
        if preferences:
            if preferences.diet_type:
                preference_text += f"Diet: {preferences.diet_type}. "
            if preferences.health_labels:
                preference_text += f"Health requirements: {', '.join(preferences.health_labels)}. "
            if preferences.cuisine_types:
                preference_text += f"Preferred cuisines: {', '.join(preferences.cuisine_types)}. "
        
        prompt = f"""
        Based on these available ingredients: {ingredients_str}
        {preference_text}
        
        Suggest 5 recipe ideas that can be made primarily with these ingredients.
        For each recipe, provide:
        1. Recipe name
        2. Brief description
        3. Main ingredients from the available list that would be used
        4. Additional ingredients that might be needed
        5. Estimated cooking time
        6. Difficulty level (Easy/Medium/Hard)
        
        Format as JSON array:
        [
            {{
                "name": "Recipe Name",
                "description": "Brief description",
                "available_ingredients": ["ingredient1", "ingredient2"],
                "additional_ingredients": ["ingredient3", "ingredient4"],
                "cooking_time": "30 minutes",
                "difficulty": "Easy"
            }}
        ]
        
        Only return the JSON array, no other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            print(f"Gemini API error: {e}")
            return []
    
    def analyze_ingredient_expiry(self, ingredients_with_dates):
        """
        Analyze ingredients and suggest recipes to use expiring items first
        """
        expiring_ingredients = [
            f"{ing['name']} (expires {ing['expiration_date']})" 
            for ing in ingredients_with_dates 
            if ing.get('is_expiring_soon')
        ]
        
        if not expiring_ingredients:
            return []
        
        prompt = f"""
        These ingredients are expiring soon: {', '.join(expiring_ingredients)}
        
        Suggest 3 quick and easy recipes that would use these expiring ingredients to minimize food waste.
        Focus on recipes that can be made quickly and use multiple expiring ingredients.
        
        Format as JSON array:
        [
            {{
                "name": "Recipe Name",
                "description": "Brief description",
                "expiring_ingredients_used": ["ingredient1", "ingredient2"],
                "cooking_time": "20 minutes",
                "urgency": "High"
            }}
        ]
        
        Only return the JSON array, no other text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return []
        except Exception as e:
            print(f"Gemini API error: {e}")
            return []


class EdamamService:
    """Service for interacting with Edamam Recipe API"""
    
    def __init__(self):
        self.app_id = settings.EDAMAM_APP_ID
        self.app_key = settings.EDAMAM_APP_KEY
        self.base_url = "https://api.edamam.com/api/recipes/v2"
    
    def search_recipes(self, query, diet=None, health=None, cuisine=None, time=None, limit=20):
        """
        Search for recipes using Edamam API
        """
        params = {
            'type': 'public',
            'q': query,
            'app_id': self.app_id,
            'app_key': self.app_key,
            'from': 0,
            'to': limit,
        }
        
        # Add filters
        if diet:
            params['diet'] = diet
        if health:
            params['health'] = health
        if cuisine:
            params['cuisineType'] = cuisine
        if time:
            params['time'] = f"1-{time}"
        
        # Required headers for EDAMAM API v2
        headers = {
            'Edamam-Account-User': self.app_id,
            'Accept': 'application/json',
            'User-Agent': 'RecipeFinder/1.0'
        }
        
        try:
            response = requests.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Edamam API error: {e}")
            return {'hits': []}
    
    def search_by_ingredients(self, ingredients, preferences=None, limit=20):
        """
        Search recipes by ingredients
        """
        # Create query from ingredients
        query = " ".join(ingredients)
        
        diet = None
        health = None
        cuisine = None
        time = None
        
        if preferences:
            diet = preferences.diet_type if preferences.diet_type else None
            health = preferences.health_labels[0] if preferences.health_labels else None
            cuisine = preferences.cuisine_types[0] if preferences.cuisine_types else None
            time = preferences.max_prep_time if preferences.max_prep_time else None
        
        return self.search_recipes(query, diet, health, cuisine, time, limit)
    
    def get_recipe_details(self, recipe_id):
        """
        Get detailed recipe information by ID
        """
        url = f"{self.base_url}/{recipe_id}"
        params = {
            'type': 'public',
            'app_id': self.app_id,
            'app_key': self.app_key,
        }
        
        # Required headers for EDAMAM API v2
        headers = {
            'Edamam-Account-User': self.app_id,
            'Accept': 'application/json',
            'User-Agent': 'RecipeFinder/1.0'
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Edamam API error: {e}")
            return None


class RecipeRecommendationService:
    """
    Main service that combines Gemini AI and Edamam API for intelligent recipe recommendations
    """
    
    def __init__(self):
        self.gemini = GeminiService()
        self.edamam = EdamamService()
    
    def get_personalized_recommendations(self, user_ingredients, preferences=None):
        """
        Get personalized recipe recommendations combining AI analysis and real recipes
        """
        # Get ingredient names
        ingredient_names = [ing.name for ing in user_ingredients]
        
        # Get AI suggestions first
        ai_suggestions = self.gemini.suggest_recipes_from_ingredients(ingredient_names, preferences)
        
        # Get real recipes from Edamam
        edamam_results = self.edamam.search_by_ingredients(ingredient_names, preferences)
        
        # Combine and format results
        recommendations = {
            'ai_suggestions': ai_suggestions,
            'real_recipes': self.format_edamam_results(edamam_results),
            'expiring_soon': self.get_expiring_ingredient_recipes(user_ingredients)
        }
        
        return recommendations
    
    def format_edamam_results(self, edamam_response):
        """
        Format Edamam API response for frontend consumption
        """
        recipes = []
        for hit in edamam_response.get('hits', []):
            recipe = hit['recipe']
            recipes.append({
                'id': recipe['uri'].split('#recipe_')[1] if '#recipe_' in recipe['uri'] else recipe['uri'],
                'title': recipe['label'],
                'image': recipe.get('image', ''),
                'url': recipe['url'],
                'source': recipe['source'],
                'ingredients': recipe['ingredientLines'],
                'calories': round(recipe.get('calories', 0)),
                'time': recipe.get('totalTime', 0),
                'servings': recipe.get('yield', 0),
                'diet_labels': recipe.get('dietLabels', []),
                'health_labels': recipe.get('healthLabels', []),
                'cuisine_type': recipe.get('cuisineType', []),
            })
        return recipes
    
    def get_expiring_ingredient_recipes(self, user_ingredients):
        """
        Get recipes specifically for expiring ingredients
        """
        expiring_ingredients = []
        for ing in user_ingredients:
            if ing.is_expiring_soon:
                expiring_ingredients.append({
                    'name': ing.name,
                    'expiration_date': ing.expiration_date.strftime('%Y-%m-%d') if ing.expiration_date else None,
                    'is_expiring_soon': ing.is_expiring_soon
                })
        
        if expiring_ingredients:
            return self.gemini.analyze_ingredient_expiry(expiring_ingredients)
        return []
    
    def generate_shopping_list(self, recipe_ingredients, user_ingredients):
        """
        Generate shopping list by comparing recipe requirements with available ingredients
        """
        available_ingredients = [ing.name.lower() for ing in user_ingredients]
        shopping_list = []
        
        for ingredient in recipe_ingredients:
            # Simple matching - could be improved with fuzzy matching
            ingredient_name = ingredient.lower()
            if not any(avail in ingredient_name or ingredient_name in avail for avail in available_ingredients):
                shopping_list.append(ingredient)
        
        return shopping_list
