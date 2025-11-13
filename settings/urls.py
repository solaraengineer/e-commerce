"""
URL configuration for settings project.
"""
from django.contrib import admin
from django.urls import path
from logic import views

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Pages
    path('', views.home, name='home'),
    path('reg', views.reg, name='reg'),
    path('login', views.loginn, name='login'),
    path('checkout/', views.checkout, name='checkout'),
    path('conf/', views.conf, name='conf'),

    # Auth
    path('register', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Cart APIs
    path('api/addcart/', views.addcart, name='addcart'),
    path('api/cleancart/', views.cleancart, name='cleancart'),
    path('api/delone/<int:id>/', views.delone, name='delete_cart_item'),
    path('api/checkout/', views.checkout_data, name='checkout_data'),

    # Checkout & Purchase
    path('buy/', views.buy, name='buy'),
    path('api/validate-checkout/', views.validate_checkout, name='validate_checkout'),
]