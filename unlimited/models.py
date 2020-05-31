from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager, PermissionsMixin
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

PLAN = (
    (0, 'カットし放題'),
    (1, 'カラーし放題'),
    (2, 'カット&カラーし放題')
)

TREATMENT = (
    (0, 'フルカット'),
    (1, 'フルカラー'),
    (2, 'メンテカット'),
    (3, 'メンテカラー')
)


# class Plan(models.Model):
#     name = models.CharField(verbose_name='プラン名', max_length=255)
#
#     def __str__(self):
#         return self.name
#
#
# class Treatment(models.Model):
#     name = models.CharField(verbose_name='施術', max_length=255)
#
#     def __str__(self):
#         return self.name


class CustomUserManager(UserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_salon', False)
        return self._create_user(email, password, **extra_fields)

    # Salon作成
    def create_salon(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_salon', True)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is _superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # ユーザーのモデル
    user_name = models.CharField(_('username'),
                                 unique=True,
                                 max_length=20,
                                 help_text=_(
                                     'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
                                 ),
                                 error_messages={
                                     'unique': _('ユーザー名が既に存在しています')
                                 }
                                 )
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)

    is_staff = models.BooleanField(_('staff status'),
                                   default=False,
                                   help_text=_(
                                       'Designates whether the user can log into this admin site.'
                                   ))
    is_active = models.BooleanField(_('active'),
                                    default=True,
                                    help_text=_(
                                        'Designates whether this user should be treated as active.'
                                        'Unselect this instead of deleting accounts.'
                                    ),
                                    )
    created_at = models.DateTimeField(_('date_joined'), default=timezone.now)
    is_user = models.BooleanField(_('is User'),
                                  default=True,
                                  blank=False,
                                  )
    # select_plan = models.ForeignKey(Plan, verbose_name='選択プラン', blank=True, on_delete=models.PROTECT, default='1')
    select_plan = models.IntegerField(verbose_name='選択プラン', choices=PLAN, default=0)
    payment_completion_date = models.DateField(verbose_name='支払い完了日', blank=True, default=timezone.now)
    expire_date = models.DateField(verbose_name='有効期限', blank=True, default=timezone.now)

    objects = CustomUserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    @property
    def username(self):
        """username属性ゲッター
                他のアプリケーションが、username属性にアクセスした場合に備えて定義
                メールアドレスを返す"""

        return self.email

    def __str__(self):
        return self.email


class Salon(models.Model):
    class Meta:
        db_table = 'salon'

    salon = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='サロンID', on_delete=models.PROTECT, null=True,
                              blank=True)
    salon_name = models.CharField(verbose_name='店名', max_length=255, blank=False, null=False)
    salon_email = models.EmailField(verbose_name='店舗メール', null=False,
                                    blank=False, unique=True)
    # salon_password = models.CharField(verbose_name='パスワード', max_length=125, blank=False, null=False)
    home_page = models.URLField(verbose_name='ホームページ', unique=True)
    salon_phone_num_regex = RegexValidator(regex=r'^[0-9]+$', message="電話番号は入力必須です。例:09012345678")
    salon_phone_num = models.CharField(verbose_name='店舗電話番号', null=False, unique=True, blank=False,
                                       validators=[salon_phone_num_regex], max_length=15, )
    salon_address = models.CharField(verbose_name='住所', max_length=255, null=False, blank=False)
    business_hours = models.CharField(verbose_name='営業日時', max_length=255)
    cut_prise = models.IntegerField(verbose_name='カット料金', null=False, blank=False)
    color_prise = models.IntegerField(verbose_name='カラー料金', null=False, blank=False)
    mainte_cut_prise = models.IntegerField(verbose_name='メンテナンスカット料金', null=False, blank=False, default=1500)
    mainte_color_prise = models.IntegerField(verbose_name='メンテナンスカラー料金', null=False, blank=False, default=2000)

    def __str__(self):
        return self.salon_name


class Stylist(models.Model):
    class Meta:
        db_table = 'stylist'

    affiliation_salon = models.ForeignKey(Salon, verbose_name='所属サロン', on_delete=models.PROTECT)
    stylist_name = models.CharField(verbose_name='名前', max_length=255, blank=False, null=False)

    def __str__(self):
        return self.stylist_name


class Reservation(models.Model):
    STATUS = (
        (0, '予約完了'),
        (1, '済'),
        (2, 'キャンセル'),
        (3, 'ドタキャン')
    )

    class Meta:
        db_table = 'Reservation'

    member = models.CharField(verbose_name='お客様ID', max_length=20)
    salon = models.ForeignKey(Salon, verbose_name='予約サロン', on_delete=models.PROTECT)
    stylist = models.ForeignKey(Stylist, verbose_name='指名スタイリスト', on_delete=models.PROTECT)
    # plan = models.ForeignKey(Plan, verbose_name='選択プラン', on_delete=models.PROTECT, blank=True, null=True)
    plan = models.IntegerField(verbose_name='選択プラン', choices=PLAN, default=0)
    # treatment = models.ForeignKey(Treatment, verbose_name='施術', on_delete=models.PROTECT, blank=True, null=True)
    treatment = models.IntegerField(verbose_name='施術', choices=TREATMENT, default=0)
    add_treat = models.TextField(verbose_name='追加施術', blank=True, max_length=255)
    date = models.DateField(verbose_name='予約日', default=timezone.localtime)
    start = models.TimeField(verbose_name='開始時間', default=timezone.localtime)
    end = models.TimeField(verbose_name='終了時間', default=timezone.localtime)
    remarks = models.TextField(verbose_name='備考', blank=True, max_length=255)
    status = models.IntegerField(verbose_name='状態', choices=STATUS, default=0)

    def __str__(self):
        return 'お客様ID：{} - 予約サロン：{}'.format(self.member, self.salon)
