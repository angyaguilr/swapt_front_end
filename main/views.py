import random
import stripe
import json
from django.shortcuts import render,redirect
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse,HttpResponse
from .models import Banner,Category,Brand,CmntyListing, CmntyCampusPropertyNamePair, ProductAttribute,CartOrder,CartOrderItems,ProductReview,Wishlist,UserAddressBook,  SwaptCampusPropertyNamePair, SwaptListingModel, SwaptListingTag, SwaptPropertyManager, SwaptPaymentHistory, Swapt_Prices, SwaptListingTransactionRef, CmntyListingPrice
from django.db.models import Max,Min,Count,Avg
from django.utils.decorators import method_decorator
from django.shortcuts import render, get_object_or_404
from django.core.mail import send_mail
from accounts.models import SwaptUser
from django.db.models.functions import ExtractMonth
from django.views.generic import View, UpdateView, CreateView, DetailView, ListView, TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.template.loader import render_to_string
from .forms import SignupForm,ReviewAdd,AddressBookForm,ProfileForm, ListingEditForm, ListingRejectForm, CmntyListingCreationForm
from .serializers import CmntyListingSerializer, SwaptListingSerializer, SwaptCampusPropertyNamePairSerializer, CampusPropertyNamePairSerializer, CampusPropertyNamePairSerializer, CmntyListingReviewSerializer, SwaptListingReviewSerializer
from django.contrib.auth import login,authenticate
from django.contrib.auth.decorators import login_required
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
#paypal
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
from django_nextjs.render import render_nextjs_page_sync


stripe.api_key = settings.STRIPE_SECRET_KEY
YOUR_DOMAIN = 'http://127.0.0.1:8000' 

# Home Page
def index(request):
    return render_nextjs_page_sync(request)

def home(request):
	banners=Banner.objects.all().order_by('-id')
	data=CmntyListing.objects.filter(is_featured=True).order_by('-id')
	return render(request,'index.html',{'data':data,'banners':banners})

# Category
def category_list(request):
    data=Category.objects.all().order_by('-id')
    return render(request,'category_list.html',{'data':data})

# Brand
def brand_list(request):
    data=Brand.objects.all().order_by('-id')
    return render(request,'brand_list.html',{'data':data})

# CmntyListing List
def product_list(request):
	total_data=CmntyListing.objects.count()
	data=CmntyListing.objects.all().order_by('-id')[:3]
	min_price=ProductAttribute.objects.aggregate(Min('price'))
	max_price=ProductAttribute.objects.aggregate(Max('price'))
	return render(request,'product_list.html',
		{
			'data':data,
			'total_data':total_data,
			'min_price':min_price,
			'max_price':max_price,
		}
		)

# CmntyListing List According to Category
def category_product_list(request,cat_id):
	category=Category.objects.get(id=cat_id)
	data=CmntyListing.objects.filter(category=category).order_by('-id')
	return render(request,'category_product_list.html',{
			'data':data,
			})

# CmntyListing List According to Brand
def brand_product_list(request,brand_id):
	brand=Brand.objects.get(id=brand_id)
	data=CmntyListing.objects.filter(brand=brand).order_by('-id')
	return render(request,'category_product_list.html',{
			'data':data,
			})

# CmntyListing Detail
def product_detail(request,slug,id):
	product=CmntyListing.objects.get(id=id)
	related_products=CmntyListing.objects.filter(category=product.category).exclude(id=id)[:4]
	colors=ProductAttribute.objects.filter(product=product).values('color__id','color__title','color__color_code').distinct()
	sizes=ProductAttribute.objects.filter(product=product).values('size__id','size__title','price','color__id').distinct()
	reviewForm=ReviewAdd()

	# Check
	canAdd=True
	reviewCheck=ProductReview.objects.filter(user=request.user,product=product).count()
	if request.user.is_authenticated:
		if reviewCheck > 0:
			canAdd=False
	# End

	# Fetch reviews
	reviews=ProductReview.objects.filter(product=product)
	# End

	# Fetch avg rating for reviews
	avg_reviews=ProductReview.objects.filter(product=product).aggregate(avg_rating=Avg('review_rating'))
	# End

	return render(request, 'product_detail.html',{'data':product,'related':related_products,'colors':colors,'sizes':sizes,'reviewForm':reviewForm,'canAdd':canAdd,'reviews':reviews,'avg_reviews':avg_reviews})

# Search
def search(request):
	q=request.GET['q']
	data=CmntyListing.objects.filter(title__icontains=q).order_by('-id')
	return render(request,'search.html',{'data':data})

# Filter Data
def filter_data(request):
	colors=request.GET.getlist('color[]')
	categories=request.GET.getlist('category[]')
	brands=request.GET.getlist('brand[]')
	sizes=request.GET.getlist('size[]')
	minPrice=request.GET['minPrice']
	maxPrice=request.GET['maxPrice']
	allProducts=CmntyListing.objects.all().order_by('-id').distinct()
	allProducts=allProducts.filter(productattribute__price__gte=minPrice)
	allProducts=allProducts.filter(productattribute__price__lte=maxPrice)
	if len(colors)>0:
		allProducts=allProducts.filter(productattribute__color__id__in=colors).distinct()
	if len(categories)>0:
		allProducts=allProducts.filter(category__id__in=categories).distinct()
	if len(brands)>0:
		allProducts=allProducts.filter(brand__id__in=brands).distinct()
	if len(sizes)>0:
		allProducts=allProducts.filter(productattribute__size__id__in=sizes).distinct()
	t=render_to_string('ajax/product-list.html',{'data':allProducts})
	return JsonResponse({'data':t})

