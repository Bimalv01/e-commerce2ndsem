from datetime import date
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.views import View
from .models import Customer
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib import messages
from .models import *
from .forms import AddressForm
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.db.models import F 
from django.core.mail import send_mail
from django.views.generic import View
from django.conf import settings
from django.http import HttpResponse
from .models import Product
import random
import string


# Create your views here.
# Create your views here.
def index(request):
    products = Product.objects.all()
    return render(request, 'index.html', {'products': products})


def customer_dashboard(request):
    return render(request, 'customer/customer_dashboard.html')

# from django.contrib.auth.password_validation import validate_password
# from django.core.exceptions import ValidationError


def register(request):
    if request.method == 'POST':
        full_name = request.POST.get('full-name')
        email = request.POST.get('your-email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        phone_number = request.POST.get('phone-number')

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, 'Passwords Do Not Match!')
            return render(request, 'customer/register.html')

        # Check password strength using Django's built-in validators
        try:
            validate_password(password)
        except ValidationError as e:
            messages.error(request, ', '.join(e.messages))
            return render(request, 'customer/register.html')

        # Create user
        try:
            user = User.objects.create_user(username=email, email=email, password=password)
        except:
            messages.error(request, 'Email already exists!')
            return render(request, 'customer/register.html')

        # Create customer
        customer = Customer.objects.create(user=user, customer_name=full_name, email=email, contact_number=phone_number)
        
        # Authenticate and login user
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Your Account Has Been Registered Successfully!')
            return redirect('index')
        else:
            messages.error(request, 'Failed to login user.')
            return render(request, 'customer/register.html')

    return render(request, 'customer/register.html')



def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'You have successfully logged in!')
            
            # Redirect based on user role
            try:
                customer = user.customer
                return redirect('index')  # Redirect customer to index page
            except Customer.DoesNotExist:
                try:
                    seller = user.seller
                    return redirect('seller_purchase_orders')  # Redirect seller to seller dashboard
                except Seller.DoesNotExist:
                    messages.error(request, 'You are not authorized to access this page.')
                    return redirect('login')  # Redirect to login page if no associated role found

        else:
            messages.error(request, 'Invalid email or password. Please try again.')
            return render(request, 'customer/login.html')  # Change 'login.html' to your login template path
    return render(request, 'customer/login.html')  # Change 'login.html' to your login template path

def user_logout(request):
    logout(request)
    return redirect('index') 



@login_required
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        user = request.user  # Assuming the user is already logged in

        if user.check_password(old_password):
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password changed successfully.")
                return redirect('login')
            else:
                messages.error(request, "New passwords do not match.")
        else:
            messages.error(request, "Old password is incorrect.")

    return render(request, 'customer/change_password.html')


class CustomTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            str(user.pk) + user.password + str(timestamp)
        )



