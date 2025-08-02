from django import forms
from .models import UserIngredient, UserPreference, ShoppingListItem


class IngredientForm(forms.ModelForm):
    class Meta:
        model = UserIngredient
        fields = ['name', 'quantity', 'expiration_date']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., tomatoes, chicken breast, rice'
            }),
            'quantity': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2 large, 1 lb, 1 cup'
            }),
            'expiration_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }


class BulkIngredientForm(forms.Form):
    ingredients_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter your ingredients in natural language, e.g.:\n"I have 2 large tomatoes, 1 onion, some garlic, chicken breast, and rice"'
        }),
        label='Describe your available ingredients',
        help_text='Use natural language - our AI will parse and organize your ingredients automatically.'
    )


class UserPreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = ['diet_type', 'health_labels', 'cuisine_types', 'max_prep_time']
        widgets = {
            'diet_type': forms.Select(attrs={'class': 'form-select'}),
            'health_labels': forms.CheckboxSelectMultiple(),
            'cuisine_types': forms.CheckboxSelectMultiple(),
            'max_prep_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 45',
                'min': '1',
                'max': '300'
            })
        }
        labels = {
            'max_prep_time': 'Maximum preparation time (minutes)',
        }
        help_texts = {
            'max_prep_time': 'Maximum preparation time in minutes',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize health labels display
        self.fields['health_labels'].choices = [
            (choice[0], choice[1]) for choice in UserPreference.HEALTH_CHOICES
        ]
        self.fields['cuisine_types'].choices = [
            (choice[0], choice[1]) for choice in UserPreference.CUISINE_CHOICES
        ]


class RecipeSearchForm(forms.Form):
    # Health condition choices for underlying health conditions
    HEALTH_CONDITION_CHOICES = [
        ('', 'No specific health condition'),
        ('diabetes', 'Diabetes (Low-Sugar)'),
        ('heart-disease', 'Heart Disease (Low-Sodium)'),
        ('kidney-disease', 'Kidney Disease (Low-Potassium)'),
        ('high-blood-pressure', 'High Blood Pressure (DASH)'),
        ('celiac', 'Celiac Disease (Gluten-Free)'),
        ('lactose-intolerance', 'Lactose Intolerance (Dairy-Free)'),
        ('immune-support', 'Immune Support'),
    ]
    
    # Sodium/Sugar level choices
    SODIUM_LEVEL_CHOICES = [
        ('', 'Any sodium level'),
        ('low-sodium', 'Low Sodium'),
        ('no-salt', 'No Added Salt'),
    ]
    
    SUGAR_LEVEL_CHOICES = [
        ('', 'Any sugar level'),
        ('low-sugar', 'Low Sugar'),
        ('sugar-conscious', 'Sugar Conscious'),
        ('no-sugar', 'No Added Sugar'),
    ]
    
    query = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search for recipes...'
        }),
        required=False
    )
    
    use_my_ingredients = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Use my available ingredients'
    )
    
    diet_filter = forms.ChoiceField(
        choices=[('', 'Any Diet')] + UserPreference.DIET_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Diet Type'
    )
    
    cuisine_filter = forms.ChoiceField(
        choices=[('', 'Any Cuisine')] + UserPreference.CUISINE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Cuisine Type'
    )
    
    max_time = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 30',
            'min': '1',
            'max': '300'
        }),
        label='Max cooking time (minutes)',
        help_text='Maximum cooking time in minutes'
    )
    
    health_condition = forms.ChoiceField(
        choices=HEALTH_CONDITION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Health Condition',
        help_text='Filter recipes suitable for specific health conditions'
    )
    
    sodium_level = forms.ChoiceField(
        choices=SODIUM_LEVEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Sodium Level',
        help_text='Control sodium content in recipes'
    )
    
    sugar_level = forms.ChoiceField(
        choices=SUGAR_LEVEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Sugar Level',
        help_text='Control sugar content in recipes'
    )


class ShoppingListForm(forms.ModelForm):
    class Meta:
        model = ShoppingListItem
        fields = ['ingredient_name', 'quantity']
        widgets = {
            'ingredient_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingredient name'
            }),
            'quantity': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Quantity needed'
            })
        }