# Load More
def load_more_data(request):
	offset=int(request.GET['offset'])
	limit=int(request.GET['limit'])
	data=CmntyListing.objects.all().order_by('-id')[offset:offset+limit]
	t=render_to_string('ajax/product-list.html',{'data':data})
	return JsonResponse({'data':t}
)

# Add to cart
def add_to_cart(request):
	# del request.session['cartdata']
	cart_p={}
	cart_p[str(request.GET['id'])]={
		'image':request.GET['image'],
		'title':request.GET['title'],
		'qty':request.GET['qty'],
		'price':request.GET['price'],
	}
	if 'cartdata' in request.session:
		if str(request.GET['id']) in request.session['cartdata']:
			cart_data=request.session['cartdata']
			cart_data[str(request.GET['id'])]['qty']=int(cart_p[str(request.GET['id'])]['qty'])
			cart_data.update(cart_data)
			request.session['cartdata']=cart_data
		else:
			cart_data=request.session['cartdata']
			cart_data.update(cart_p)
			request.session['cartdata']=cart_data
	else:
		request.session['cartdata']=cart_p
	return JsonResponse({'data':request.session['cartdata'],'totalitems':len(request.session['cartdata'])})

# Cart List Page
def cart_list(request):
	total_amt=0
	if 'cartdata' in request.session:
		for p_id,item in request.session['cartdata'].items():
			total_amt+=int(item['qty'])*float(item['price'])
		return render(request, 'cart.html',{'cart_data':request.session['cartdata'],'totalitems':len(request.session['cartdata']),'total_amt':total_amt})
	else:
		return render(request, 'cart.html',{'cart_data':'','totalitems':0,'total_amt':total_amt})


# Delete Cart Item
def delete_cart_item(request):
	p_id=str(request.GET['id'])
	if 'cartdata' in request.session:
		if p_id in request.session['cartdata']:
			cart_data=request.session['cartdata']
			del request.session['cartdata'][p_id]
			request.session['cartdata']=cart_data
	total_amt=0
	for p_id,item in request.session['cartdata'].items():
		total_amt+=int(item['qty'])*float(item['price'])
	t=render_to_string('ajax/cart-list.html',{'cart_data':request.session['cartdata'],'totalitems':len(request.session['cartdata']),'total_amt':total_amt})
	return JsonResponse({'data':t,'totalitems':len(request.session['cartdata'])})

# Delete Cart Item
def update_cart_item(request):
	p_id=str(request.GET['id'])
	p_qty=request.GET['qty']
	if 'cartdata' in request.session:
		if p_id in request.session['cartdata']:
			cart_data=request.session['cartdata']
			cart_data[str(request.GET['id'])]['qty']=p_qty
			request.session['cartdata']=cart_data
	total_amt=0
	for p_id,item in request.session['cartdata'].items():
		total_amt+=int(item['qty'])*float(item['price'])
	t=render_to_string('ajax/cart-list.html',{'cart_data':request.session['cartdata'],'totalitems':len(request.session['cartdata']),'total_amt':total_amt})
	return JsonResponse({'data':t,'totalitems':len(request.session['cartdata'])})

# Signup Form
def signup(request):
	if request.method=='POST':
		form=SignupForm(request.POST)
		if form.is_valid():
			form.save()
			username=form.cleaned_data.get('username')
			pwd=form.cleaned_data.get('password1')
			user=authenticate(username=username,password=pwd)
			login(request, user)
			return redirect('home')
	form=SignupForm
	return render(request, 'registration/signup.html',{'form':form})


# Checkout
@login_required
def checkout(request):
	total_amt=0
	totalAmt=0
	if 'cartdata' in request.session:
		for p_id,item in request.session['cartdata'].items():
			totalAmt+=int(item['qty'])*float(item['price'])
		# Order
		order=CartOrder.objects.create(
				user=request.user,
				total_amt=totalAmt
			)
		# End
		for p_id,item in request.session['cartdata'].items():
			total_amt+=int(item['qty'])*float(item['price'])
			# OrderItems
			items=CartOrderItems.objects.create(
				order=order,
				invoice_no='INV-'+str(order.id),
				item=item['title'],
				image=item['image'],
				qty=item['qty'],
				price=item['price'],
				total=float(item['qty'])*float(item['price'])
				)
			# End
		# Process Payment
		host = request.get_host()
		paypal_dict = {
		    'business': settings.PAYPAL_RECEIVER_EMAIL,
		    'amount': total_amt,
		    'item_name': 'OrderNo-'+str(order.id),
		    'invoice': 'INV-'+str(order.id),
		    'currency_code': 'USD',
		    'notify_url': 'http://{}{}'.format(host,reverse('paypal-ipn')),
		    'return_url': 'http://{}{}'.format(host,reverse('payment_done')),
		    'cancel_return': 'http://{}{}'.format(host,reverse('payment_cancelled')),
		}
		form = PayPalPaymentsForm(initial=paypal_dict)
		address=UserAddressBook.objects.filter(user=request.user,status=True).first()
		return render(request, 'checkout.html',{'cart_data':request.session['cartdata'],'totalitems':len(request.session['cartdata']),'total_amt':total_amt,'form':form,'address':address})

@csrf_exempt
def payment_done(request):
	returnData=request.POST
	return render(request, 'payment-success.html',{'data':returnData})


@csrf_exempt
def payment_canceled(request):
	return render(request, 'payment-fail.html')


