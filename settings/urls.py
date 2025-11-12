"""
URL configuration for settings project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from logic.views import *
from logic import views

urlpatterns = [
    path('buy/',views.buy,name='buy'),
    path('conf/', conf),
    path('checkout/', checkout, name='checkout'),
    path('', home, name='home'),
    path('api/checkout/', views.checkout_data, name='checkout_data'),
    path('admin/', admin.site.urls),
    path('login',login,name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/addcart/', views.addcart, name='addacrt'),
    path('reg', reg, name='reg'),
    path('login', loginn, name='login'),
    path('register', register, name='register'),
    ]
