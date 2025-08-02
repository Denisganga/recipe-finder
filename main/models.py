from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserIngredient(models.Model):
    """Model to store user's available ingredients"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    quantity = models.CharField(max_length=50, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    added_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    @property
    def is_expiring_soon(self):
        """Check if ingredient expires within 3 days"""
        if self.expiration_date:
            days_until_expiry = (self.expiration_date - timezone.now().date()).days
            return days_until_expiry <= 3
        return False


class SavedRecipe(models.Model):
    """Model to store user's saved recipes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe_id = models.CharField(max_length=200)  # Edamam recipe ID
    recipe_title = models.CharField(max_length=200)
    recipe_image = models.URLField(blank=True)
    recipe_url = models.URLField()
    saved_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['user', 'recipe_id']
    
    def __str__(self):
        return f"{self.user.username} - {self.recipe_title}"


class ShoppingListItem(models.Model):
    """Model for shopping list items"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ingredient_name = models.CharField(max_length=100)
    quantity = models.CharField(max_length=50, blank=True)
    is_purchased = models.BooleanField(default=False)
    added_date = models.DateTimeField(default=timezone.now)
    recipe_source = models.CharField(max_length=200, blank=True)  # Which recipe suggested this
    
    def __str__(self):
        return f"{self.user.username} - {self.ingredient_name}"


class UserPreference(models.Model):
    """Model to store user's dietary preferences"""
    DIET_CHOICES = [
        ('balanced', 'Balanced'),
        ('high-fiber', 'High-Fiber'),
        ('high-protein', 'High-Protein'),
        ('low-carb', 'Low-Carb'),
        ('low-fat', 'Low-Fat'),
        ('low-sodium', 'Low-Sodium'),
    ]
    
    HEALTH_CHOICES = [
        ('alcohol-cocktail', 'Alcohol-Cocktail'),
        ('alcohol-free', 'Alcohol-Free'),
        ('celery-free', 'Celery-Free'),
        ('crustacean-free', 'Crustacean-Free'),
        ('dairy-free', 'Dairy-Free'),
        ('DASH', 'DASH'),
        ('egg-free', 'Egg-Free'),
        ('fish-free', 'Fish-Free'),
        ('fodmap-free', 'FODMAP-Free'),
        ('gluten-free', 'Gluten-Free'),
        ('immuno-supportive', 'Immuno-Supportive'),
        ('keto-friendly', 'Keto-Friendly'),
        ('kidney-friendly', 'Kidney-Friendly'),
        ('kosher', 'Kosher'),
        ('low-potassium', 'Low-Potassium'),
        ('low-sugar', 'Low-Sugar'),
        ('lupine-free', 'Lupine-Free'),
        ('Mediterranean', 'Mediterranean'),
        ('mollusk-free', 'Mollusk-Free'),
        ('mustard-free', 'Mustard-Free'),
        ('no-oil-added', 'No-Oil-Added'),
        ('paleo', 'Paleo'),
        ('peanut-free', 'Peanut-Free'),
        ('pescatarian', 'Pescatarian'),
        ('pork-free', 'Pork-Free'),
        ('red-meat-free', 'Red-Meat-Free'),
        ('sesame-free', 'Sesame-Free'),
        ('shellfish-free', 'Shellfish-Free'),
        ('soy-free', 'Soy-Free'),
        ('sugar-conscious', 'Sugar-Conscious'),
        ('sulfite-free', 'Sulfite-Free'),
        ('tree-nut-free', 'Tree-Nut-Free'),
        ('vegan', 'Vegan'),
        ('vegetarian', 'Vegetarian'),
        ('wheat-free', 'Wheat-Free'),
    ]
    
    CUISINE_CHOICES = [
        ('american', 'American'),
        ('asian', 'Asian'),
        ('british', 'British'),
        ('caribbean', 'Caribbean'),
        ('central-europe', 'Central Europe'),
        ('chinese', 'Chinese'),
        ('eastern-europe', 'Eastern Europe'),
        ('french', 'French'),
        ('indian', 'Indian'),
        ('italian', 'Italian'),
        ('japanese', 'Japanese'),
        ('kosher', 'Kosher'),
        ('mediterranean', 'Mediterranean'),
        ('mexican', 'Mexican'),
        ('middle-eastern', 'Middle Eastern'),
        ('nordic', 'Nordic'),
        ('south-american', 'South American'),
        ('south-east-asian', 'South East Asian'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    diet_type = models.CharField(max_length=20, choices=DIET_CHOICES, blank=True)
    health_labels = models.JSONField(default=list, blank=True)  # Multiple health preferences
    cuisine_types = models.JSONField(default=list, blank=True)  # Multiple cuisine preferences
    max_prep_time = models.IntegerField(null=True, blank=True)  # in minutes
    
    def __str__(self):
        return f"{self.user.username} preferences"
