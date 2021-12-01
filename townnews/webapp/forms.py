from django import forms

class LoginForm(forms.Form):
    login = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Логин'}))
    password = password = forms.CharField(max_length=32, widget=forms.PasswordInput(attrs={'placeholder': 'Пароль'}))

class NewsForm(forms.Form):
    title = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Заголовок'}))
    tags = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Тег новости'}))
    image = forms.ImageField()
    text = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Текст записи'}))

class PromoForm(forms.Form):
    title = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Заголовок'}))
    code = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Промокод'}))
    image = forms.ImageField()
