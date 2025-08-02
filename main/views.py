from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

from .models import UserIngredient, UserPreference, SavedRecipe, ShoppingListItem
from .forms import IngredientForm, BulkIngredientForm, UserPreferenceForm, RecipeSearchForm, ShoppingListForm
from .services import RecipeRecommendationService, GeminiService, EdamamService


def home(request):
    """Landing page view"""
    return render(request, 'main/home.html')


def signup_view(request):
    """User registration view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Basic validation
        errors = {}
        
        if not username:
            errors['username'] = ['Username is required']
        elif User.objects.filter(username=username).exists():
            errors['username'] = ['Username already exists']
            
        if not email:
            errors['email'] = ['Email is required']
        elif User.objects.filter(email=email).exists():
            errors['email'] = ['Email already exists']
            
        if not password1:
            errors['password1'] = ['Password is required']
        elif len(password1) < 8:
            errors['password1'] = ['Password must be at least 8 characters long']
            
        if password1 != password2:
            errors['password2'] = ['Passwords do not match']
        
        if not errors:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create default user preferences
            UserPreference.objects.create(user=user)
            
            # Log the user in
            login(request, user)
            messages.success(request, f'Welcome to Recipe Finder, {user.first_name or user.username}!')
            return redirect('dashboard')
        else:
            # Return form with errors
            return render(request, 'main/signup.html', {'form': {'errors': errors}})
    
    return render(request, 'main/signup.html')


def login_view(request):
    """User login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('dashboard')
        else:
            errors = {'__all__': ['Invalid username or password']}
            return render(request, 'main/login.html', {'form': {'errors': errors}})
    
    return render(request, 'main/login.html')


@login_required
def dashboard(request):
    """User dashboard view - requires authentication"""
    # Get user statistics
    user_ingredients = UserIngredient.objects.filter(user=request.user)
    saved_recipes = SavedRecipe.objects.filter(user=request.user)
    shopping_items = ShoppingListItem.objects.filter(user=request.user, is_purchased=False)
    expiring_ingredients = user_ingredients.filter(expiration_date__isnull=False)
    expiring_soon = [ing for ing in expiring_ingredients if ing.is_expiring_soon]
    
    # Get recipe recommendations if user has ingredients
    recommendations = None
    if user_ingredients.exists():
        try:
            preferences = UserPreference.objects.get(user=request.user)
        except UserPreference.DoesNotExist:
            preferences = UserPreference.objects.create(user=request.user)
        
        recommendation_service = RecipeRecommendationService()
        recommendations = recommendation_service.get_personalized_recommendations(
            user_ingredients, preferences
        )
    
    context = {
        'user_ingredients_count': user_ingredients.count(),
        'saved_recipes_count': saved_recipes.count(),
        'shopping_items_count': shopping_items.count(),
        'expiring_soon_count': len(expiring_soon),
        'expiring_ingredients': expiring_soon,
        'recommendations': recommendations,
        'recent_ingredients': user_ingredients.order_by('-added_date')[:5],
        'recent_recipes': saved_recipes.order_by('-saved_date')[:5],
    }
    
    return render(request, 'main/dashboard.html', context)


@login_required
def ingredients_view(request):
    """Manage user ingredients"""
    user_ingredients = UserIngredient.objects.filter(user=request.user).order_by('-added_date')
    
    if request.method == 'POST':
        if 'bulk_add' in request.POST:
            bulk_form = BulkIngredientForm(request.POST)
            if bulk_form.is_valid():
                # Use Gemini AI to parse ingredients
                gemini_service = GeminiService()
                ingredients_text = bulk_form.cleaned_data['ingredients_text']
                parsed_ingredients = gemini_service.parse_ingredients(ingredients_text)
                
                added_count = 0
                for ingredient_data in parsed_ingredients:
                    ingredient, created = UserIngredient.objects.get_or_create(
                        user=request.user,
                        name=ingredient_data['name'].lower().strip(),
                        defaults={'quantity': ingredient_data.get('quantity', '')}
                    )
                    if created:
                        added_count += 1
                
                messages.success(request, f'Added {added_count} ingredients successfully!')
                return redirect('ingredients')
        else:
            form = IngredientForm(request.POST)
            if form.is_valid():
                ingredient = form.save(commit=False)
                ingredient.user = request.user
                ingredient.name = ingredient.name.lower().strip()
                try:
                    ingredient.save()
                    messages.success(request, f'Added {ingredient.name} to your ingredients!')
                except:
                    messages.error(request, f'{ingredient.name} is already in your ingredients!')
                return redirect('ingredients')
    
    form = IngredientForm()
    bulk_form = BulkIngredientForm()
    
    context = {
        'ingredients': user_ingredients,
        'form': form,
        'bulk_form': bulk_form,
    }
    
    return render(request, 'main/ingredients.html', context)


