from django.shortcuts import render
from django.views.generic import ListView

# Create your views here.
from .models import Salon


class SalonListView(ListView):
    model = Salon
    context_object_name = 'salon_list'
    template_name = 'salon_list.html'