# Save Review
def save_review(request,pid):
	product=CmntyListing.objects.get(pk=pid)
	user=request.user
	review=ProductReview.objects.create(
		user=user,
		product=product,
		review_text=request.POST['review_text'],
		review_rating=request.POST['review_rating'],
		)
	data={
		'user':user.username,
		'review_text':request.POST['review_text'],
		'review_rating':request.POST['review_rating']
	}

	# Fetch avg rating for reviews
	avg_reviews=ProductReview.objects.filter(product=product).aggregate(avg_rating=Avg('review_rating'))
	# End

	return JsonResponse({'bool':True,'data':data,'avg_reviews':avg_reviews})

# User Dashboard
import calendar
def my_dashboard(request):
	orders=CartOrder.objects.annotate(month=ExtractMonth('order_dt')).values('month').annotate(count=Count('id')).values('month','count')
	monthNumber=[]
	totalOrders=[]
	for d in orders:
		monthNumber.append(calendar.month_name[d['month']])
		totalOrders.append(d['count'])
	return render(request, 'user/dashboard.html',{'monthNumber':monthNumber,'totalOrders':totalOrders})

# My Orders
def my_orders(request):
	orders=CartOrder.objects.filter(user=request.user).order_by('-id')
	return render(request, 'user/orders.html',{'orders':orders})

# Order Detail
def my_order_items(request,id):
	order=CartOrder.objects.get(pk=id)
	orderitems=CartOrderItems.objects.filter(order=order).order_by('-id')
	return render(request, 'user/order-items.html',{'orderitems':orderitems})

# Wishlist
def add_wishlist(request):
	pid=request.GET['product']
	product=CmntyListing.objects.get(pk=pid)
	data={}
	checkw=Wishlist.objects.filter(product=product,user=request.user).count()
	if checkw > 0:
		data={
			'bool':False
		}
	else:
		wishlist=Wishlist.objects.create(
			product=product,
			user=request.user
		)
		data={
			'bool':True
		}
	return JsonResponse(data)

# My Wishlist
def my_wishlist(request):
	wlist=Wishlist.objects.filter(user=request.user).order_by('-id')
	return render(request, 'user/wishlist.html',{'wlist':wlist})

# My Reviews
def my_reviews(request):
	reviews=ProductReview.objects.filter(user=request.user).order_by('-id')
	return render(request, 'user/reviews.html',{'reviews':reviews})

# My AddressBook
def my_addressbook(request):
	addbook=UserAddressBook.objects.filter(user=request.user).order_by('-id')
	return render(request, 'user/addressbook.html',{'addbook':addbook})

# Save addressbook
def save_address(request):
	msg=None
	if request.method=='POST':
		form=AddressBookForm(request.POST)
		if form.is_valid():
			saveForm=form.save(commit=False)
			saveForm.user=request.user
			if 'status' in request.POST:
				UserAddressBook.objects.update(status=False)
			saveForm.save()
			msg='Data has been saved'
	form=AddressBookForm
	return render(request, 'user/add-address.html',{'form':form,'msg':msg})

# Activate address
def activate_address(request):
	a_id=str(request.GET['id'])
	UserAddressBook.objects.update(status=False)
	UserAddressBook.objects.filter(id=a_id).update(status=True)
	return JsonResponse({'bool':True})

# Edit Profile
def edit_profile(request):
	msg=None
	if request.method=='POST':
		form=ProfileForm(request.POST,instance=request.user)
		if form.is_valid():
			form.save()
			msg='Data has been saved'
	form=ProfileForm(instance=request.user)
	return render(request, 'user/edit-profile.html',{'form':form,'msg':msg})

# Update addressbook
def update_address(request,id):
	address=UserAddressBook.objects.get(pk=id)
	msg=None
	if request.method=='POST':
		form=AddressBookForm(request.POST,instance=address)
		if form.is_valid():
			saveForm=form.save(commit=False)
			saveForm.user=request.user
			if 'status' in request.POST:
				UserAddressBook.objects.update(status=False)
			saveForm.save()
			msg='Data has been saved'
	form=AddressBookForm(instance=address)
	return render(request, 'user/update-address.html',{'form':form,'msg':msg})

class Index2(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'listings/index.html')
    
class About(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'about.html')


#Checkout with Stripe
class SuccessView(TemplateView):
    template_name = "listings/success.html"

class CancelView(TemplateView):
    template_name = "listings/cancel.html"

class CreateStripeCheckoutSessionView(View):
    """
    Create a checkout session and redirect the user to Stripe's checkout page
    """

    def post(self, request, *args, **kwargs):
        price = ProductAttribute.objects.get(id=self.kwargs["pk"])

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(price.price) * 100,
                        "product_data": {
                            "name": price.product.title,
                            "description": price.product.desc,
                            "images": [
                                f"{settings.BACKEND_DOMAIN}/{price.image}"
                            ],
                        },
                    },
                    "quantity": price.product.quantity,
                }
            ],
            metadata={"listing_id": price.product.id},
            mode="payment",
            success_url=settings.PAYMENT_SUCCESS_URL,
            cancel_url=settings.PAYMENT_CANCEL_URL,
        )
        return redirect(checkout_session.url)

