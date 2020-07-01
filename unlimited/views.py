import datetime

from .models import Salon, Stylist, Reservation
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView)
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, resolve_url, render, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import generic
from .forms import (
    LoginForm, UserCreateForm, UserUpdateForm, MyPasswordChangeForm,
    MyPasswordResetForm, MySetPasswordForm, EmailChangeForm,
    StylistCreateForm, ReservationCreateForm, SalonUpdateForm, )
from django.utils import timezone
from dateutil.relativedelta import relativedelta

User = get_user_model()


def distribution(request):
    user = request.user
    print(user)
    if user.is_user:
        return redirect('unlimited:salon_list')
    else:
        return redirect('unlimited:stylist_list')


class Landing(generic.TemplateView):
    template_name = 'unlimited/landing.html'


class Login(LoginView):
    """ログインページ"""
    form_class = LoginForm
    template_name = 'unlimited/login.html'


class Logout(LogoutView):
    """ログアウトページ"""
    template_name = 'unlimited/landing.html'


class UserCreate(generic.CreateView):
    """ユーザー仮登録"""
    template_name = 'unlimited/user_create.html'
    form_class = UserCreateForm

    def form_valid(self, form):
        """仮登録と本登録用メールの発行."""
        # 仮登録と本登録の切り替えは、is_active属性を使うと簡単です。
        # 退会処理も、is_activeをFalseにするだけにしておくと捗ります。
        user = form.save(commit=False)
        user.is_active = False
        # random_username = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(6)])
        # print(random_username)
        # user.username = random_username
        user.save()

        # アクティベーションURLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': domain,
            'token': dumps(user.pk),
            'user': user,
        }

        subject = render_to_string('unlimited/mail_template/create/subject.txt', context)
        message = render_to_string('unlimited/mail_template/create/message.txt', context)

        user.email_user(subject, message)
        return redirect('unlimited:user_create_done')


class UserCreateDone(generic.TemplateView):
    """ユーザー仮登録"""
    template_name = 'unlimited/user_create_done.html'


class UserCreateComplete(generic.TemplateView):
    """メール内URLアクセス後のユーザー本登録"""
    template_name = 'unlimited/user_create_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60 * 60 * 24)  # デフォルトでは1日以内

    def get(self, request, **kwargs):
        """tokenが正しければ本登録."""
        token = kwargs.get('token')
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                return HttpResponseBadRequest()
            else:
                if not user.is_active:
                    # まだ仮登録で、他に問題なければ本登録とする
                    user.is_active = True
                    user.save()
                    return super().get(request, **kwargs)

        return HttpResponseBadRequest()


class OnlyYouMixin(UserPassesTestMixin):
    """本人か、スーパーユーザーだけユーザーページアクセスを許可する"""
    raise_exception = True

    def test_func(self):
        user = self.request.user
        return user.pk == self.kwargs['pk'] or user.is_superuser


class UserDetail(OnlyYouMixin, generic.DetailView):
    """ユーザーの詳細ページ"""
    model = User
    template_name = 'unlimited/user_detail.html'

    def get_context_data(self, **kwargs):
        user_name = self.request.user.user_name
        reserve_info = Reservation.objects.filter(member=user_name)
        context = super(UserDetail, self).get_context_data(**kwargs)
        context.update({
            'reserve_info': reserve_info
        })


class UserUpdate(OnlyYouMixin, generic.UpdateView):
    """ユーザー情報更新ページ"""
    model = User
    form_class = UserUpdateForm
    template_name = 'unlimited/user_form.html'  # デフォルトユーザーを使う場合に備え、きちんとtemplate名を書く

    def get_success_url(self):
        return resolve_url('unlimited:user_detail', pk=self.kwargs['pk'])


class PasswordChange(PasswordChangeView):
    """パスワード変更ビュー"""
    form_class = MyPasswordChangeForm
    success_url = reverse_lazy('unlimited:password_change_done')
    template_name = 'unlimited/password_change.html'


class PasswordChangeDone(PasswordChangeDoneView):
    """パスワード変更しました"""
    template_name = 'unlimited/password_change_done.html'


class PasswordReset(PasswordResetView):
    """パスワード変更用URLの送付ページ"""
    subject_template_name = 'unlimited/mail_template/password_reset/subject.txt'
    email_template_name = 'unlimited/mail_template/password_reset/message.txt'
    template_name = 'unlimited/password_reset_form.html'
    form_class = MyPasswordResetForm
    success_url = reverse_lazy('unlimited:password_reset_done')


