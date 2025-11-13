from django import forms


class RegisterForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class CheckContactForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    phone_number = forms.CharField()


class CheckShipping(forms.Form):
    Address = forms.CharField()
    apartment = forms.CharField()
    city = forms.CharField()
    state = forms.CharField()
    zipcode = forms.CharField()
    country = forms.CharField()




