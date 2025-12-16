# shop/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(required=True, label='Имя')
    last_name = forms.CharField(required=True, label='Фамилия')
    phone = forms.CharField(required=False, label='Телефон')
    address = forms.CharField(widget=forms.Textarea, required=False, label='Адрес')

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'address', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        user.address = self.cleaned_data['address']
        user.role = 'Покупатель'

        if commit:
            user.save()
        return user


class OrderForm(forms.ModelForm):
    billing_address = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label='Адрес для счета (если отличается от адреса доставки)'
    )

    class Meta:
        model = Order
        fields = ('shipping_address', 'billing_address')
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'shipping_address': 'Адрес доставки',
        }


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('rating', 'comment')
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'rating': 'Оценка',
            'comment': 'Отзыв',
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ('created_at', 'updated_at')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }