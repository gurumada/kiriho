from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import UserManager, PermissionsMixin
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.db import models

# Create your models here.
from django.utils import timezone


class Salon(models.Model):
    # サロンモデル
    class Meta:
        db_table = 'salon'

    salon_name = models.CharField(verbose_name='店名', max_length=255, blank=False, null=False)
    salon_email = models.EmailField(verbose_name='店舗メール', null=False,
                                    blank=False, unique=True)
    salon_password = models.CharField(verbose_name='パスワード', max_length=125, blank=False, null=False)
    home_page = models.URLField(verbose_name='ホームページ', unique=True)
    salon_phone_num_regex = RegexValidator(regex=r'^[0-9]+$', message="電話番号は入力必須です。例:09012345678")
    salon_phone_num = models.CharField(verbose_name='店舗電話番号', null=False, unique=True, blank=False,
                                       validators=[salon_phone_num_regex], max_length=15, )
    salon_address = models.CharField(verbose_name='住所', max_length=255, null=False, blank=False)
    business_hours = models.CharField(verbose_name='営業日時', max_length=255)
    cut_prise = models.IntegerField(verbose_name='カット料金', null=False, blank=False)

    def __str__(self):
        return self.salon_name, self.home_page, self.salon_phone_num, self.salon_address, self.business_hours


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
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is _superuser=True.')
        return self._create_user(email, password, **extra_fields)

    class User(AbstractBaseUser, PermissionsMixin):
        email = models.EmailField(_('email address'), unique=True)
        first_name = models.CharField(_('first name'), max_length=30, blank=True)
        last_name = models.CharField(_('last name'), max_length=150, blank=True)

        is_staff = models.BooleanField(
            _('staff status'),
            default=False,
            help_text=_(
                'Designates whether the user can log into this admin site.'),
        )
        is_active = models.BooleanField(
            _('active'),
            default=True,
            help_text=_(
                'Designates whether this user should be treated as active.'
                'Unselect this instead of deleting accounts.'
            ),
        )
        date_joined = models.DateTimeField(_('date_joined'), default=timezone.now)

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
