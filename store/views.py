from imaplib import _Authenticator
from django.shortcuts import redirect, render, get_object_or_404
from django.http import JsonResponse
import json
import datetime
from .models import * 
from .utils import cartData, guestOrder
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
def store(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}
	return render(request, 'store/store.html', context)

def productView(request):
	data = cartData(request)
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']
	
	products = Product.objects.all()
	context = {'products':products, 'cartItems':cartItems}
	return render(request, 'store/productView.html', context)


def product_detail_view(request, product_name):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    product = get_object_or_404(Product, name=product_name)

    context = {'product': product, 'cartItems': cartItems}
    return render(request, 'store/productView.html', context)


def signup(request):

	if request.method == "POST":
		username = request.POST['username']
		fname = request.POST['fname']
		lname = request.POST['lname']
		email = request.POST['email']
		pass1 = request.POST['pass1']
		pass2 = request.POST['pass2']

		if User.objects.filter(username=username):
			messages.error(request, 'username already exists. Please try another one')
			return redirect('signup')
		
		if User.objects.filter(email=email):
			messages.error(request, 'Email already registered')
			return redirect('signup')
		
		if len(username)>10:
			messages.error(request, 'Username must be less than 10 characters')
			return redirect('signup')

		if pass1 != pass2:
			messages.error(request, 'Passwords did not match')
			return redirect('signup')

		myuser = User.objects.create_user(username, email, pass1)
		myuser.first_name = fname
		myuser.last_name = lname
		myuser.save()
		c = Customer(user=myuser, name=fname, email=email)
		c.save()
		

		messages.success(request, 'your account is successfully created')
		return redirect('signin')
	
	return render(request, 'store/signup.html')

def signin(request):

	if request.method == "POST":
		username = request.POST['username']
		pass1 = request.POST['pass1']

		user = authenticate(username=username, password=pass1)

		if user is not None:
			login(request, user)
			fname = user.first_name
			return render(request, "store/cart.html", {'fname': fname})

		else:
			messages.error(request, 'Invalid username or password')
			
	return render(request, 'store/signin.html')

def signout(request):
	logout(request)
	messages.success(request, "Logged Out Successfully")
	return redirect('store')




def cart(request):
	data = cartData(request)

	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/cart.html', context)

def checkout(request):
	data = cartData(request)
	
	cartItems = data['cartItems']
	order = data['order']
	items = data['items']

	context = {'items':items, 'order':order, 'cartItems':cartItems}
	return render(request, 'store/checkout.html', context)

def updateItem(request):
	data = json.loads(request.body)
	productId = data['productId']
	action = data['action']
	print('Action:', action)
	print('Product:', productId)

	customer = request.user.customer
	product = Product.objects.get(id=productId)
	order, created = Order.objects.get_or_create(customer=customer, complete=False)

	orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

	if action == 'add':
		orderItem.quantity = (orderItem.quantity + 1)
	elif action == 'remove':
		orderItem.quantity = (orderItem.quantity - 1)

	orderItem.save()

	if orderItem.quantity <= 0:
		orderItem.delete()

	return JsonResponse('Item was added', safe=False)

def processOrder(request):
	transaction_id = datetime.datetime.now().timestamp()
	data = json.loads(request.body)

	if request.user.is_authenticated:
		customer = request.user.customer
		order, created = Order.objects.get_or_create(customer=customer, complete=False)
	else:
		customer, order = guestOrder(request, data)

	total = float(data['form']['total'])
	order.transaction_id = transaction_id

	if total == order.get_cart_total:
		order.complete = True
	order.save()

	if order.shipping == True:
		ShippingAddress.objects.create(
		customer=customer,
		order=order,
		address=data['shipping']['address'],
		city=data['shipping']['city'],
		state=data['shipping']['state'],
		zipcode=data['shipping']['zipcode']
		)
	order.save()

	return JsonResponse('Payment submitted..', safe=False)