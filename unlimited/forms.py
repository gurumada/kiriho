import random
import string
from random import choice
from string import ascii_lowercase, digits

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm, UserCreationForm, PasswordChangeForm,
    PasswordResetForm, SetPasswordForm
)

from .models import Salon, Stylist, Reservation

User = get_user_model()


class EmailChangeForm(forms.ModelForm):
    """メールアドレス変更フォーム"""

    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email']
        User.objects.filter(email=email, is_active=False).delete()
        return email


class LoginForm(AuthenticationForm):
    """ログインフォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label  # placeholderにフィールドのラベルを入れる


class UserCreateForm(UserCreationForm):
    """ユーザー登録用フォーム"""

    class Meta:
        model = User
        fields = ('user_name', 'email', 'first_name', 'last_name', 'select_plan',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['username'].widget.attrs['class'] = 'form-control'
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

        # randusername = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(6)])
        # randusername = generate_random_username
        # print(randusername)
        # self.fields['randusername'].queryset = randusername

    def clean_email(self):
        email = self.cleaned_data['email']
        User.objects.filter(email=email, is_active=False).delete()
        return email


# ********* ランダムなusernameを生成するメソッド **************

# def generate_random_username(length=6, chars=ascii_lowercase + digits, split=4, delimiter='-'):
#     username = ''.join([choice(chars) for i in range(length)])
#
#     if split:
#         username = delimiter.join([username[start:start + split] for start in range(0, len(username), split)])
#         print(username)
#
#     try:
#         print(username)
#         User.objects.get(username=username)
#         return generate_random_username(length=length, chars=chars, split=split, delimiter=delimiter)
#     except User.DoesNotExist:
#         return username


# ******************************************************

class UserUpdateForm(forms.ModelForm):
    """ユーザー情報更新フォーム"""

    class Meta:
        model = User
        fields = ('last_name', 'first_name',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class MyPasswordChangeForm(PasswordChangeForm):
    """パスワード変更フォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class MyPasswordResetForm(PasswordResetForm):
    """パスワード忘れたときのフォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class MySetPasswordForm(SetPasswordForm):
    """パスワード再設定用フォーム(パスワード忘れて再設定)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class SalonUpdateForm(forms.ModelForm):
    class Meta:
        model = Salon
        exclude = ('salon', 'cut_prise', 'color_prise', 'mainte_cut_prise', 'mainte_color_prise',)


class StylistCreateForm(forms.ModelForm):
    class Meta:
        model = Stylist
        fields = ('stylist_name',)


class ReservationCreateForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = '__all__'
        exclude = ('status',)
        # todo:時間選択に何かしら方法を検討する
        widgets = {
            'date': forms.SelectDateWidget,
            'start': forms.TimeInput(format='%H:%M'),
            'end': forms.TimeInput(format='%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        self.salon = kwargs.pop('salon_pk')
        super(ReservationCreateForm, self).__init__(*args, **kwargs)
        self.fields['salon'].queryset = Salon.objects.filter(id=self.salon)
        self.fields['stylist'].queryset = Stylist.objects.filter(affiliation_salon=self.salon)
