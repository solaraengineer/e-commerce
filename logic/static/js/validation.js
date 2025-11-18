
// Example JavaScript for handling form validation via API

// Helper function to get CSRF token
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Generic function to show error messages
function showError(field, message) {
  const errorDiv = document.getElementById(`${field}-error`);
  if (errorDiv) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
  }

  const inputField = document.getElementById(field);
  if (inputField) {
    inputField.classList.add('error');
  }
}

function clearError(field) {
  const errorDiv = document.getElementById(`${field}-error`);
  if (errorDiv) {
    errorDiv.style.display = 'none';
  }

  const inputField = document.getElementById(field);
  if (inputField) {
    inputField.classList.remove('error');
  }
}

// ===== LOGIN VALIDATION =====
const loginForm = document.getElementById('login-form');
if (loginForm) {
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.querySelector('input[name="username"]').value;
    const password = document.querySelector('input[name="password"]').value;

    // Clear previous errors
    document.querySelectorAll('.error-message').forEach(el => el.remove());

    try {
      const response = await fetch('/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (data.status === 'success') {
        window.location.href = data.redirect;
      } else {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.color = 'red';
        errorDiv.style.marginTop = '10px';
        errorDiv.textContent = data.message;
        loginForm.appendChild(errorDiv);


      }
    } catch (error) {
      console.error('Login error:', error);
      const errorDiv = document.createElement('div');
      errorDiv.className = 'error-message';
      errorDiv.style.color = 'red';
      errorDiv.style.marginTop = '10px';
      errorDiv.textContent = 'An error occurred. Please try again.';
      loginForm.appendChild(errorDiv);
    }
  });
}

// ===== REGISTER VALIDATION =====
const registerForm = document.getElementById('register-form');
if (registerForm) {
  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.querySelector('input[name="username"]').value;
    const password = document.querySelector('input[name="password"]').value;

    // Clear previous errors
    document.querySelectorAll('.error-message').forEach(el => el.remove());

    try {
      const response = await fetch('/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (data.status === 'success') {
        window.location.href = data.redirect;
      } else {
        // Show error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.style.color = 'red';
        errorDiv.style.marginTop = '10px';
        errorDiv.textContent = data.message;
        registerForm.appendChild(errorDiv);
      }
    } catch (error) {
      console.error('Registration error:', error);
      const errorDiv = document.createElement('div');
      errorDiv.className = 'error-message';
      errorDiv.style.color = 'red';
      errorDiv.style.marginTop = '10px';
      errorDiv.textContent = 'An error occurred. Please try again.';
      registerForm.appendChild(errorDiv);
    }
  });
}

// ===== CHECKOUT VALIDATION (SIMPLIFIED) =====
// This will just let the forms submit normally unless you want to add specific validation later
// To add validation, you need error divs in your checkout.html like:
// <div id="fieldname-error" class="error-message" style="display:none; color:red;"></div>


// ===== ADD TO CART VALIDATION =====
document.querySelectorAll('.add-to-cart').forEach(button => {
  button.addEventListener('click', async () => {
    const productId = button.id;

    // Find the price element - try multiple ways
    let priceElement = document.getElementById(`price-${productId}`);
    if (!priceElement) {
      // Try finding it as sibling or parent
      priceElement = button.closest('.product-card')?.querySelector('.product-price');
    }

    if (!priceElement) {
      console.error('Price element not found for product:', productId);
      alert('Error: Could not find product price');
      return;
    }

    const priceText = priceElement.textContent || priceElement.innerText;
    const price = parseFloat(priceText.replace(/[^0-9.]/g, ''));

    if (isNaN(price) || price <= 0) {
      console.error('Invalid price:', priceText);
      alert('Error: Invalid product price');
      return;
    }

    try {
      const response = await fetch('/api/addcart/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
          product: productId,
          price: price,
        }),
      });

      const data = await response.json();

      if (data.status === 'success') {
        // Show success feedback
        button.textContent = 'Added ✓';
        button.style.background = '#10B981';
        setTimeout(() => {
          button.textContent = 'Add to Cart';
          button.style.background = '';
        }, 2000);
        console.log('Item added to cart successfully');
      } else {
        alert(data.message || 'Failed to add item to cart');
      }
    } catch (error) {
      console.error('Error adding to cart:', error);
      alert('An error occurred. Please try again.');
    }
  });
});

// Note: For real-time input validation, add this code when you have the proper HTML structure with error divs