@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    """
    Stripe webhook view to handle checkout session completed event.
    """

    def post(self, request, format=None):
        payload = request.body
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
        sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
        event = None

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            # Invalid payload
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return HttpResponse(status=400)

        if event["type"] == "checkout.session.completed":
            print("Payment successful")
            session = event["data"]["object"]
            customer_email = session["customer_details"]["email"]
            listing_id = session["metadata"]["listing_id"]
            listing = get_object_or_404(SwaptListingModel, id=listing_id)

            send_mail(
                subject="Here is your listing",
                message=f"Thanks for your purchase. The URL is: {listing.url}",
                recipient_list=[customer_email],
                from_email="test@gmail.com",
            )

            SwaptPaymentHistory.objects.create(
                email=customer_email, listing=listing, payment_status="completed"
            ) # Add this
        # Can handle other events here.

        return HttpResponse(status=200)


#Swapt Listings
class SwaptReviewListingsAPI(viewsets.ModelViewSet):
    queryset = SwaptListingModel.objects.filter(confirmed=True)
    serializer_class = SwaptListingReviewSerializer

    def get_queryset(self):

        # Get attributes from query string
        stage = int(self.request.GET.get('stage'))

        if(stage == 5): 
            return SwaptListingModel.objects.filter(stage=5)
        
        locations = self.request.GET.getlist('location', ['ElonNC', 'CollegeParkMD', 'BurlingtonNC', 'ColumbiaMD'])
        propertynames = self.request.GET.getlist('propertyname', ['Oaks', 'MillPoint', 'OakHill'])
        campuses = self.request.GET.getlist('campus', ['Elon', 'UMD', 'UNCG'])
        showNA = self.request.GET.get('showNA', 'true')

        # Same filtering as in the regular review view
        pairs = SwaptCampusPropertyNamePair.objects.filter(propertyname__in=propertynames,campus__in=campuses)
        queryset = SwaptListingModel.objects.filter(stage=stage, location__in=locations, swaptcampuspropertynamepair__in=pairs, confirmed=True).distinct()
        
        if(showNA == "true"):
            queryset = queryset | SwaptListingModel.objects.filter(stage=stage, location__in=locations,
            swaptcampuspropertynamepair__in=pairs, confirmed=True).distinct()
        
        if self.request._request.user.is_swapt_user:
            return queryset.filter(swaptuser=self.request._request.user.swaptuser)
        else:
            return queryset

class SwaptListingsConfirmationView(View):

    # Returns view of swapt_user's unconfirmed listings (this page is redirected to right after the upload page if successful)
    # swapt_user can delete or edit listings
     def get(self, request):
        
        listings = SwaptListingModel.objects.filter(swaptuser=request.user.swaptuser, confirmed=False)

        # Can't access page without unconfirmed listings
        if not listings:
            return redirect("listings:swapt_create")

        template = "swaptlistings/swapt_confirm.html"
        context = {"listings": SwaptListingModel.objects.filter(swaptuser=request.user.swaptuser, confirmed=False)}
        return render(request, template, context)
     def post(self, request):

        listings = SwaptListingModel.objects.filter(swaptuser=request.user.swaptuser, confirmed=False)

        # Sets listings' and pairs' confirm fields to true if swapt_user selected the confirm button
        if request.POST.get('status') == "confirm":
            for listing in listings:
                listing.confirmed = True
                for pair in listing.swaptcampuspropertynamepair_set.all():
                    pair.confirmed = True
                    pair.save()

            SwaptListingModel.objects.bulk_update(listings, ['confirmed'])
            return redirect("listings:swapt_review")

        # If selected the delete button for a specific card, deletes that cards
        elif request.POST.get('status') == "delete":
            id = request.POST['id']
            listings.get(id=id).delete()
            return redirect("listings:swapt_confirm")

        # The only other button that results in a post request is the cancel button, which deletes all unconfirmed cards
        else:
            listings.delete()
            return redirect("listings:swapt__create")['ElonNC', 'CollegeParkMD', 'BurlingtonNC', 'ColumbiaMD']
        
class SwaptListingsReviewView(View):

    def get(self, request):
        template = "swaptlistings/swapt_review.html"
    
        # Gets different attributes from the query string, but by default will be the most expansive possible
        locations = self.request.GET.getlist('location', ['ElonNC', 'CollegeParkMD', 'BurlingtonNC', 'ColumbiaMD'])
        propertynames = self.request.GET.getlist('propertyname', ['Oaks', 'MillPoint', 'OakHill'])
        campuses = self.request.GET.getlist('campus', ['Elon', 'UMD', 'UNCG'])
        showNA = self.request.GET.get('showNA', 'true')

        # Filters to relevant pairs, then when filtering listings filters by those pairs and other attributes
        # Also stage 1 is the review stage
        pairs = SwaptCampusPropertyNamePair.objects.filter(campus__in=campuses, propertyname__in=propertynames)
        queryset = SwaptListingModel.objects.filter(stage=1, location__in=locations, 
            swaptcampuspropertynamepair__in=pairs, confirmed=True).distinct()
        
        # If the user wants to see cards that have 0 in/itemsSold, add those into the queryset too
        if(showNA == "true"):
            queryset = queryset | SwaptListingModel.objects.filter(stage=1, location__in=locations, 
            swaptcampuspropertynamepair__in=pairs, confirmed=True).distinct()

        if request.user.is_swapt_user:
            context = {"user": request.user, "swaptreview": queryset.filter(swaptuser=request.user.swaptuser)}
        elif request.user.is_admin:
            context = {"user": request.user, "swaptreview": queryset[:3]} # Only show 3 at a time for admin
        return render(request, template, context)

    def post(self, request):
        id = request.POST['id']
        listing = SwaptListingModel.objects.get(id=id)

        # Deletes listings or changes stage (i.e. if approve or reject button is pressed)
        if request.POST.get('status'):
            if request.POST.get('status') == "delete" and (request.user.is_admin or (request.user.is_swapt_user and listing.stage != 2)):
                listing.delete()
            elif request.user.is_admin:
                listing.stage = int(request.POST.get('status'))
                if listing.stage == 2:
                    listing.issue = None # If the card is approved again, don't keep previous issue in the database
                listing.save()
        
        
        return redirect("listings:swapt_review")

