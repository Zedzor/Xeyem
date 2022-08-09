from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Dashboard
from .forms import UserCreationForm

from django.contrib.auth import login
from django.urls import reverse_lazy

# Create your views here.

# User views
class CustomLoginView(LoginView):
    template_name = 'app/login.html'
    fields = '__all__'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('index')
    
class RegisterPage(FormView):
    template_name = 'app/register.html'
    form_class = UserCreationForm
    redirect_authenticated_user = True
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        if user is not None:
            login(self.request, user)
        return super(RegisterPage, self).form_valid(form)

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('login')
        return super(RegisterPage, self).get(*args, **kwargs)


# Dashboard Views
class DashboardList(ListView):
    model = Dashboard
    context_object_name = 'dashboards'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['dashboards'] = context['dashboards'].filter(user_id=self.request.user)
            context['count'] = context['dashboards'].count()
            
            search_input = self.request.GET.get('search-area') or ''
            if search_input:
                context['dashboards'] = context['dashboards'].filter(
                    title__contains=search_input)
            context['search_input'] = search_input
            
            context['default_dashboard'] = context['dashboards'].filter(default_dashboard=True)

        return context


# class IndexView(TemplateView):
#     template_name = 'app/index.html'
