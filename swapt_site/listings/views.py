import csv, io
import random
import stripe
import json

from django.shortcuts import redirect, render
from django.contrib import messages
from django.views.generic import View, UpdateView, CreateView, DetailView, ListView, TemplateView
from django.urls import reverse_lazy, reverse
from django.db.models import Max,Min,Count,Avg
from rest_framework import generics, viewsets
from django.template.loader import render_to_string
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.db.models import Q
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse,HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from accounts.models import SwaptUser
from .models import  Banner, CmntyListingsCategory, Brand, Color, Dimensions, CmntyListingPrice, CmntyListingTag, CmntyListing, CmntyCampusPropertyNamePair, CmntyListingAttribute, Swapt_Prices, SwaptCampusPropertyNamePair, SwaptListingModel, SwaptListingTag, SwaptPropertyManager, SwaptPaymentHistory, SwaptListingTransactionRef
from .forms import ListingEditForm, ListingRejectForm, CmntyListingCreationForm, ListingCreationForm, CmntyListingPriceCreationForm
from .serializers import CmntyListingSerializer, SwaptListingSerializer, SwaptCampusPropertyNamePairSerializer, CampusPropertyNamePairSerializer, CampusPropertyNamePairSerializer, CmntyListingReviewSerializer, SwaptListingReviewSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY
YOUR_DOMAIN = 'http://127.0.0.1:8000' 

# stripe.Account.create(type="express")

# stripe.AccountLink.create(
#   account="acct_1032D82eZvKYlo2C",
#   refresh_url="https://example.com/reauth",
#   return_url="https://example.com/return",
#   type="account_onboarding",
# )
import csv, io
import random

from django.shortcuts import redirect, render
from django.contrib import messages
from django.views.generic import View, UpdateView, CreateView
from django.urls import reverse_lazy, reverse
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Banner, CmntyListingsCategory, Brand, Color, Dimensions, CmntyListingPrice, CmntyListingTag, CmntyListing, CmntyCampusPropertyNamePair, CmntyListingAttribute, Swapt_Prices, SwaptCampusPropertyNamePair, SwaptListingModel, SwaptListingTag, SwaptPropertyManager, SwaptPaymentHistory, SwaptListingTransactionRef
from .forms import ListingEditForm, ListingRejectForm, CmntyListingCreationForm
from .serializers import SwaptListingSerializer, SwaptListingReviewSerializer, CmntyListingSerializer

#index /about
class Index(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'listings/index.html')
    
class About(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'listings/about.html')


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
        price = CmntyListingPrice.objects.get(id=self.kwargs["pk"])

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(price.price) * 100,
                        "product_data": {
                            "name": price.listing.title,
                            "description": price.listing.desc,
                            "images": [
                                f"{settings.BACKEND_DOMAIN}/{price.listing.thumbnail}"
                            ],
                        },
                    },
                    "quantity": price.listing.quantity,
                }
            ],
            metadata={"listing_id": price.listing.id},
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

        template = "listings/swapt_confirm.html"
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
        template = "listings/swapt_review.html"
    
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
    template_name = 'listings/swapt_edit_form.html'

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
    template_name = 'listings/swapt_reject.html'

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

        return render(request, 'listings/swapt_listings.html', context)

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

        return render(request, 'listings/swapt_listings.html', context)

class SwaptListingCreation(View):
    def get(self, request, *args, **kwargs):
        # get every item from each category
        DiningFurnitureSets = CmntyListing.objects.filter(swaptuser=request.user.swaptuser, 
            category__name__contains='DiningFurniture')
        BedroomFurnitureSets = CmntyListing.objects.filter(swaptuser=request.user.swaptuser, category__name__contains='BedroomFurniture')
        OutdoorFurnituresSets = CmntyListing.objects.filter(swaptuser=request.user.swaptuser, category__name__contains='OutdoorFurniture')
        LivingRmFurnitureSets = CmntyListing.objects.filter(swaptuser=request.user.swaptuser, category__name__contains='LivingRmFurniture')

        # pass into context
        context = {
            'DiningFurnitureSets': DiningFurnitureSets,
            'BedroomFurnitureSets': BedroomFurnitureSets,
            'OutdoorFurnituresSets': OutdoorFurnituresSets,
            'LivingRmFurnitureSets': LivingRmFurnitureSets,
        }

        # render the template
        return render(request, 'listings/swapt_create_form.html', context)

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
    template_name = "listings/swapt_listing_list.html"

class SwaptListingDetailView(DetailView):
    model = SwaptListingModel
    context_object_name = "swapt_bundle_listing"
    template_name = "listings/swapt_listing_detail.html"

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

        return render(request, 'listings/swapt_create_confirmation.html', context)

    def post(self, request, pk, *args, **kwargs):
        data = json.loads(request.body)

        if data['isPaid']:
            order = SwaptListingModel.objects.get(pk=pk)
            order.is_paid = True
            order.save()

        return redirect('listings:payment-confirmation')

class SwaptListingPayConfirmation(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'listings/swapt_pay_confirmation.html')

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
    
class CmntyListingPriceCreationView(CreateView):
    model = CmntyListingPrice
    form_class = CmntyListingPriceCreationForm
    template_name ="listings/cmnty_create_price.html"

    def form_valid(self, form):
        price = form.save()
        if self.request.user.is_swapt_user:
            price.save()

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