class SwaptListingEditView(UpdateView):
    form_class = ListingEditForm
    model = SwaptListingModel
    template_name = 'swaptlistings/swapt_edit_form.html'

    def get(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        listing = SwaptListingModel.objects.get(id=pk)

        # Conditionals to make sure user has access to review page for the listing with the particular id requested
        if request.user.is_admin:
            return super().get(self, request, *args, **kwargs)
        if listing.swaptuser != request.user.swaptuser or (request.user.is_swapt_user and listing.stage == 2):
            return redirect('listings:swapt_review')
        return super().get(self, request, *args, **kwargs)
    
    # This function is used to get the initial values of form fields
    # Mostly used for pairs since those are part of a related model (through the manytomany field), so model fields
    # are for the most part automatically filled in with proper intial values
    def get_initial(self):
        pk = self.kwargs['pk']
        listing = SwaptListingModel.objects.get(id=pk)
        pairs = listing.swaptcampuspropertynamepair_set.all()
        
        intial = {'stage': listing.stage, 'campusOne': "", 'propertynameOne': "", 'campusTwo': "", 'propertynameTwo': "", 'campusThree': "", 'propertynameThree': ""}
        
        counter = 1
        
        for pair in pairs:
            if counter == 1:
                intial['campusOne'] = pair.campus
                intial['propertynameOne'] = pair.propertyname
            if counter == 2:
                intial['campusTwo'] = pair.campus
                intial['propertynameTwo'] = pair.propertyname
            if counter == 3:
                intial['campusThree'] = pair.campus
                intial['propertynameThree'] = pair.propertyname

            counter += 1
        
        return intial

    def get_success_url(self):
        pk = self.kwargs['pk']
        # self.request
        listing = SwaptListingModel.objects.get(id=pk)

        # Go back to confirmation page if editing an unconfirmed card, otherwise return to the review page
        if self.request.user.is_swapt_user and not listing.confirmed:
            return reverse_lazy("listings:swapt_confirm")
        if (self.request.user.is_swapt_user and listing.confirmed) or self.request.user.is_admin:
            return reverse_lazy("listings:swapt_review")

    def form_valid(self, form):
        listing = form.save()

        # Change stage, either based on admin changing it or automatic changes when swapt_user updates rejected/reported card
        if self.request.user.is_admin:
            listing.stage = int(form.cleaned_data["stage"])
        elif self.request.user.is_swapt_user and (listing.stage == 3 or listing.stage == 4):
            listing.stage = 1
        listing.save()

        return super().form_valid(form)

class SwaptListingRejectView(UpdateView):
    form_class = ListingRejectForm
    model = SwaptListingModel
    template_name = 'swaptlistings/swapt_reject.html'

    def form_valid(self, form):
        listing = form.save()
        listing.save()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("listings:swapt_review") + "#nav-review-tab" # Go back to the review tab after rejecting since can only reject from that tab

class SwaptListingListAPIView(generics.ListAPIView):
    queryset = SwaptListingModel.objects.filter(confirmed=True)
    serializer_class = SwaptListingSerializer

    def get_queryset(self):

        # Get attibutes
        locations = self.request.GET.getlist('location')
        campuss = self.request.GET.getlist('')
        number = self.request.GET.get('number')

        # Get pairs with  levels specified, then narrow down listings based on those pairs and other attributes
        pairs = SwaptCampusPropertyNamePair.objects.filter(campus__in=campuss)
        queryset = SwaptListingModel.objects.filter(swaptcampuspropertynamepair__in=pairs).distinct()
        queryset = queryset.filter(confirmed=True, stage=2, location__in=locations) # Make sure cards returned in request are approved and confirmed
        queryset = sorted(queryset, key=lambda x: random.random()) # Randomize order as to not give same cards in same order every time to the app
        queryset = queryset[:int(int(number) * .85)] # Only give up to 85% number of cards specified
        queryset = sorted(queryset + sorted(SwaptListingModel.objects.filter(stage=5), key=lambda x: random.random())[:int(int(number) * .15)], key=lambda x: random.random()) # Other 15% of cards are cmnty cards
       
        return queryset


    def list(self, request, **kwargs):
        # Note the use of `get_queryset()` instead of `self.queryset`
        queryset = self.get_queryset()
        # Passes  list in so that serializer can randomly pick the propertyname levels to return in the request for the cards
        serializer = SwaptListingSerializer(queryset, many=True, context={'campuss': self.request.GET.getlist('')})  
        data = serializer.data

        # This is for the animations in the app to work
        # i = int(self.request.GET.get('number'))
        i = int(request.GET.get('number')) - 1
        for entry in data:
            entry["index"] = i
            i -= 1
        return Response(serializer.data)

class SwaptReportListingView(generics.UpdateAPIView):
    queryset = SwaptListingModel.objects.filter(stage=2, confirmed=True)
    serializer_class = SwaptListingSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return SwaptListingModel.objects.filter(stage=2, confirmed=True)

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.get(pk=self.request.GET.get('id'))
        return obj
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)

        instance = self.get_object()
        # Updates listing to be reported with the issue field filled in (it will be whatever the user wrote)
        serializer = self.get_serializer(instance, data={"stage": 4, "issue": request.data["issue"]}, partial=partial) 
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


