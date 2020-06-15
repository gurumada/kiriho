import random
import string
import datetime
from random import choice
from string import ascii_lowercase, digits

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm, UserCreationForm, PasswordChangeForm,
    PasswordResetForm, SetPasswordForm
)
from django.utils import timezone

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


# class ReservationDateTimeForm(forms.ModelForm):
#     class Meta:
#         model = Reservation
#         fields = ('date', 'start', 'end')
#         widgets = {
#             'date': forms.SelectDateWidget,
#             'start': forms.TimeInput(format='%H:%M'),
#             'end': forms.TimeInput(format='%H:%M'),
#         }


class ReservationCreateForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = '__all__'
        exclude = ('status',)
        widgets = {
            'member': forms.TextInput(attrs={'readonly': 'readonly'}),
            'plan': forms.Select(attrs={'readonly': 'readonly'}),
            'date': forms.TextInput(attrs={'readonly': 'readonly'}),
            'start': forms.TextInput(attrs={'readonly': 'readonly'}),
            'end': forms.TextInput(attrs={'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        self.salon = kwargs.pop('salon_pk')
        self.member = kwargs.pop('user_name')

        reserve_date = kwargs.pop('reserve_date')
        reserve = datetime.datetime.strptime(reserve_date, '%Y-%m-%d')
        date = datetime.datetime.date(reserve)
        self.date = date

        self.start = kwargs.pop('start')
        self.end = kwargs.pop('end')
        super(ReservationCreateForm, self).__init__(*args, **kwargs)

        self.fields['member'].initial = self.member
        self.fields['member'].required = True
        # ログインサロンの初期値を設定
        salon = Salon.objects.get(id=self.salon)
        self.fields['salon'].choices = ((salon.pk, salon.salon_name),)
        self.fields['stylist'].queryset = Stylist.objects.filter(affiliation_salon=self.salon)

        # ユーザー選択プランの初期値設定
        plan = User.objects.filter(user_name=self.member).values('select_plan')
        if plan[0]['select_plan'] == 0:
            select_plan = (('0', 'カットし放題'),)
        elif plan[0]['select_plan'] == 1:
            select_plan = (('1', 'カラーし放題'),)
        elif plan[0]['select_plan'] == 2:
            select_plan = (('2', 'カット＆カラーし放題'),)
        else:
            select_plan = (('9', '利用不可'),)

        self.fields['plan'].choices = select_plan
        self.fields['date'].initial = self.date
        self.fields['start'].initial = self.start
        self.fields['end'].initial = self.end

        # ユーザーの利用可能施術を設定
        full_cut = (('0', 'フルカット'),)
        full_color = (('1', 'フルカラー'),)
        mainte_cut = (('2', 'メンテカット'),)
        mainte_color = (('3', 'メンテカラー'),)
        unusable = (('9', '利用不可'),)

        # 最新の予約情報取得
        try:
            treatment_info = Reservation.objects.filter(member=self.member).order_by('-date')
            self.fields['treatment'].choices = recursive_choice_setting(treatment_info, 0, date)

        # 予約した記録がなかったら
        except IndexError:
            self.fields['treatment'].choices = full_cut

    def clean_treatment(self):
        treatment = self.cleaned_data['treatment']
        if treatment == 9:
            raise forms.ValidationError('利用できません')
        return treatment


########################################
# 施術可能選択肢を再起処理で実現(カットのみ) #
########################################
def recursive_choice_setting(obj_treatment_info, int_list_no, date_reserve_date):
    # ユーザーの利用可能施術を設定
    full_cut = (('0', 'フルカット'),)
    full_color = (('1', 'フルカラー'),)
    mainte_cut = (('2', 'メンテカット'),)
    mainte_color = (('3', 'メンテカラー'),)
    unusable = (('9', '利用不可'),)

    # 最新の予約が「予約済み」状態だった場合
    if obj_treatment_info.values('status')[int_list_no]['status'] == 0:
        return unusable
    # 最新の予約が「済」だった場合
    elif obj_treatment_info.values('status')[int_list_no]['status'] == 1:
        reserved_date = obj_treatment_info.values('date')[int_list_no]['date']
        # now = datetime.datetime.now()
        # interval_date = now.date() - reserved_date
        interval_date = date_reserve_date - reserved_date

        # 当日に2回行こうとした場合、利用不可
        if interval_date == datetime.timedelta(days=0):
            return unusable

        # 最新の予約から30日経過していたらフルカット
        elif interval_date > datetime.timedelta(days=30):
            return full_cut

        # 最新の予約から30日経過していなかったらメンテカット
        elif interval_date <= datetime.timedelta(days=30):
            return mainte_cut

    # 最新の予約が「キャンセル」だった場合
    elif obj_treatment_info.values('status')[int_list_no]['status'] == 2:
        return recursive_choice_setting(obj_treatment_info, int_list_no + 1, date_reserve_date)

    # 最新の予約が「ドタキャン」だった場合
    elif obj_treatment_info.values('status')[int_list_no]['status'] == 3:
        reserved_date = obj_treatment_info.values('date')[int_list_no]['date']
        # now = datetime.datetime.now()
        # interval_date = now.date() - reserved_date
        interval_date = date_reserve_date - reserved_date

        # ドタキャンから20日経過していた場合
        if interval_date > datetime.timedelta(days=20):
            try:
                reserved_date = obj_treatment_info.values('date')[int_list_no + 1]['date']
                # now = datetime.datetime.now()
                # interval_date = now.date() - reserved_date
                interval_date = date_reserve_date - reserved_date

                # ドタキャンより前の予約から30日経過していた場合
                if interval_date > datetime.timedelta(days=30):
                    return full_cut

                # ドタキャンより前の予約から30日経過していなかった場合
                elif interval_date <= datetime.timedelta(days=30):
                    return mainte_cut

            # ドタキャンより前の予約がなかったら
            except IndexError:
                return full_cut

        # ドタキャンから20日経過していなかったら利用不可
        elif interval_date <= datetime.timedelta(days=20):
            return unusable
