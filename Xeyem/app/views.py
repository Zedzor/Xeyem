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
from .templatetags.app_extras import total_votes
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
            context['top_filter'] = top_filter
            # Group by address and show count
            context['searches'] = context['searches'].values('wallet_address').annotate(count=Count('wallet_address')).order_by('-count')
            context['searches'] = context['searches'][:5]
            # get tags for each address
            for search in context['searches']:
                address = Address.objects.filter(address=search['wallet_address'].lower()).first()
                if address:
                    search['tag'] = address.entity_id.entity_tag
                else:
                    search['tag'] = 'Other'
        return context


class DashboardDetail(LoginRequiredMixin, FormMixin, DetailView):
    model = Dashboard
    context_object_name = 'dashboard'
    template_name = 'app/dashboard.html'
    form_class = ExecuteSearchForm
    
    def get_queryset(self):
        qs = super(DashboardDetail, self).get_queryset().filter(user_id=self.request.user)
        return qs

    def __get_most_voted_notes(self, notes):
        note_list = []
        for note in notes:
            note_list.append({
                'note': note,
                'votes': total_votes(note.upvotes, note.downvotes)
            })
        note_list = sorted(note_list, key=lambda k: k['votes'], reverse=True)[:5]
        return [ note['note'] for note in note_list ]
    
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
                context['default_dashboard'] = dashboard.pk
                context['results'] = results
                context['address'] = address.lower()
                context['notes'] = Note.objects.filter(wallet_address=address.lower())
                context['top_notes'] = self.__get_most_voted_notes(context['notes'])
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

class AddressList(ListView):
    model = Address
    template_name = 'app/web-addr.html'
    context_object_name = 'addresses'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            if 'results' not in context:
                context['results'] = {}
            addr = Address.objects.filter(address=self.kwargs['address'])
            context['default_dashboard'] = Dashboard.objects.filter(user_id=self.request.user, default_dashboard=True).first().pk
            context['address'] = addr.first().address
            context['results']['addresses'] = context['addresses'].filter(entity_id=addr.first().entity_id)
            context['results']['web_appearances'] = WebAppearance.objects.filter(address=addr.first())
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

class AddressCreate(LoginRequiredMixin, CreateView):
    model = Address
    fields = ['address']
    success_url = reverse_lazy('success')
    slug_field: str = 'address'
    slug_url_kwarg: str = 'address'
    success_url = reverse_lazy('success')

    def form_invalid(self, form):
        print(form.errors)
        print(form.non_field_errors)
        print("INVALID")
    
    def form_valid(self, form):
        form.instance.informant = self.request.user
        address = self.kwargs['address']
        form.instance.address = form.instance.address.lower()
        form.instance.entity_id = Address.objects.get(address=address).entity_id
        return super(AddressCreate, self).form_valid(form)


class NoteDelete(LoginRequiredMixin, DeleteView):
    model = Note
    context_object_name = 'note'
    success_url = reverse_lazy('note-list')

    def get_queryset(self):
        qs = super(NoteDelete, self).get_queryset().filter(user_id=self.request.user)
        return qs
    
    def get(self, *args, **kwargs):
        return redirect('index')

class AddressDelete(LoginRequiredMixin, DeleteView):
    model = Address
    context_object_name = 'address'
    success_url = reverse_lazy('success')

    def get_queryset(self):
        qs = super(AddressDelete, self).get_queryset().filter(informant=self.request.user)
        return qs
    
    def get(self, *args, **kwargs):
        return redirect('success')

def handle_vote(request, pk):
    if request.method == 'POST':
        # get note from pk from url
        note = get_object_or_404(Note, pk=pk)
        vote = request.POST.get('vote')
        user = request.user
        upvoters = note.upvotes.split(',')
        downvoters = note.downvotes.split(',')
        if vote == 'up':
            if user.email in upvoters:
                return JsonResponse({'success':False}, status=403)
            if user.email in downvoters:
                # remove user and following comma
                note.downvotes = note.downvotes.replace(user.email + ',', '')
            note.upvotes += user.email + ','
            note.save()
            return JsonResponse({'success':True}, status=200)
        elif vote == 'down':
            if user.email in downvoters:
                return JsonResponse({'success':False}, status=403)
            if user.email in upvoters:
                # remove user and following comma
                note.upvotes = note.upvotes.replace(user.email + ',', '')
            note.downvotes += user.email + ','
            note.save()
            return JsonResponse({'success':True}, status=200)
    return JsonResponse({'success':False}, status=400)

class WebAppearanceCreate(LoginRequiredMixin, CreateView):
    model = WebAppearance
    fields = ['web_address']
    success_url = reverse_lazy('success')

    def form_valid(self, form):
        form.instance.informant = self.request.user
        address = self.kwargs['address']
        form.instance.address = get_object_or_404(Address, address=address)
        return super(WebAppearanceCreate, self).form_valid(form)
    
class WebAppearanceDelete(LoginRequiredMixin, DeleteView):
    model = WebAppearance
    context_object_name = 'web_appearance'
    success_url = reverse_lazy('success')

    def get_queryset(self):
        qs = super(WebAppearanceDelete, self).get_queryset().filter(informant=self.request.user)
        return qs
    
    def get(self, *args, **kwargs):
        return redirect('success')

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
