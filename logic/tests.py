# logic/tests.py (for ecommerce project)
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from decimal import Decimal
import json
from unittest.mock import patch, Mock
from logic.models import User, CartItem, Orders

User = get_user_model()


class CartTestCase(TestCase):
    """Test cart functionality"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_add_to_cart(self):
        """Test adding item to cart"""
        response = self.client.post(
            '/addcart/',
            data=json.dumps({
                'product': 'Test Product',
                'price': '99.99'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')

        # Check item was added to database
        cart_item = CartItem.objects.filter(user=self.user).first()
        self.assertIsNotNone(cart_item)
        self.assertEqual(cart_item.item_id, 'Test Product')
        self.assertEqual(cart_item.price, Decimal('99.99'))

    def test_add_to_cart_invalid_price(self):
        """Test adding item with invalid price fails"""
        response = self.client.post(
            '/addcart/',
            data=json.dumps({
                'product': 'Test Product',
                'price': 'invalid'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_add_to_cart_negative_price(self):
        """Test adding item with negative price fails"""
        response = self.client.post(
            '/addcart/',
            data=json.dumps({
                'product': 'Test Product',
                'price': '-50.00'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_delete_cart_item(self):
        """Test deleting single item from cart"""
        cart_item = CartItem.objects.create(
            user=self.user,
            item_id='Test Product',
            price=Decimal('50.00')
        )

        response = self.client.post(f'/delone/{cart_item.id}')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')

        # Check item was deleted
        self.assertFalse(CartItem.objects.filter(id=cart_item.id).exists())

    def test_clear_cart(self):
        """Test clearing entire cart"""
        CartItem.objects.create(user=self.user, item_id='Product 1', price=Decimal('10.00'))
        CartItem.objects.create(user=self.user, item_id='Product 2', price=Decimal('20.00'))
        CartItem.objects.create(user=self.user, item_id='Product 3', price=Decimal('30.00'))

        response = self.client.post('/cleancart/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['deleted_count'], 3)

        # Check cart is empty
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)

    def test_get_cart_data(self):
        """Test retrieving cart data via AJAX"""
        CartItem.objects.create(user=self.user, item_id='Product 1', price=Decimal('25.50'))
        CartItem.objects.create(user=self.user, item_id='Product 2', price=Decimal('74.50'))

        response = self.client.get(
            '/buy/',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['items']), 2)
        self.assertEqual(data['total'], 100.0)


class CheckoutTestCase(TestCase):
    """Test checkout and payment flow"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='buyer',
            password='pass123',
            email='buyer@test.com',
            first_name='Test',
            last_name='Buyer',
            phone_number='123456789'
        )
        self.client.login(username='buyer', password='pass123')

        # Add items to cart
        CartItem.objects.create(user=self.user, item_id='Product A', price=Decimal('50.00'))
        CartItem.objects.create(user=self.user, item_id='Product B', price=Decimal('50.00'))

    @patch('logic.views.requests.post')
    def test_successful_checkout(self, mock_post):
        """Test successful checkout with valid payment"""
        # Mock bank API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'balance': 900.0,
            'user_id': 1
        }
        mock_post.return_value = mock_response

        response = self.client.post('/buy/', {
            'first_name': 'Test',
            'last_name': 'Buyer',
            'email': 'buyer@test.com',
            'phone_number': '123456789',
            'Address': '123 Test St',
            'city': 'Warsaw',
            'state': 'Mazovia',
            'zipcode': '00-000',
            'country': 'Poland',
            'Card': '1234567890123456'
        })

        # Check redirect to confirmation page
        self.assertEqual(response.status_code, 302)

        # Check order was created
        order = Orders.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.total, Decimal('100.00'))
        self.assertEqual(order.status, 'Paid')

        # Check cart was cleared
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)

    @patch('logic.views.requests.post')
    def test_checkout_insufficient_funds(self, mock_post):
        """Test checkout fails with insufficient funds"""
        # Mock bank API response for insufficient funds
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'success': False,
            'error': 'Insufficient funds',
            'balance': 10.0
        }
        mock_post.return_value = mock_response

        response = self.client.post('/buy/', {
            'first_name': 'Test',
            'last_name': 'Buyer',
            'email': 'buyer@test.com',
            'phone_number': '123456789',
            'Address': '123 Test St',
            'city': 'Warsaw',
            'state': 'Mazovia',
            'zipcode': '00-000',
            'country': 'Poland',
            'Card': '1234567890123456'
        })

        # Should redirect back to checkout
        self.assertEqual(response.status_code, 302)

        # No order should be created
        self.assertEqual(Orders.objects.filter(user=self.user).count(), 0)

        # Cart should still have items
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 2)

    @patch('logic.views.requests.post')
    def test_checkout_invalid_card(self, mock_post):
        """Test checkout fails with invalid card"""
        # Mock bank API response for invalid card
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            'success': False,
            'error': 'Invalid card number'
        }
        mock_post.return_value = mock_response

        response = self.client.post('/buy/', {
            'first_name': 'Test',
            'last_name': 'Buyer',
            'email': 'buyer@test.com',
            'phone_number': '123456789',
            'Address': '123 Test St',
            'city': 'Warsaw',
            'state': 'Mazovia',
            'zipcode': '00-000',
            'country': 'Poland',
            'Card': '9999999999999999'
        })

        # Should redirect back to checkout
        self.assertEqual(response.status_code, 302)

        # No order should be created
        self.assertEqual(Orders.objects.filter(user=self.user).count(), 0)

    @patch('logic.views.requests.post')
    def test_checkout_bank_service_down(self, mock_post):
        """Test checkout handles bank service being unavailable"""
        # Mock requests exception
        mock_post.side_effect = Exception("Connection refused")

        response = self.client.post('/buy/', {
            'first_name': 'Test',
            'last_name': 'Buyer',
            'email': 'buyer@test.com',
            'phone_number': '123456789',
            'Address': '123 Test St',
            'city': 'Warsaw',
            'state': 'Mazovia',
            'zipcode': '00-000',
            'country': 'Poland',
            'Card': '1234567890123456'
        })

        # Should redirect back to checkout
        self.assertEqual(response.status_code, 302)

        # No order should be created
        self.assertEqual(Orders.objects.filter(user=self.user).count(), 0)

    def test_checkout_missing_card_number(self):
        """Test checkout fails without card number"""
        response = self.client.post('/buy/', {
            'first_name': 'Test',
            'last_name': 'Buyer',
            'email': 'buyer@test.com',
            'phone_number': '123456789',
            'Address': '123 Test St',
            'city': 'Warsaw',
            'state': 'Mazovia',
            'zipcode': '00-000',
            'country': 'Poland'
            # No Card field
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Orders.objects.filter(user=self.user).count(), 0)


class OrderTestCase(TestCase):
    """Test order management"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='orderuser',
            password='pass123'
        )
        self.client.login(username='orderuser', password='pass123')

    def test_order_confirmation_page(self):
        """Test viewing order confirmation page"""
        order = Orders.objects.create(
            user=self.user,
            item='Product A x2, Product B x1',
            total=Decimal('150.00'),
            order_id='#ABC123',
            status='Paid'
        )

        response = self.client.get(f'/conf/{order.order_id}/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.order_id)
        self.assertContains(response, '150.00')

    def test_order_confirmation_not_found(self):
        """Test viewing non-existent order redirects"""
        response = self.client.get('/conf/#INVALID123/')

        self.assertEqual(response.status_code, 302)

    def test_user_can_only_see_own_orders(self):
        """Test users can only access their own orders"""
        other_user = User.objects.create_user(username='other', password='pass')
        other_order = Orders.objects.create(
            user=other_user,
            item='Secret Product',
            total=Decimal('999.99'),
            order_id='#SECRET',
            status='Paid'
        )

        response = self.client.get(f'/conf/{other_order.order_id}/')

        # Should redirect because order doesn't belong to logged-in user
        self.assertEqual(response.status_code, 302)


class AuthTestCase(TestCase):
    """Test authentication flows"""

    def setUp(self):
        self.client = Client()

    def test_register_user(self):
        """Test user registration"""
        response = self.client.post(
            '/register/',
            data=json.dumps({
                'username': 'newuser',
                'password': 'securepass123'
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')

        # Check user was created
        user = User.objects.filter(username='newuser').first()
        self.assertIsNotNone(user)

    def test_register_duplicate_username(self):
        """Test registration fails with existing username"""
        User.objects.create_user(username='existing', password='pass123')

        response = self.client.post(
            '/register/',
            data=json.dumps({
                'username': 'existing',
                'password': 'newpass456'
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['status'], 'error')

    def test_login_success(self):
        """Test successful login"""
        User.objects.create_user(username='loginuser', password='correctpass')

        response = self.client.post(
            '/login/',
            data=json.dumps({
                'username': 'loginuser',
                'password': 'correctpass'
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')

    def test_login_invalid_credentials(self):
        """Test login fails with wrong password"""
        User.objects.create_user(username='loginuser', password='correctpass')

        response = self.client.post(
            '/login/',
            data=json.dumps({
                'username': 'loginuser',
                'password': 'wrongpass'
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertEqual(data['status'], 'error')

    def test_logout(self):
        """Test logout functionality"""
        user = User.objects.create_user(username='logoutuser', password='pass123')
        self.client.login(username='logoutuser', password='pass123')

        response = self.client.post('/logout/')

        self.assertEqual(response.status_code, 302)

        # Check user is logged out
        response = self.client.get('/checkout/')
        self.assertEqual(response.status_code, 302)  # Redirects to login


class UserSettingsTestCase(TestCase):
    """Test user settings and profile updates"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='settingsuser',
            password='oldpass123'
        )
        self.client.login(username='settingsuser', password='oldpass123')

    def test_update_username(self):
        """Test updating username"""
        response = self.client.post('/settings/', {
            'username': 'newusername',
            'password': ''
        })

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newusername')

    def test_update_password(self):
        """Test updating password"""
        response = self.client.post('/settings/', {
            'username': 'settingsuser',
            'password': 'newpass456'
        })

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass456'))

    def test_delete_account(self):
        """Test account deletion"""
        response = self.client.post('/delacc/')

        # User should be deleted
        self.assertFalse(User.objects.filter(username='settingsuser').exists())