@login_required
def delete_ingredient(request, ingredient_id):
    """Delete an ingredient"""
    ingredient = get_object_or_404(UserIngredient, id=ingredient_id, user=request.user)
    ingredient_name = ingredient.name
    ingredient.delete()
    messages.success(request, f'Removed {ingredient_name} from your ingredients.')
    return redirect('ingredients')


@login_required
def preferences_view(request):
    """Manage user preferences"""
    try:
        preferences = UserPreference.objects.get(user=request.user)
    except UserPreference.DoesNotExist:
        preferences = UserPreference.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your preferences have been updated!')
            return redirect('preferences')
    else:
        form = UserPreferenceForm(instance=preferences)
    
    return render(request, 'main/preferences.html', {'form': form})


@login_required
def recipe_search(request):
    """Search for recipes"""
    form = RecipeSearchForm(request.GET or None)
    recipes = []
    ai_suggestions = []
    
    if form.is_valid():
        query = form.cleaned_data.get('query', '')
        use_my_ingredients = form.cleaned_data.get('use_my_ingredients', False)
        diet_filter = form.cleaned_data.get('diet_filter')
        cuisine_filter = form.cleaned_data.get('cuisine_filter')
        max_time = form.cleaned_data.get('max_time')
        health_condition = form.cleaned_data.get('health_condition')
        sodium_level = form.cleaned_data.get('sodium_level')
        sugar_level = form.cleaned_data.get('sugar_level')
        
        # Map health conditions to EDAMAM health labels
        health_labels = []
        if health_condition:
            health_mapping = {
                'diabetes': ['low-sugar', 'sugar-conscious'],
                'heart-disease': ['low-sodium'],
                'kidney-disease': ['kidney-friendly', 'low-potassium'],
                'high-blood-pressure': ['DASH', 'low-sodium'],
                'celiac': ['gluten-free'],
                'lactose-intolerance': ['dairy-free'],
                'immune-support': ['immuno-supportive'],
            }
            health_labels.extend(health_mapping.get(health_condition, []))
        
        # Add sodium level to health labels
        if sodium_level:
            if sodium_level == 'low-sodium':
                health_labels.append('low-sodium')
            elif sodium_level == 'no-salt':
                health_labels.append('no-oil-added')  # Closest match in EDAMAM
        
        # Add sugar level to health labels
        if sugar_level:
            if sugar_level == 'low-sugar':
                health_labels.append('low-sugar')
            elif sugar_level == 'sugar-conscious':
                health_labels.append('sugar-conscious')
            elif sugar_level == 'no-sugar':
                health_labels.append('sugar-conscious')  # Closest match
        
        # Use the first health label for API call (EDAMAM limitation)
        primary_health_label = health_labels[0] if health_labels else None
        
        edamam_service = EdamamService()
        
        if use_my_ingredients:
            # Use user's ingredients for search
            user_ingredients = UserIngredient.objects.filter(user=request.user)
            if user_ingredients.exists():
                ingredient_names = [ing.name for ing in user_ingredients]
                search_query = ' '.join(ingredient_names)
                if query:
                    search_query += f' {query}'
                
                # Get AI suggestions
                try:
                    preferences = UserPreference.objects.get(user=request.user)
                except UserPreference.DoesNotExist:
                    preferences = None
                
                gemini_service = GeminiService()
                ai_suggestions = gemini_service.suggest_recipes_from_ingredients(
                    ingredient_names, preferences
                )
            else:
                search_query = query
        else:
            search_query = query
        
        if search_query:
            # Search using Edamam API with all filters
            results = edamam_service.search_recipes(
                search_query, diet_filter, primary_health_label, cuisine_filter, max_time
            )
            
            # Format results
            recommendation_service = RecipeRecommendationService()
            recipes = recommendation_service.format_edamam_results(results)
    
    context = {
        'form': form,
        'recipes': recipes,
        'ai_suggestions': ai_suggestions,
    }
    
    return render(request, 'main/recipe_search.html', context)


