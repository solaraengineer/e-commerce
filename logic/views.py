from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse, request

from django.views.decorators.http import require_POST
import json
import random, string

from rest_framework.templatetags.rest_framework import items

from logic.forms import RegisterForm, LoginForm
from logic.models import *


def conf(request):
    return render(request, 'conf.html',{

    })

def home(request):
    return render(request, 'index.html')

def reg(request):
    return render(request, 'reg.html',{
        'reg_form': RegisterForm(),
    })
@login_required(login_url='login')
def checkout(request):
    return render(request, 'checkout.html')


@login_required
def buy(request):
    cart = CartItem.objects.filter(user=request.user).select_related('user')


    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        items = []
        total = 0

        for c in cart:
            total += float(c.price)
            items.append({
                'id': c.id,
                'name': c.item_id,
                'price': float(c.price),
            })

        return JsonResponse({
            'items': items,
            'total': round(total, 2)
        })


    random_id = '#' + ''.join(random.choices(string.ascii_letters + string.digits, k=11))


    total = sum(float(c.price) for c in cart)

    return render(request, 'conf.html', {
        'random_id': random_id,
        'items': cart,
        'total': round(total, 2),
    })

@login_required(login_url='login')
def checkout_data(request):
    cart = CartItem.objects.filter(user=request.user).select_related('user')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        items = []
        total = 0

        for c in cart:
            total += float(c.price)
            items.append({
                'id': c.id,
                'name': c.item_id,
                'price': float(c.price),
            })

        return JsonResponse({
            'items': items,
            'total': round(total, 2)
        })

    return render(request, 'checkout.html', {'cart': cart})



def loginn(request):
    return render(request, 'login.html', {
        'login_form': LoginForm(request.POST or None)
    })


@ratelimit(key='ip', rate='5/m', block=True)
def register(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        cd = form.cleaned_data
        username = cd['username']
        password = cd['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'reg.html', {'reg_form': form})

        user = User.objects.create_user(username=username, password=password)
        auth.login(request, user)
        request.session['username'] = username
        return redirect('home')


    return render(request, 'reg.html', {'reg_form': form})

@ratelimit(key='ip', rate='5/m', block=True)
def login(request):
    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data

        user = User.objects.filter(username=cd['username']).first()

        if user and user.check_password(cd["password"]):
            auth.login(request, user)
            return redirect('home')
        messages.error(request, "Invalid credentials", extra_tags="login")

    return render(request, "login.html", {
        "login_form": form,
    })

def logout_view(request):
    if request.method == 'POST':
        auth.logout(request)
        messages.success(request, 'Login successful')
        return redirect('home')


@login_required
@require_POST
def addcart(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product')
        price = data.get('price')

        CartItem.objects.create(
            user=request.user,
            item_id=product_id,
            price=price
        )

        return JsonResponse({'message': 'Product added to cart'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

