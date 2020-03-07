from django.urls import path
from django.views.generic import TemplateView

from unlimited.views import SalonListView


app_name = 'unlimited'
urlpatterns = [
    path('salon_list/', SalonListView.as_view(), name='salon_list'),
    path('', TemplateView.as_view(template_name='landing.html'), name='landing'),
]
