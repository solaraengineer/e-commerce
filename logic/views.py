
from email import message
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.contrib.messages.storage import session
from django.shortcuts import render, redirect
import traceback
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
import json
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import random
import string
from collections import Counter

from logic.forms import RegisterForm, LoginForm, CheckContactForm, CheckShipping, UpdateDataForm
from logic.models import User, CartItem, Orders


def conf(request):
    return render(request, 'conf.html')


@login_required(login_url='login')
def settings(request):
    user = request.user

    if request.method == 'POST':
        form = UpdateDataForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            new_username = cd.get("username")
            if new_username and new_username != user.username:
                if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                    messages.error(request, 'Username already taken')
                    return render(request, 'settings.html', {'update_form': form})
                user.username = new_username

            password = cd.get("password")
            if password:
                user.set_password(password)
                auth.update_session_auth_hash(request, user)

            user.save()
            messages.success(request, 'Settings updated successfully')
            return redirect('home')
    else:
        form = UpdateDataForm(initial={'username': user.username})

    return render(request, 'settings.html', {'update_form': form})


def home(request):
    if request.user.is_authenticated:
        orders = Orders.objects.filter(user_id=str(request.user.id)).order_by('-date')
        return render(request, 'index.html', {
            'user': request.user,
            'orders': orders,
        })
    else:
        return render(request, 'index.html', {
            'orders': [],
            'user': request.user
        })


def reg(request):
    return render(request, 'reg.html', {
        'reg_form': RegisterForm(),
    })


@login_required(login_url='login')
def checkout(request):
    return render(request, 'checkout.html', {
        'check_form': CheckContactForm(),
        'checkship_form': CheckShipping(),
    })


@login_required(login_url='login')
@require_POST
def delone(request, id):
    try:
        item = CartItem.objects.get(id=id, user=request.user)
        item.delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Item deleted'
        })
    except CartItem.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Item not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to delete item'
        }, status=500)

@login_required(login_url='login')
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

    if request.method == 'POST':
        contact_form = CheckContactForm(request.POST)
        shipping_form = CheckShipping(request.POST)

        if contact_form.is_valid() and shipping_form.is_valid():
            try:
                with transaction.atomic():
                    contact_data = contact_form.cleaned_data
                    shipping_data = shipping_form.cleaned_data

                    user = request.user
                    user.first_name = contact_data['first_name']
                    user.last_name = contact_data['last_name']
                    user.email = contact_data['email']
                    user.phone_number = contact_data['phone_number']
                    user.address = shipping_data['Address']
                    user.city = shipping_data['city']
                    user.state = shipping_data['state']
                    user.zipcode = shipping_data['zipcode']
                    user.country = shipping_data['country']
                    user.save()

                    random_id = '#' + ''.join(random.choices(string.ascii_letters + string.digits, k=11))
                    total = sum(float(c.price) for c in cart)


                    item_counts = Counter([c.item_id for c in cart])
                    items_formatted = ', '.join([f"{item} x{count}" for item, count in item_counts.items()])

                    order = Orders.objects.create(
                        user_id=str(user.id),
                        item=items_formatted,
                        total=total,
                        order_id=random_id,
                        status='Paid'
                    )

                    send_order_confirmation(
                        user=request.user,
                        order_id=random_id,
                        items=items_formatted,
                        total=total
                    )
                    orderadmin(
                        user=request.user,
                        order_id=random_id,
                        items=items_formatted,
                        total=total
                    )

                    cart.delete()

                return render(request, 'conf.html', {
                    'random_id': random_id,
                    'items': [order],
                    'total': round(total, 2),
                })

            except Exception as e:
                messages.error(request, f'Order failed: {str(e)}')
                return redirect('checkout')
        else:
            errors = {}
            if not contact_form.is_valid():
                errors['contact'] = contact_form.errors
            if not shipping_form.is_valid():
                errors['shipping'] = shipping_form.errors

            messages.error(request, 'Please fix the errors in your form')
            return render(request, 'checkout.html', {
                'check_form': contact_form,
                'checkship_form': shipping_form,
                'errors': errors
            })

    return redirect('checkout')


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

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request'
    }, status=400)


def loginn(request):
    return render(request, 'login.html', {
        'login_form': LoginForm(request.POST or None)
    })


