from http.client import NotConnected
from multiprocessing import context
from django.shortcuts import render, redirect
from django.db.models import Count
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormMixin
from django.http import Http404, HttpResponse, JsonResponse
from django.contrib.auth import login
from django.urls import reverse_lazy

from .functionalities.funcs import execute_search
from .models import Address, Dashboard, Note, Search, WebAppearance
from .forms import ExecuteSearchForm, UserCreationForm
from django.shortcuts import get_object_or_404

import datetime

# Dictionary for date range searches
filter_query = {
    'week': datetime.date.today() - datetime.timedelta(days=7),
    'month': datetime.date.today() - datetime.timedelta(days=30),
    'year': datetime.date.today() - datetime.timedelta(days=365),
}

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

class DashboardList(ListView):
    model = Dashboard
    context_object_name = 'dashboards'
    template_name = 'app/dashboard_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['dashboards'] = context['dashboards'].filter(user_id=self.request.user)
            context['count'] = context['dashboards'].count()
            context['form'] = DashboardCreate.get_form_class(DashboardCreate)
            context['form_update'] = DashboardUpdate.get_form_class(DashboardUpdate)
        return context


class HomeView(ListView):
    model = Dashboard
    context_object_name = 'dashboards'
    template_name = 'app/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['dashboards'] = context['dashboards'].filter(user_id=self.request.user)
            context['default_dashboard'] = context['dashboards'].get(default_dashboard=True).pk
            context['notes'] = Note.objects.all()
            context['searches'] = Search.objects.all()
            top_filter = self.request.GET.get('search-area') or 'year'
            end_datetime = datetime.datetime.now()

            # Filter by date range and order by date
            context['searches'] = context['searches'].filter(search_date__range=(filter_query[top_filter], end_datetime)).order_by('-search_date')
            # Group by address and show count
            context['searches'] = context['searches'].values('wallet_address').annotate(count=Count('wallet_address')).order_by('-count')

        return context


class DashboardDetail(LoginRequiredMixin, FormMixin, DetailView):
    model = Dashboard
    context_object_name = 'dashboard'
    template_name = 'app/dashboard.html'
    form_class = ExecuteSearchForm
    
    def get_queryset(self):
        qs = super(DashboardDetail, self).get_queryset().filter(user_id=self.request.user)
        return qs
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        dashboard = Dashboard.objects.get(id=self.kwargs['pk'])
        address = self.request.POST.get('address')
        if address:
            functionalities = dashboard.get_functionalities()
            try:
                results = execute_search(address, functionalities)
                new_search = Search(
                    user_id=self.request.user,
                    wallet_address=address
                )
                new_search.save()
                context = self.get_context_data(**kwargs)
                context['results'] = results
                context['address'] = address
                context['notes'] = Note.objects.filter(wallet_address=address)
                return render(request, 'app/dashboard.html', context)
            except Http404:
                raise


class NoteList(ListView):
    model = Note
    template_name = 'app/note_list.html'
    context_object_name = 'notes'
    slug_field = 'address'
    slug_url_kwarg = 'address'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['notes'] = context['notes'].filter(wallet_address=self.kwargs['address'])
        return context

def success(request):
    return JsonResponse({'success':True}, status=200)

class NoteCreate(LoginRequiredMixin, CreateView):
    model = Note
    fields = ['note']
    slug_field = 'address'
    slug_url_kwarg = 'address'
    success_url = reverse_lazy('success')

    def form_invalid(self, form):
        print(form.errors)
        print(form.non_field_errors)
        print("INVALID")

    def form_valid(self, form):
        form.instance.user_id = self.request.user
        address = self.kwargs['address']
        form.instance.wallet_address = get_object_or_404(Address, address=address)
        return super(NoteCreate, self).form_valid(form)



class NoteDelete(LoginRequiredMixin, DeleteView):
    model = Note
    context_object_name = 'note'
    success_url = reverse_lazy('note-list')

    def get_queryset(self):
        qs = super(NoteDelete, self).get_queryset().filter(user_id=self.request.user)
        return qs
    
    def get(self, *args, **kwargs):
        return redirect('index')

class WebAppearanceCreate(LoginRequiredMixin, CreateView):
    model = WebAppearance
    fields = ['web_address']
    success_url = reverse_lazy('success')

    def form_valid(self, form):
        form.instance.user_id = self.request.user
        address = self.kwargs['address']
        form.instance.address = get_object_or_404(Address, address=address)
        return super(WebAppearanceCreate, self).form_valid(form)
    
class DashboardCreate(LoginRequiredMixin, CreateView):
    model = Dashboard
    fields = [
        'name', 'default_dashboard', 'balance', 'balance_time', 
        'fst_lst_transaction', 'transactions', 'transactions_stats', 
        'related_addresses', 'illegal_activity', 'web_appearances'
    ]
    success_url = reverse_lazy('index')
    
    def get(self, *args, **kwargs):
        return redirect('index')
    
    def form_valid(self, form):
        form.instance.user_id = self.request.user
        return super(DashboardCreate, self).form_valid(form)
    
class DashboardUpdate(LoginRequiredMixin, UpdateView):
    model = Dashboard
    fields = [
        'name', 'default_dashboard', 'balance', 'balance_time', 
        'fst_lst_transaction', 'transactions', 'transactions_stats', 
        'related_addresses', 'illegal_activity', 'web_appearances'
    ]
    success_url = reverse_lazy('index')
    
    def get(self, *args, **kwargs):
        return redirect('index')
    
    def form_valid(self, form):
        form.instance.user_id = self.request.user
        return super(DashboardUpdate, self).form_valid(form)

class DashboardDelete(LoginRequiredMixin, DeleteView):
    model = Dashboard
    context_object_name = 'dashboard'
    success_url = reverse_lazy('index')
    
    def get_queryset(self):
        owner = self.request.user
        return self.model.objects.filter(user_id=owner)
    
    def get(self, *args, **kwargs):
        return redirect('index')



class SearchList(LoginRequiredMixin, ListView):   
    model = Search
    context_object_name = 'searches'
    
    def get_queryset(self):
        qs = super(SearchList, self).get_queryset().filter(user_id=self.request.user)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['searches'] = context['searches'].filter(user_id=self.request.user)
            context['count'] = context['searches'].count()
            # context['form'] = SearchUpdate.get_form_class(SearchUpdate)
                        
        return context

# class SearchUpdate(LoginRequiredMixin, UpdateView):
#     model = Search
#     fields = ['notes']
#     success_url = reverse_lazy('searches')
    
#     def get(self, *args, **kwargs):
#         return redirect('searches')
    
#     def form_valid(self, form):
#         form.instance.user_id = self.request.user
#         return super(SearchUpdate, self).form_valid(form)

# class IndexView(TemplateView):
#     template_name = 'app/index.html'
