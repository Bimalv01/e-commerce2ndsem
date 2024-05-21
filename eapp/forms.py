from django import forms
from .models import Address, Seller

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['recepient_name', 'recepient_contact', 'address_line1', 'address_line2', 'city', 'state', 'postal_code']
        widgets = {
            'recepient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Recipient Name'}),
            'recepient_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Recipient Contact'}),
            'address_line1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 1'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address Line 2'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'}),
        }

# class PurchaseOrderForm(forms.Form):
#     seller = forms.ModelChoiceField(queryset=Seller.objects.all(), empty_label="Select Seller")

# class PurchaseForm(forms.Form):
#     quantity = forms.IntegerField(min_value=1, label='Quantity')

# class SellerLoginForm(forms.Form):
#     email = forms.EmailField(label='Email')
#     password = forms.CharField(label='Password', widget=forms.PasswordInput)