@ratelimit(key='ip', rate='5/m', block=True)
def register(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                form = RegisterForm(data)

                if form.is_valid():
                    cd = form.cleaned_data
                    username = cd['username']
                    password = cd['password']

                    if User.objects.filter(username=username).exists():
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Username already exists',
                            'field': 'username'
                        }, status=400)

                    user = User.objects.create_user(username=username, password=password)
                    auth.login(request, user)
                    request.session['username'] = username

                    return JsonResponse({
                        'status': 'success',
                        'message': 'Registration successful',
                        'redirect': '/'
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Validation failed',
                        'errors': form.errors
                    }, status=400)

            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON data'
                }, status=400)
            except Exception as e:
                print(f"REGISTER ERROR: {e}")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Registration failed',
                }, status=500)


    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
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
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
     if request.method == 'POST':
            try:
                data = json.loads(request.body)
                form = LoginForm(data)

                if form.is_valid():
                    cd = form.cleaned_data
                    username = cd['username']
                    password = cd['password']

                    user = User.objects.filter(username=username).first()

                    if user and user.check_password(password):
                        auth.login(request, user)
                        return JsonResponse({
                            'status': 'success',
                            'message': 'Login successful',
                            'redirect': '/'
                        })
                    else:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Invalid username or password',
                            'field': 'password'
                        }, status=401)
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Validation failed',
                        'errors': form.errors
                    }, status=400)

            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON data'
                }, status=400)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Login failed'
                }, status=500)

    form = LoginForm
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
        request.session.pop('username', None)
        request.session.flush()
        messages.success(request, 'Logged out successfully')
        return redirect('home')
    return redirect('home')


@login_required(login_url='login')
@require_POST
def addcart(request):
    try:
        data = json.loads(request.body)
        product_id = data.get('product')
        price = data.get('price')

        if not product_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Product ID is required'
            }, status=400)

        if not price:
            return JsonResponse({
                'status': 'error',
                'message': 'Price is required'
            }, status=400)

        try:
            price = float(price)
            if price <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Price must be greater than 0'
                }, status=400)
        except (ValueError, TypeError):
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid price format'
            }, status=400)

        CartItem.objects.create(
            user=request.user,
            item_id=product_id,
            price=price
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Product added to cart'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to add to cart'
        }, status=500)


@login_required(login_url='login')
@csrf_exempt
@require_POST
def cleancart(request):
    try:
        count, _ = CartItem.objects.filter(user=request.user).delete()
        return JsonResponse({
            'status': 'success',
            'message': 'Cart cleared',
            'deleted_count': count
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to clear cart'
        }, status=500)

@transaction.atomic
def delacc(request):
    if request.method == 'POST':
     user = User.objects.filter(username=request.user).first()
    if user:
     user.delete()
    else:
        return JsonResponse({
            'status': 'error',
        })
    return redirect('login')

@login_required(login_url='login')
@require_POST
def validate_checkout(request):
    try:
        data = json.loads(request.body)
        form_type = data.get('form_type')

        if form_type == 'contact':
            form = CheckContactForm(data)
            if form.is_valid():
                return JsonResponse({
                    'status': 'success',
                    'message': 'Contact info valid'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors
                }, status=400)

        elif form_type == 'shipping':
            form = CheckShipping(data)
            if form.is_valid():
                return JsonResponse({
                    'status': 'success',
                    'message': 'Shipping info valid'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'errors': form.errors
                }, status=400)
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid form type'
            }, status=400)

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Validation failed'
        }, status=500)


def send_order_confirmation(user, order_id, items, total):


    html_message = render_to_string('EMAILCONF.html', {
        'user': user,
        'order_id': order_id,
        'items': items,
        'total': total,
        'site_url': 'https://fwaeh.cloud'
    })

    plain_message = strip_tags(html_message)

    send_mail(
        subject='Order Confirmation',
        message=plain_message,
        from_email='solaradeveloper@gmail.com',
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

def orderadmin(user, order_id, items, total):
    html_message = render_to_string('EMAILADMIN.html', {
        'user': user,
        'order_id': order_id,
        'items': items,
        'total': total,
        'customer_name': f"{user.first_name} {user.last_name}",
        'customer_email': user.email,
        'customer_phone': user.phone_number,
        'shipping_address': f"{user.address}, {user.city}, {user.state} {user.zipcode}, {user.country}",
    })

    plain_message = strip_tags(html_message)

    send_mail(
        subject=f'New Order: {order_id}',
        message=plain_message,
        from_email='solaradeveloper@gmail.com',
        recipient_list=['solaradeveloper@gmail.com'],
        html_message=html_message,
        fail_silently=False,
    )