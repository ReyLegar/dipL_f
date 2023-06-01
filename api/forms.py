from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=20)
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    patronymic = forms.CharField(max_length=50)
    balance = forms.DecimalField(max_digits=10, decimal_places=2)
    document_image = forms.ImageField()
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'first_name', 'last_name', 'patronymic', 'balance', 'document_image', 'password1', 'password2')

class CreditConfirmationForm(forms.Form):
    document = forms.ImageField(label='Загрузите документ', required=True)
    term = forms.IntegerField(label='Срок кредита')
    interest_rate = forms.DecimalField(label='Процентная ставка')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document'].widget.attrs.update({'accept': 'image/jpg, image/jpeg, image/png, image/gif'})

    def clean_interest_rate(self):
        interest_rate = self.cleaned_data.get('interest_rate', False)
        if interest_rate:
            if interest_rate > 100 or interest_rate < 0:
                raise forms.ValidationError("Процентная ставка должна быть от 0 до 100")
        else:
            raise forms.ValidationError("Необходимо указать процентную ставку")
        return interest_rate

    def clean_term(self):
        term = self.cleaned_data.get('term', False)
        if term:
            if term > 360 or term < 1:
                raise forms.ValidationError("Срок кредита должен быть от 1 до 360 месяцев")
        else:
            raise forms.ValidationError("Необходимо указать срок кредита")
        return term