class SwaptListingsUploaded(View):
    def get(self, request, *args, **kwargs):
        swapt_bundle_items = SwaptListingModel.objects.all()

        context = {
            'swapt_bundle_items': swapt_bundle_items
        }

        return render(request, 'swaptlistings/swapt_listings.html', context)

class SwaptListingsUploadedSearch(View):
    def get(self, request, *args, **kwargs):
        query = self.request.GET.get("q")

        swapt_bundle_items = SwaptListingModel.objects.filter(
            Q(title__icontains=query) |
            Q(desc__icontains=query)
        )

        context = {
            'swapt_bundle_items': swapt_bundle_items
        }

        return render(request, 'swaptlistings/swapt_listings.html', context)

class SwaptListingCreation(View):
    def get(self, request, *args, **kwargs):
        # get every item from each category
        DiningFurnitureSets = CmntyListing.objects.filter(swaptuser=request.user.swaptuser, 
            category__title__contains='DiningFurniture')
        BedroomFurnitureSets = CmntyListing.objects.filter(swaptuser=request.user.swaptuser, category__title__contains='BedroomFurniture')
        OutdoorFurnituresSets = CmntyListing.objects.filter(swaptuser=request.user.swaptuser, category__title__contains='OutdoorFurniture')
        LivingRmFurnitureSets = CmntyListing.objects.filter(swaptuser=request.user.swaptuser, category__title__contains='LivingRmFurniture')

        # pass into context
        context = {
            'DiningFurnitureSets': DiningFurnitureSets,
            'BedroomFurnitureSets': BedroomFurnitureSets,
            'OutdoorFurnituresSets': OutdoorFurnituresSets,
            'LivingRmFurnitureSets': LivingRmFurnitureSets,
        }

        # render the template
        return render(request, 'swaptlistings/swapt_create_form.html', context)

    def post(self, request, *args, **kwargs):
        name = request.POST.get('title')
        propertyname = request.POST.get('propertyname')
        street = request.POST.get('street')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip')

        order_items = {
            'items': []
        }

        items = request.POST.getlist('items[]')

        for item in items:
            swapt_item = CmntyListing.objects.get(pk__contains=int(item))
            item_data = {
                'id': swapt_item.pk,
                'title': swapt_item.title,
                'price': swapt_item.itemPrice
            }

            order_items['items'].append(item_data)

            price = 0
            item_ids = []

        for item in order_items['items']:
            price += item['price']
            item_ids.append(item['id'])

        order = SwaptListingModel.objects.create(
            price=price,
            name=name,
            propertyname=propertyname,
            street=street,
            city=city,
            state=state,
            zip_code=zip_code
        )
        order.items.add(*item_ids)

        # After everything is done, send confirmation email to the user
        body = ('Thank you for your order! Your food is being made and will be delivered soon!\n'
                f'Your total: {price}\n'
                'Thank you again for your order!')

        # send_mail(
        #     'Thank You For Your SwaptListing!',
        #     body,
        #     'example@example.com',
        #     [email],
        #     fail_silently=False
        # )

        context = {
            'items': order_items['items'],
            'price': price
        }

        return redirect('listings:swapt_confirmation', pk=order.pk)  
      
class SwaptListingListView(ListView):
    model = SwaptListingModel
    context_object_name = "swapt_bundle_listings"
    template_name = "swaptlistings/swapt_listing_list.html"

class SwaptListingDetailView(DetailView):
    model = SwaptListingModel
    context_object_name = "swapt_bundle_listing"
    template_name = "swaptlistings/swapt_listing_detail.html"

    def get_context_data(self, **kwargs):
        context = super( SwaptListingDetailView, self).get_context_data()
        context["swapt_prices"] = Swapt_Prices.objects.filter(swapt_bundle_listing=self.get_object())
        return context          

class SwaptListingConfirmation(View):
    def get(self, request, pk, *args, **kwargs):
        order = SwaptListingModel.objects.get(pk=pk)

        context = {
            'pk': order.pk,
            'items': order.items,
            'price': order.price,
        }

        return render(request, 'swaptlistings/swapt_create_confirmation.html', context)

    def post(self, request, pk, *args, **kwargs):
        data = json.loads(request.body)

        if data['isPaid']:
            order = SwaptListingModel.objects.get(pk=pk)
            order.is_paid = True
            order.save()

        return redirect('listings:payment-confirmation')

class SwaptListingPayConfirmation(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'swaptlistings/swapt_pay_confirmation.html')

#Community Listings
class CmntyReviewListingsAPI(viewsets.ModelViewSet):
    queryset = CmntyListing.objects.filter(confirmed=True)
    serializer_class = CmntyListingReviewSerializer

    def get_queryset(self):

        # Get attributes from query string
        stage = int(self.request.GET.get('stage'))

        if(stage == 5): 
            return CmntyListing.objects.filter(stage=5)
        
        locations = self.request.GET.getlist('location', ['ElonNC', 'CollegeParkMD', 'BurlingtonNC', 'ColumbiaMD'])
        propertynames = self.request.GET.getlist('propertyname', ['Oaks', 'MillPoint', 'OakHill'])
        campuses = self.request.GET.getlist('campus', ['Elon', 'UMD', 'UNCG'])
        showNA = self.request.GET.get('showNA', 'true')

        # Same filtering as in the regular review view
        pairs = CmntyCampusPropertyNamePair.objects.filter(propertyname__in=propertynames,campus__in=campuses)
        queryset = CmntyListing.objects.filter(stage=stage, location__in=locations, 
            cmntycampuspropertynamepair__in=pairs, confirmed=True).distinct()
        
        if(showNA == "true"):
            queryset = queryset | CmntyListing.objects.filter(stage=stage, location__in=locations, 
            cmntycampuspropertynamepair__in=pairs, confirmed=True).distinct()
        
        if self.request._request.user.is_swapt_user:
            return queryset.filter(swaptuser=self.request._request.user.swaptuser)
        else:
            return queryset
        
