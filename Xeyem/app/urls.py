from django import urls
from django.urls import path
from .views import DashboardDetail, DashboardList, CustomLoginView, DashboardUpdate, RegisterPage, DashboardCreate
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', DashboardList.as_view(), name='index'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', RegisterPage.as_view(), name='register'),
    
    path('dashboard-create/', DashboardCreate.as_view(), name='dashboard-create'),
    path('dashboard-update/<int:pk>/', DashboardUpdate.as_view(), name='dashboard-update'),
    path('dashboard/<int:pk>/', DashboardDetail.as_view(), name='dashboard')
]