@login_required
def save_recipe(request):
    """Save a recipe to user's collection"""
    if request.method == 'POST':
        recipe_id = request.POST.get('recipe_id')
        recipe_title = request.POST.get('recipe_title')
        recipe_image = request.POST.get('recipe_image', '')
        recipe_url = request.POST.get('recipe_url')
        
        saved_recipe, created = SavedRecipe.objects.get_or_create(
            user=request.user,
            recipe_id=recipe_id,
            defaults={
                'recipe_title': recipe_title,
                'recipe_image': recipe_image,
                'recipe_url': recipe_url,
            }
        )
        
        if created:
            messages.success(request, f'Saved "{recipe_title}" to your collection!')
        else:
            messages.info(request, f'"{recipe_title}" is already in your collection.')
    
    return redirect('recipe_search')


@login_required
def saved_recipes(request):
    """View saved recipes"""
    recipes = SavedRecipe.objects.filter(user=request.user).order_by('-saved_date')
    return render(request, 'main/saved_recipes.html', {'recipes': recipes})


@login_required
def shopping_list(request):
    """Manage shopping list"""
    items = ShoppingListItem.objects.filter(user=request.user).order_by('-added_date')
    
    if request.method == 'POST':
        form = ShoppingListForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, f'Added {item.ingredient_name} to your shopping list!')
            return redirect('shopping_list')
    else:
        form = ShoppingListForm()
    
    context = {
        'items': items,
        'form': form,
        'pending_items': items.filter(is_purchased=False),
        'purchased_items': items.filter(is_purchased=True),
    }
    
    return render(request, 'main/shopping_list.html', context)


@login_required
def toggle_shopping_item(request, item_id):
    """Toggle shopping list item as purchased/unpurchased"""
    item = get_object_or_404(ShoppingListItem, id=item_id, user=request.user)
    item.is_purchased = not item.is_purchased
    item.save()
    
    status = "purchased" if item.is_purchased else "pending"
    messages.success(request, f'Marked {item.ingredient_name} as {status}.')
    return redirect('shopping_list')


@login_required
def delete_shopping_item(request, item_id):
    """Delete shopping list item"""
    item = get_object_or_404(ShoppingListItem, id=item_id, user=request.user)
    item_name = item.ingredient_name
    item.delete()
    messages.success(request, f'Removed {item_name} from your shopping list.')
    return redirect('shopping_list')


@login_required
@require_http_methods(["POST"])
def generate_shopping_list_from_recipe(request):
    """Generate shopping list items from a recipe"""
    recipe_ingredients = request.POST.getlist('ingredients')
    recipe_name = request.POST.get('recipe_name', 'Selected Recipe')
    
    user_ingredients = UserIngredient.objects.filter(user=request.user)
    recommendation_service = RecipeRecommendationService()
    
    needed_ingredients = recommendation_service.generate_shopping_list(
        recipe_ingredients, user_ingredients
    )
    
    added_count = 0
    for ingredient in needed_ingredients:
        item, created = ShoppingListItem.objects.get_or_create(
            user=request.user,
            ingredient_name=ingredient,
            defaults={'recipe_source': recipe_name}
        )
        if created:
            added_count += 1
    
    messages.success(request, f'Added {added_count} items to your shopping list from {recipe_name}!')
    return redirect('shopping_list')