class PasswordResetDone(PasswordResetDoneView):
    """パスワード変更用URLを送りましたページ"""
    template_name = 'unlimited/password_reset_done.html'


class PasswordResetConfirm(PasswordResetConfirmView):
    """新パスワード入力ページ"""
    form_class = MySetPasswordForm
    success_url = reverse_lazy('unlimited:password_reset_complete')
    template_name = 'unlimited/password_reset_confirm.html'


class PasswordResetComplete(PasswordResetCompleteView):
    """新パスワード設定しましたページ"""
    template_name = 'unlimited/password_reset_complete.html'


class EmailChange(LoginRequiredMixin, generic.FormView):
    """メールアドレスの変更"""
    template_name = 'unlimited/email_change_form.html'
    form_class = EmailChangeForm

    def form_valid(self, form):
        user = self.request.user
        new_email = form.cleaned_data['email']

        # URLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': 'https' if self.request.is_secure() else 'http',
            'domain': domain,
            'token': dumps(new_email),
            'user': user,
        }

        subject = render_to_string('unlimited/mail_template/email_change/subject.txt', context)
        message = render_to_string('unlimited/mail_template/email_change/message.txt', context)
        send_mail(subject, message, None, [new_email])

        return redirect('unlimited:email_change_done')


class EmailChangeDone(LoginRequiredMixin, generic.TemplateView):
    """メールアドレスの変更メールを送ったよ"""
    template_name = 'unlimited/email_change_done.html'


class EmailChangeComplete(LoginRequiredMixin, generic.TemplateView):
    """リンクを踏んだ後に呼ばれるメアド変更ビュー"""
    template_name = 'unlimited/email_change_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60 * 60 * 24)  # デフォルトでは1日以内

    def get(self, request, **kwargs):
        token = kwargs.get('token')
        try:
            new_email = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            User.objects.filter(email=new_email, is_active=False).delete()
            request.user.email = new_email
            request.user.save()
            return super().get(request, **kwargs)


class Dashboard(LoginRequiredMixin, generic.TemplateView):
    model = Reservation
    template_name = 'unlimited/dashboard.html'

    def get_context_data(self, **kwargs):
        # ユーザー情報を取得
        user_info = User.objects.filter(pk=self.kwargs['pk'])
        user_name = user_info.values('user_name')
        user_name = user_name[0]['user_name']

        payment_completion_date = user_info.values('payment_completion_date')
        payment_completion_date = payment_completion_date[0]['payment_completion_date']
        payment_completion_date = str(payment_completion_date)
        # print(type(payment_completion_date))

        if payment_completion_date == '9991-12-31':
            status = '利用不可'
            # todo:支払い完了してない場合の処理
        else:
            user_status = Reservation.objects.filter(member=user_name).order_by('-date')
            if user_status.count() == 0:
                status = 'フルカット'
            else:
                status = get_user_status(user_status, 0)

        # 予約履歴を取得
        reserve_history = Reservation.objects.filter(member=user_name).order_by('-date')

        context = super().get_context_data(**kwargs)
        context.update({
            'user_info': user_info,
            'payment_completion_date': payment_completion_date,
            'status': status,
            'reserve_history': reserve_history,
        })
        return context


def get_user_status(obj_reserve_history, int_list_no):
    # 最新の予約が「予約済み」状態だった場合
    if obj_reserve_history.values('status')[int_list_no]['status'] == 0:
        return '利用不可'
    # 最新の予約が「済」だった場合
    elif obj_reserve_history.values('status')[int_list_no]['status'] == 1:
        reserved_date = obj_reserve_history.values('date')[int_list_no]['date']
        now = datetime.datetime.now()
        interval_date = now.date() - reserved_date
        # interval_date = date_reserve_date - reserved_date

        # 当日に2回行こうとした場合、利用不可
        if interval_date == datetime.timedelta(days=0):
            return '利用不可'

        # 最新の予約から30日経過していたらフルカット
        elif interval_date > datetime.timedelta(days=30):
            return 'フルカット'

        # 最新の予約から30日経過していなかったらメンテカット
        elif interval_date <= datetime.timedelta(days=30):
            return 'メンテカット'

    # 最新の予約が「キャンセル」だった場合
    elif obj_reserve_history.values('status')[int_list_no]['status'] == 2:
        try:
            return get_user_status(obj_reserve_history, int_list_no + 1)
        except IndexError:
            return 'フルカット'

    # 最新の予約が「ドタキャン」だった場合
    elif obj_reserve_history.values('status')[int_list_no]['status'] == 3:
        reserved_date = obj_reserve_history.values('date')[int_list_no]['date']
        now = datetime.datetime.now()
        interval_date = now.date() - reserved_date
        # interval_date = date_reserve_date - reserved_date

        # ドタキャンから20日経過していた場合
        if interval_date > datetime.timedelta(days=20):
            try:
                reserved_date = obj_reserve_history.values('date')[int_list_no + 1]['date']
                now = datetime.datetime.now()
                interval_date = now.date() - reserved_date
                # interval_date = date_reserve_date - reserved_date

                # ドタキャンより前の予約から30日経過していた場合
                if interval_date > datetime.timedelta(days=30):
                    return 'フルカット'

                # ドタキャンより前の予約から30日経過していなかった場合
                elif interval_date <= datetime.timedelta(days=30):
                    return 'メンテカット'

            # ドタキャンより前の予約がなかったら
            except IndexError:
                return 'フルカット'

        # ドタキャンから20日経過していなかったら利用不可
        elif interval_date <= datetime.timedelta(days=20):
            return '利用不可'


