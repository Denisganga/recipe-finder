from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Ingredients management
    path('ingredients/', views.ingredients_view, name='ingredients'),
    path('ingredients/delete/<int:ingredient_id>/', views.delete_ingredient, name='delete_ingredient'),
    
    # User preferences
    path('preferences/', views.preferences_view, name='preferences'),
    
    # Recipe search and management
    path('search/', views.recipe_search, name='recipe_search'),
    path('save-recipe/', views.save_recipe, name='save_recipe'),
    path('saved-recipes/', views.saved_recipes, name='saved_recipes'),
    
    # Shopping list
    path('shopping-list/', views.shopping_list, name='shopping_list'),
    path('shopping-list/toggle/<int:item_id>/', views.toggle_shopping_item, name='toggle_shopping_item'),
    path('shopping-list/delete/<int:item_id>/', views.delete_shopping_item, name='delete_shopping_item'),
    path('shopping-list/generate/', views.generate_shopping_list_from_recipe, name='generate_shopping_list'),
]