def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = CustomTokenGenerator().make_token(user)
            reset_password_url = request.build_absolute_uri('/reset_password/{}/{}/'.format(uid, token))
            email_subject = 'Reset Your Password'

            # Render both HTML and plain text versions of the email
            email_body_html = render_to_string('customer/reset_password_email.html', {
                'reset_password_url': reset_password_url,
                'user': user,
            })
            email_body_text = "Click the following link to reset your password: {}".format(reset_password_url)

            # Create an EmailMultiAlternatives object to send both HTML and plain text versions
            email = EmailMultiAlternatives(
                email_subject,
                email_body_text,
                settings.EMAIL_HOST_USER,
                [email],
            )
            email.attach_alternative(email_body_html, 'text/html')  # Attach HTML version
            email.send(fail_silently=False)

            messages.success(request, 'An email has been sent to your email address with instructions on how to reset your password.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "User with this email does not exist.")
    return render(request, 'customer/forgot_password.html')


def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and CustomTokenGenerator().check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password reset successfully. You can now login with your new password.")
                return redirect('login')
            else:
                messages.error(request, "Passwords do not match.")
        return render(request, 'customer/reset_password.html')
    else:
        messages.error(request, "Invalid reset link. Please try again or request a new reset link.")
        return redirect('login')


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Customer

@login_required
def edit_customer(request):
    # Retrieve the current logged-in user
    current_user = request.user
    # Check if the current user has a corresponding Customer instance
    try:
        customer = Customer.objects.get(user=current_user)
    except Customer.DoesNotExist:
        # Handle the case where the logged-in user does not have a corresponding Customer instance
        return HttpResponse("You are not associated with any customer profile.")

    if request.method == 'POST':
        # Update customer details with the data from the form
        customer.customer_name = request.POST['full-name']
        customer.email = request.POST['your-email']
        customer.contact_number = request.POST['phone-number']
        customer.save()

        # Update associated user's email
        current_user.email = request.POST['your-email']
        current_user.username = request.POST['your-email']
        current_user.save()

        # Redirect to the customer detail page after editing
        return redirect('index')

    # If it's a GET request, display the edit form with existing customer details
    return render(request, 'customer/edit_customer.html', {'customer': customer})


    

@login_required
def address_list(request):
    addresses = Address.objects.filter(customer=request.user.customer)
    return render(request, 'customer/address_list.html', {'addresses': addresses})

@login_required
def address_create(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.customer = request.user.customer
            address.save()
            return redirect('address_list')
    else:
        form = AddressForm()
    return render(request, 'customer/address_form.html', {'form': form})

@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, customer=request.user.customer)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return redirect('address_list')
    else:
        form = AddressForm(instance=address)
    return render(request, 'customer/address_form.html', {'form': form})

@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, customer=request.user.customer)
    if request.method == 'POST':
        address.delete()
        return redirect('address_list')
    return render(request, 'customer/address_confirm_delete.html', {'address': address})

def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'product-details.html', {'product': product})

@login_required
def cart(request):
    customer = request.user.customer
    cart_items = Cart.objects.filter(customer=customer)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'cart.html', context)

@login_required
def add_to_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity')
        if product_id and quantity:
            try:
                product = Product.objects.get(pk=product_id)
                customer = request.user.customer
                cart_item, created = Cart.objects.get_or_create(customer=customer, product=product)
                cart_item.quantity += int(quantity)
                if cart_item.quantity <= product.quantity_in_stock:
                    cart_item.save()
                    messages.success(request, f'{quantity} item(s) added to cart.')
                else:
                    messages.error(request, 'Requested quantity exceeds available stock.')
            except Product.DoesNotExist:
                messages.error(request, 'Product does not exist.')
        else:
            messages.error(request, 'Invalid request.')
    return redirect('cart')

@login_required
def delete_item_in_cart(request, id):
    customer = request.user.customer
    product = get_object_or_404(Product, id=id)
    cart_item = Cart.objects.get(customer=customer, product=product)
    cart_item.delete()
    return redirect('cart')


@login_required
def increase_quantity(request, cart_item_id):
    cart_item = Cart.objects.get(pk=cart_item_id)
    if cart_item.quantity < cart_item.product.quantity_in_stock:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart')

@login_required
def decrease_quantity(request, cart_item_id):
    cart_item = Cart.objects.get(pk=cart_item_id)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')