class SalonListView(generic.ListView):
    model = Salon
    template_name = 'salon_list.html'


class SalonUpdateView(generic.UpdateView):
    model = Salon
    template_name = 'unlimited/salon_update.html'
    form_class = SalonUpdateForm

    def form_valid(self, form):
        salon = form.save(commit=False)
        salon.save()
        return redirect('unlimited:salon_update_complete')


class SalonUpdateComplete(generic.TemplateView):
    template_name = 'unlimited/salon_update_complete.html'


class StylistList(generic.ListView):
    model = Stylist
    template_name = 'unlimited/stylist_list.html'

    def get_context_data(self, **kwargs):
        today = timezone.datetime.now().date()
        month = timezone.datetime.now().month
        first_day = today.replace(day=1)
        last_day = (today + relativedelta(month=month + 1)).replace(day=1)
        # ログインユーザーのサロン：target_salon
        target_salon = Salon.objects.get(salon=self.request.user.pk)

        # 本日以降の予約情報：reservations
        reservations = Reservation.objects.filter(salon=target_salon.id, date__gte=first_day).order_by('-date')

        # 今月の施術完了数
        monthly_info = Reservation.objects.filter(salon=target_salon.id, date__gte=first_day,
                                                  date__lt=last_day, status=1)
        monthly_count = monthly_info.count()

        # 今月のフルカット数
        monthly_count_full_cut = monthly_info.filter(treatment=0).count()

        # 今月のフルカラー数
        monthly_count_full_color = monthly_info.filter(treatment=1).count()

        # 今月のメンテカット数
        monthly_count_mainte_cut = monthly_info.filter(treatment=2).count()

        # 今月のメンテカラー数
        monthly_count_mainte_color = monthly_info.filter(treatment=3).count()

        # サロン情報の取得
        salon_info = Salon.objects.filter(salon=self.request.user.pk)

        # 今月のフルカット売上
        full_cut_prise = salon_info.values('cut_prise')
        monthly_sales_full_cut = monthly_count_full_cut * full_cut_prise[0]['cut_prise']

        # 今月のフルカラー売上
        full_color_prise = salon_info.values('color_prise')
        monthly_sales_full_color = monthly_count_full_color * full_color_prise[0]['color_prise']

        # 今月のメンテカット売上
        mainte_cut_prise = salon_info.values('mainte_cut_prise')
        monthly_sales_mainte_cut = monthly_count_mainte_cut * mainte_cut_prise[0]['mainte_cut_prise']

        # 今月のメンテカラー売上
        mainte_color_prise = salon_info.values('mainte_color_prise')
        monthly_sales_mainte_color = monthly_count_mainte_color * mainte_color_prise[0]['mainte_color_prise']

        # 今月の総売上
        monthly_sales = (monthly_sales_full_cut + monthly_sales_full_color + monthly_sales_mainte_cut +
                         monthly_sales_mainte_color)

        context = super().get_context_data(**kwargs)
        context.update({
            'salon_id': target_salon.id,
            'reservations': reservations,
            'month': month,
            'monthly_count': monthly_count,
            'monthly_sales': monthly_sales,
        })

        return context


class StylistDetail(generic.DetailView):
    model = Stylist
    template_name = 'unlimited/stylist_detail.html'

    def get_context_data(self, **kwargs):
        stylist = self.kwargs['pk']
        reservations = Reservation.objects.filter(stylist=stylist)
        count = Reservation.objects.filter(stylist=stylist).count()
        context = super().get_context_data(**kwargs)
        context.update({
            'reservations': reservations,
            'count': count,
        })
        return context