class CmntyListingCreationView(CreateView):
    model = CmntyListing
    form_class = CmntyListingCreationForm
    template_name ="listings/cmnty_create_form.html"

    def form_valid(self, form):
        listing = form.save()
        listing.swaptuser = SwaptUser.objects.get(user=self.request.user) 
        listing.save()
        if self.request.user.is_swapt_user:
            listing.save()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("listings:cmnty_review") + "#nav-cmnty-tab"

class CmntyListingsConfirmationView(View):

    # Returns view of swapt_user's unconfirmed listings (this page is redirected to right after the upload page if successful)
    # swapt_user can delete or edit listings
    def get(self, request):
        
        listings = CmntyListing.objects.filter(swaptuser=request.user.swaptuser, confirmed=False)

        # Can't access page without unconfirmed listings
        if not listings:
            return redirect("listings:cmnty_create")

        template = "listings/cmnty_confirm.html"
        context = {"listings": CmntyListing.objects.filter(swaptuser=request.user.swaptuser, confirmed=False)}
        return render(request, template, context)
    
    def post(self, request):

        listings = CmntyListing.objects.filter(swaptuser=request.user.swaptuser, confirmed=False)

        # Sets listings' and pairs' confirm fields to true if swapt_user selected the confirm button
        if request.POST.get('status') == "confirm":
            for listing in listings:
                listing.confirmed = True
                for pair in listing.cmntycampuspropertynamepair_set.all():
                    pair.confirmed = True
                    pair.save()

            CmntyListing.objects.bulk_update(listings, ['confirmed'])
            return redirect("listings:cmnty_review")

        # If selected the delete button for a specific card, deletes that cards
        elif request.POST.get('status') == "delete":
            id = request.POST['id']
            listings.get(id=id).delete()
            return redirect("listings:cmnty_confirm")

        # The only other button that results in a post request is the cancel button, which deletes all unconfirmed cards
        else:
            listings.delete()
            return redirect("listings:cmnty_create")['ElonNC', 'CollegeParkMD', 'BurlingtonNC', 'ColumbiaMD']

class CmntyListingsReviewView(View):

    def get(self, request):
        template = "listings/cmnty_review.html"
    
        # Gets different attributes from the query string, but by default will be the most expansive possible
        locations = self.request.GET.getlist('location', ['ElonNC', 'CollegeParkMD', 'BurlingtonNC', 'ColumbiaMD'])
        propertynames = self.request.GET.getlist('propertyname', ['Oaks', 'MillPoint', 'OakHill'])
        campuses = self.request.GET.getlist('campus', ['Elon', 'UMD', 'UNCG'])
        showNA = self.request.GET.get('showNA', 'true')

        # Filters to relevant pairs, then when filtering listings filters by those pairs and other attributes
        # Also stage 1 is the review stage
        pairs = CmntyCampusPropertyNamePair.objects.filter(campus__in=campuses, propertyname__in=propertynames)
        queryset = CmntyListing.objects.filter(stage=1, location__in=locations, 
            cmntycampuspropertynamepair__in=pairs, confirmed=True).distinct()
        
        # If the user wants to see cards that have 0 in/itemsSold, add those into the queryset too
        if(showNA == "true"):
            queryset = queryset | CmntyListing.objects.filter(stage=1, location__in=locations, 
            cmntycampuspropertynamepair__in=pairs, confirmed=True).distinct()

        if request.user.is_swapt_user:
            context = {"user": request.user, "review": queryset.filter(swaptuser=request.user.swaptuser)}
        elif request.user.is_admin:
            context = {"user": request.user, "review": queryset[:3]} # Only show 3 at a time for admin
        return render(request, template, context)

    def post(self, request):
        id = request.POST['id']
        listing = CmntyListing.objects.get(id=id)

        # Deletes listings or changes stage (i.e. if approve or reject button is pressed)
        if request.POST.get('status'):
            if request.POST.get('status') == "delete" and (request.user.is_admin or (request.user.is_swapt_user and listing.stage != 2)):
                listing.delete()
            elif request.user.is_admin:
                listing.stage = int(request.POST.get('status'))
                if listing.stage == 2:
                    listing.issue = None # If the card is approved again, don't keep previous issue in the database
                listing.save()
        
        return redirect("listings:cmnty_review")