def generate_bill_number(length=8):
    """Generate a random bill number."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=length))

@login_required
def checkout(request):
    customer = request.user.customer
    cart_items = Cart.objects.filter(customer=customer)
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        if not address_id:
            messages.error(request, "Please select or add an address to checkout.")
            return redirect('checkout')
        address = Address.objects.get(id=address_id)
        order = Order.objects.create(customer=customer, address=address)
        for item in cart_items:
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity)
            # Reduce the quantity of the product in stock
            item.product.quantity_in_stock -= item.quantity
            item.product.save()
            item.delete()
        
        # Send confirmation email to customer
        email_subject = 'Order Confirmation'
        email_body_html = render_to_string('order_confirmation_email.html', {'order': order})
        email_body_text = "Thank you for your order. Your order ID is {}. We will process it shortly.".format(order.id)
        email = EmailMultiAlternatives(
            email_subject,
            email_body_text,
            settings.EMAIL_HOST_USER,
            [customer.email],
        )
        email.attach_alternative(email_body_html, 'text/html')
        email.send()
        
        # Generate PDF bill
        bill_number = generate_bill_number()
        pdf_template = get_template('bill_template.html')
        html = pdf_template.render({'order': order, 'bill_number': bill_number})  # Pass bill number to the template
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'filename="bill.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response

        return redirect('order_detail', order.id)
    else:
        addresses = Address.objects.filter(customer=customer)
        context = {
            'cart_items': cart_items,
            'total_price': total_price,
            'addresses': addresses,
        }
        return render(request, 'checkouts.html', context)

@login_required
def order_list(request):
    customer = request.user.customer
    orders = Order.objects.filter(customer=customer)
    for order in orders:
        order.is_cancelled = order.orderitem_set.filter(canceled=True).exists()
    context = {
        'orders': orders,
    }
    return render(request, 'order_list.html', context)

@login_required
def cancel_order_item(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__customer=request.user.customer)
    if not order_item.canceled:
        order_item.canceled = True
        order_item.product.quantity_in_stock += order_item.quantity
        order_item.product.save()
        order_item.save()
        
        # Check if all items are canceled
        order = order_item.order
        if order.orderitem_set.filter(canceled=True).count() == order.orderitem_set.count():
            order.status = 'Cancelled'
            order.save()
    
    return redirect('order_list')

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    context = {
        'order': order,
    }
    return render(request, 'order_detail.html', context)


def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.prefetch_related('subcategory_set').all()
    return render(request, 'product_list.html', {'products': products, 'categories': categories})

def search_results(request):
    query = request.GET.get('q')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    products = Product.objects.filter(name__icontains=query) | \
               Product.objects.filter(subcategory__subcategory_name__icontains=query) | \
               Product.objects.filter(subcategory__parent_category__category_name__icontains=query)

    # Apply price filtering if min_price and max_price are provided
    if min_price and max_price:
        products = products.filter(price__gte=min_price, price__lte=max_price)
    elif min_price:
        products = products.filter(price__gte=min_price)
    elif max_price:
        products = products.filter(price__lte=max_price)

    context = {
        'products': products,
        'query': query,
        'min_price': min_price,
        'max_price': max_price,
    }

    return render(request, 'search_results.html', context)

def category_products(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    products = Product.objects.filter(subcategory__parent_category=category)
    return render(request, 'category_products.html', {'category': category, 'products': products})

def subcategory_products(request, subcategory_id):
    subcategory = get_object_or_404(Subcategory, pk=subcategory_id)
    products = Product.objects.filter(subcategory=subcategory)
    return render(request, 'subcategory_products.html', {'subcategory': subcategory, 'products': products})

# from .forms import PurchaseOrderForm

# def purchase_order(request):
#     products = None  # Initialize products to None
    
#     if request.method == 'POST':
#         form = PurchaseOrderForm(request.POST)
#         if form.is_valid():
#             selected_seller = form.cleaned_data['seller']
#             products = Product.objects.filter(seller=selected_seller)
#     else:
#         form = PurchaseOrderForm()

#     return render(request, 'purchase_order.html', {'form': form, 'products': products})

# from .forms import PurchaseForm


# def make_purchase(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     total_price = product.price  # Default total price to product price

#     if request.method == 'POST':
#         form = PurchaseForm(request.POST)
#         if form.is_valid():
#             quantity = form.cleaned_data['quantity']
#             total_price = product.price * quantity  # Calculate total price based on quantity
#             # Create purchase order
#             purchase_order = PurchaseOrder.objects.create(
#                 seller=product.seller,
#                 product=product,
#                 quantity=quantity,
#                 total_price=total_price
#             )
#             purchase_order.save()
#             return redirect('purchase_list')  # Redirect to purchase list page
#     else:
#         form = PurchaseForm()

#     return render(request, 'make_purchase.html', {'form': form, 'product': product, 'total_price': total_price})

# def purchase_list(request):
#     purchase_orders = PurchaseOrder.objects.all()
#     return render(request, 'purchase_list.html', {'purchase_orders': purchase_orders})


# class SellerLoginView(View):
#     def get(self, request):
#         return render(request, 'login.html')

#     def post(self, request):
#         email = request.POST['email']
#         password = request.POST['password']
#         user = authenticate(request, username=email, password=password)

#         if user is not None:
#             login(request, user)
#             return redirect('purchase_list')
#         else:
#             return render(request, 'login.html', {'error': 'Invalid credentials'})

def seller_purchase_orders(request):
    # Assuming you have a way to identify the current seller, e.g., request.user.seller
    seller = request.user.seller
    purchase_orders = PurchaseOrder.objects.filter(Seller=seller)
    return render(request, 'seller_purchase_orders.html', {'purchase_orders': purchase_orders})

from django.db import transaction

@transaction.atomic
def purchase_order_details(request, purchase_order_id):
    purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)
    order_items = PurchaseOrderItem.objects.filter(PurchaseOrder=purchase_order)
    if request.method == 'POST':
        # Handle form submission to update delivery date and status
        delivery_date = request.POST.get('delivery_date')
        status = request.POST.get('status')
        # Update purchase order with new delivery date and status
        purchase_order.ExpectedDeliveryDate = delivery_date
        purchase_order.Status = status
        purchase_order.save()

        # Update product quantity if status is "Delivered"
        if status == 'Delivered':
            for item in order_items:
                item.Product.quantity_in_stock += item.Quantity
                item.Product.save()
        return redirect('seller_purchase_orders')

    return render(request, 'purchase_order_details.html', {'purchase_order': purchase_order, 'order_items': order_items})

def reject_purchase_order(request, purchase_order_id):
    if request.method == 'GET':
        seller_message = request.GET.get('seller_message', '')  # Get seller message from the query parameters
        purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)  # Get the purchase order object

        # Update purchase order status and seller message
        purchase_order.Status = 'Rejected'
        purchase_order.seller_message = seller_message
        purchase_order.save()

        return redirect('seller_purchase_orders')  # Redirect to seller purchase orders page
    
class CreatePurchaseOrderView(View):
    def get(self, request):
        sellers = Seller.objects.all()
        products = Product.objects.none()  # Initially empty

        if 'seller' in request.GET:
            seller_id = request.GET.get('seller')
            if seller_id:
                products = Product.objects.filter(seller_id=seller_id)
        
        context = {
            'sellers': sellers,
            'products': products,
        }
        return render(request, 'create_purchase_order.html', context)
    
    def post(self, request):
        seller_id = request.POST.get('seller')
        total_amount = request.POST.get('total_amount')

        # Get the selected seller
        selected_seller = Seller.objects.get(id=seller_id)

        # Create the PurchaseOrder object with the selected seller
        purchase_order = PurchaseOrder.objects.create(
            TotalAmount=total_amount,
            PurchaseOrderDate=date.today(),
            Seller=selected_seller,  # Assign the Seller object, not just the ID
        )

        # Save purchase order items
        for i in range(len(request.POST.getlist('product'))):
            product_id = request.POST.getlist('product')[i]
            product = Product.objects.get(id=product_id)
            quantity = request.POST.getlist('quantity')[i]
            purchase_unit_price = Product.objects.get(id=product_id).cost
            
            PurchaseOrderItem.objects.create(
                Product=product,
                Quantity=quantity,
                PurchaseUnitPrice=purchase_unit_price,
                PurchaseOrder=purchase_order,
            )

        return redirect('/admin/eapp/purchaseorder/')  # Redirect to a success page
        


