from django.shortcuts import render
from django.views import generic
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.
from .models import Salon


class SalonListView(ListView):
    model = Salon
    context_object_name = 'salon_list'
    template_name = 'salon_list.html'


class Mypage(LoginRequiredMixin, generic.TemplateView):
    template_name = 'my_page.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #TODO:戻り値を追加する？
        return context
