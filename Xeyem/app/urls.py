from django import urls
from django.urls import path
from .views import DashboardDelete, DashboardDetail, CustomLoginView, DashboardUpdate, HomeView, NoteCreate, NoteDelete, NoteList, RegisterPage, DashboardCreate, SearchList, DashboardList, success
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', HomeView.as_view(), name='index'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', RegisterPage.as_view(), name='register'),
    
    path('dashboard-create/', DashboardCreate.as_view(), name='dashboard-create'),
    path('dashboard-update/<int:pk>/', DashboardUpdate.as_view(), name='dashboard-update'),
    path('dashboard/<int:pk>/', DashboardDetail.as_view(), name='dashboard'),
    path('dashboard-delete/<int:pk>/', DashboardDelete.as_view(), name='dashboard-delete'),

    path('dashboard-list/', DashboardList.as_view(), name='dashboard-list'),
    path('my-searches/', SearchList.as_view(), name='my-searches'),

    path('note-list/<slug:address>', NoteList.as_view(), name='note-list'),
    path('note-create/<slug:address>', NoteCreate.as_view(), name='note-create'),
    path('note-delete/<int:pk>/', NoteDelete.as_view(), name='note-delete'),

    path('note-create/success/', success, name='success'),
]
