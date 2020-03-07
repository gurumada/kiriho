from django.core.validators import RegexValidator
from django.db import models


# Create your models here.
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