class StylistCreate(generic.CreateView):
    model = Stylist
    form_class = StylistCreateForm

    def form_valid(self, form):
        salon_pk = self.kwargs['affiliation_salon_id']
        salon = get_object_or_404(Salon, pk=salon_pk)
        stylist = form.save(commit=False)
        stylist.affiliation_salon = salon
        stylist.save()
        return redirect('unlimited:stylist_list')


class StylistDelete(generic.DeleteView):
    model = Stylist
    success_url = reverse_lazy('unlimited:stylist_list')


class ReservationCreate(generic.CreateView):
    model = Reservation
    form_class = ReservationCreateForm

    def get_form_kwargs(self):
        salon_pk = self.kwargs['salon_id']
        user_name = self.kwargs['user_name']
        reserve_date = self.request.GET.get('reserve_date')
        start = self.request.GET.get('start')
        end = self.request.GET.get('end')
        kwargs = super(ReservationCreate, self).get_form_kwargs()
        kwargs['salon_pk'] = salon_pk
        kwargs['user_name'] = user_name
        kwargs['reserve_date'] = reserve_date
        kwargs['start'] = start
        kwargs['end'] = end
        return kwargs

    def form_valid(self, form):
        reservation = form.save(commit=False)
        reservation.save()
        return redirect('unlimited:reservation_create_complete')


class ReservationCreateComplete(generic.TemplateView):
    template_name = 'unlimited/reservation_create_complete.html'


def reservation_update(request, reservation_id):
    if request.method == 'POST':

        if 'complete' in request.POST:
            reservation = Reservation.objects.get(id=reservation_id)
            reservation.status = 1
            reservation.save()

        elif 'cancel' in request.POST:
            reservation = Reservation.objects.get(id=reservation_id)
            reservation.status = 2
            reservation.save()

        elif 'dotacan' in request.POST:
            reservation = Reservation.objects.get(id=reservation_id)
            reservation.status = 3
            reservation.save()

    return redirect('unlimited:stylist_list')


class UserSearch(generic.ListView):
    model = User
    template_name = 'unlimited/reservation_user_search_form.html'

    def get_queryset(self):
        user_id = self.request.GET.get('query')

        # try:
        #     object_list = User.objects.filter(user_name=user_id)
        #     return object_list
        # except User.DoesNotExist:
        #     object_list = ['ユーザーが見つかりません', ]
        #     return object_list

        if user_id:
            object_list = User.objects.filter(user_name=user_id)
        else:
            object_list = ['ユーザーが見つかりません', ]
        return object_list

    def get_context_data(self, **kwargs):
        # ログインユーザーのサロン：target_salon
        target_salon = Salon.objects.get(salon=self.request.user.pk)
        context = super().get_context_data(**kwargs)
        context.update({
            'salon_id': target_salon.id,
        })
        return context


class PrivacyPolicy(generic.TemplateView):
    template_name = 'unlimited/privacy_policy.html'


class TermsOfService(generic.TemplateView):
    template_name = 'unlimited/terms_of_service.html'


class TransactionLaw(generic.TemplateView):
    template_name = 'unlimited/transaction_law.html'

# 以下は使用していないメソッド
# def stylist_create(request):
#     # salon_id = get_object_or_404(Salon, pk=pk)
#     form = StylistCreateForm(request.POST or None)
#     if request.method == 'POST' and form.is_valid():
#         form.save()
#         return redirect('unlimited:stylist_list')
#     context = {
#         'form': form
#     }
#     # context = {
#     #     'form': StylistCreateForm()
#     # }
#     return render(request, 'unlimited/stylist_form.html', context)

# def stylist_create_send(request):
#     form = StylistCreateForm(request.POST)
#     if form.is_valid():
#         form.save()
#         return redirect('unlimited:salon_list')
#     else:
#         context = {
#             'form': form,
#         }
#         return render(request, 'unlimited/stylist_form.html', context)


# def reservation_member_search(request, user_name):
#     session_salon_id = request.session.pop('salon_id', None)  # ReservationCreateから受け取る
#     if session_salon_id is None:
#         return redirect('unlimited:stylist_list')
#
#     member = request.POST['member']
#     if request.method == 'POST':
#         if 'search' in request.POST:
#             try:
#                 user = User.objects.get(user_name=member)
#                 # form = ReservationCreateForm(member)
#
#             except User.DoesNotExist:
#                 user = 'ユーザーが見つかりません'
#     context = {
#         'user': user,
#
#     }
#     # return render(request, 'unlimited/reservation_form.html', context)
#     return redirect('unlimited:reservation_create', salon_id=session_salon_id)