class CmntyListingEditView(UpdateView):
    form_class = ListingEditForm
    model = CmntyListing
    template_name = 'listings/cmnty_edit_form.html'

    def get(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        listing = CmntyListing.objects.get(id=pk)

        # Conditionals to make sure user has access to review page for the listing with the particular id requested
        if request.user.is_admin:
            return super().get(self, request, *args, **kwargs)
        if listing.swaptuser != request.user.swaptuser or (request.user.is_swapt_user and listing.stage == 2):
            return redirect('listings:cmnty_review')
        return super().get(self, request, *args, **kwargs)
    
    # This function is used to get the initial values of form fields
    # Mostly used for pairs since those are part of a related model (through the manytomany field), so model fields
    # are for the most part automatically filled in with proper intial values
    def get_initial(self):
        pk = self.kwargs['pk']
        listing = CmntyListing.objects.get(id=pk)
        pairs = listing.cmntycampuspropertynamepair_set.all()
        
        intial = {'stage': listing.stage, 'campusOne': "", 'propertynameOne': "", 'campusTwo': "", 'propertynameTwo': "", 'campusThree': "", 'propertynameThree': ""}
        
        counter = 1
        
        for pair in pairs:
            if counter == 1:
                intial['campusOne'] = pair.campus
                intial['propertynameOne'] = pair.propertyname
            if counter == 2:
                intial['campusTwo'] = pair.campus
                intial['propertynameTwo'] = pair.propertyname
            if counter == 3:
                intial['campusThree'] = pair.campus
                intial['propertynameThree'] = pair.propertyname

            counter += 1
        
        return intial

    def get_success_url(self):
        pk = self.kwargs['pk']
        # self.request
        listing = CmntyListing.objects.get(id=pk)

        # Go back to confirmation page if editing an unconfirmed card, otherwise return to the review page
        if self.request.user.is_swapt_user and not listing.confirmed:
            return reverse_lazy("listings:cmnty_confirm")
        if (self.request.user.is_swapt_user and listing.confirmed) or self.request.user.is_admin:
            return reverse_lazy("listings:cmnty_review")

    def form_valid(self, form):
        listing = form.save()

        # Change stage, either based on admin changing it or automatic changes when swapt_user updates rejected/reported card
        if self.request.user.is_admin:
            listing.stage = int(form.cleaned_data["stage"])
        elif self.request.user.is_swapt_user and (listing.stage == 3 or listing.stage == 4):
            listing.stage = 1
        listing.save()

        return super().form_valid(form)

class CmntyListingRejectView(UpdateView):
    form_class = ListingRejectForm
    model = CmntyListing
    template_name = 'listings/cmnty_reject.html'

    def form_valid(self, form):
        listing = form.save()
        listing.save()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("listings:cmnty_review") + "#nav-cmntyreview-tab" # Go back to the review tab after rejecting since can only reject from that tab

class CmntyListingListAPIView(generics.ListAPIView):
    queryset = CmntyListing.objects.filter(confirmed=True)
    serializer_class = CmntyListingSerializer

    def get_queryset(self):

        # Get attibutes
        locations = self.request.GET.getlist('location')
        campuss = self.request.GET.getlist('')
        number = self.request.GET.get('number')

        # Get pairs with  levels specified, then narrow down listings based on those pairs and other attributes
        pairs = CmntyCampusPropertyNamePair.objects.filter(campus__in=campuss)
        queryset = CmntyListing.objects.filter(cmntycampuspropertynamepair__in=pairs).distinct()
        queryset = queryset.filter(confirmed=True, stage=2, location__in=locations) # Make sure cards returned in request are approved and confirmed
        queryset = sorted(queryset, key=lambda x: random.random()) # Randomize order as to not give same cards in same order every time to the app
        queryset = queryset[:int(int(number) * .85)] # Only give up to 85% number of cards specified
        queryset = sorted(queryset + sorted(CmntyListing.objects.filter(stage=5), key=lambda x: random.random())[:int(int(number) * .15)], key=lambda x: random.random()) # Other 15% of cards are cmnty cards
       
        return queryset


    def list(self, request, **kwargs):
        # Note the use of `get_queryset()` instead of `self.queryset`
        queryset = self.get_queryset()
        # Passes  list in so that serializer can randomly pick the propertyname levels to return in the request for the cards
        serializer = CmntyListingSerializer(queryset, many=True, context={'campuss': self.request.GET.getlist('')})  
        data = serializer.data

        # This is for the animations in the app to work
        # i = int(self.request.GET.get('number'))
        i = int(request.GET.get('number')) - 1
        for entry in data:
            entry["index"] = i
            i -= 1
        return Response(serializer.data)

class CmntyReportListingView(generics.UpdateAPIView):
    queryset = CmntyListing.objects.filter(stage=2, confirmed=True)
    serializer_class = CmntyListingSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return CmntyListing.objects.filter(stage=2, confirmed=True)

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.get(pk=self.request.GET.get('id'))
        return obj
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)

        instance = self.get_object()
        # Updates listing to be reported with the issue field filled in (it will be whatever the user wrote)
        serializer = self.get_serializer(instance, data={"stage": 4, "issue": request.data["issue"]}, partial=partial) 
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


class CmntyListingsUploaded(View):
    def get(self, request, *args, **kwargs):
        swapt_items = CmntyListing.objects.all()

        context = {
            'swapt_items': swapt_items
        }

        return render(request, 'listings/cmnty_listings.html', context)

class CmntyListingsUploadedSearch(View):
    def get(self, request, *args, **kwargs):
        query = self.request.GET.get("q")

        swapt_items = CmntyListing.objects.filter(
            Q(title__icontains=query) |
            Q(desc__icontains=query)
        )

        context = {
            'swapt_items': swapt_items
        }

        return render(request, 'listings/cmnty_listings.html', context)
    
class CmntyListingListView(ListView):
    model = CmntyListing
    context_object_name = "listings"
    template_name = "listings/cmnty_listing_list.html"

class CmntyListingDetailView(DetailView):
    model = CmntyListing
    context_object_name = "listing"
    template_name = "listings/cmnty_listing_detail.html"

    def get_context_data(self, **kwargs):
        context = super(CmntyListingDetailView, self).get_context_data()
        context["prices"] = CmntyListingPrice.objects.filter(listing=self.get_object())
        return context 