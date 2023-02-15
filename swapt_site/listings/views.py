import csv, io
import random
import stripe

from django.shortcuts import redirect, render
from django.contrib import messages
from django.views.generic import View, UpdateView, CreateView, DetailView, ListView, TemplateView
from django.urls import reverse_lazy, reverse
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import render
from django.conf import settings
from django.db.models import Q
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse,HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import Listing, CampusPropertyNamePair, Order,  Price, PaymentHistory, OrderModel, Category
from .forms import ListingEditForm, ListingRejectForm, CommMktListingCreationForm, ListingCreationForm
from .serializers import ListingSerializer, ListingReviewSerializer

stripe.api_key = settings.STRIPE_SECRET_KEY
YOUR_DOMAIN = 'http://127.0.0.1:8000' 

# stripe.Account.create(type="express")

# stripe.AccountLink.create(
#   account="acct_1032D82eZvKYlo2C",
#   refresh_url="https://example.com/reauth",
#   return_url="https://example.com/return",
#   type="account_onboarding",
# )


# @csrf_exempt
# def create_checkout_session(request):
#     #Updated- creating Order object
#     order=Order(email=" ",paid="False",amount=0,description=" ")
#     order.save()
#     session = stripe.checkout.Session.create(
#         client_reference_id=request.user.id if request.user.is_authenticated else None,
#         payment_method_types=['card'],
#         line_items=[{
#             'price_data': {
#                 'currency': 'usd',
#                 'product_data': {
#                     'name': 'Swapt Listings',
#                     },
#                     'unit_amount': 10000,
#                     },
#                     'quantity': 1,
#         }],
#         #Update - passing order ID in checkout to update the order object in bhookhook
#         metadata={
#             "order_id":swapt_create.id
#             },
#             mode='payment',
#             success_url='http://127.0.0.1:8000/listings/success.html/',
#             cancel_url='http://127.0.0.1:8000/listings/cancel.html/',
#     )
#     return JsonResponse({'id': session.id})

class ListingListView(ListView):
    model = Listing
    context_object_name = "listings"
    template_name = "listings/cmnty_listing_list.html"

class ListingDetailView(DetailView):
    model = Listing
    context_object_name = "listing"
    template_name = "listings/cmnty_listing_detail.html"

    def get_context_data(self, **kwargs):
        context = super(ListingDetailView, self).get_context_data()
        context["prices"] = Price.objects.filter(listing=self.get_object())
        return context           


class SuccessView(TemplateView):
    template_name = "listings/cmnty_success.html"

class CancelView(TemplateView):
    template_name = "listings/cmnty_cancel.html"


class CreateStripeCheckoutSessionView(View):
    """
    Create a checkout session and redirect the user to Stripe's checkout page
    """

    def post(self, request, *args, **kwargs):
        price = Price.objects.get(id=self.kwargs["pk"])

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(price.price) * 100,
                        "product_data": {
                            "name": price.listing.name,
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
            listing = get_object_or_404(Listing, id=listing_id)

            send_mail(
                subject="Here is your listing",
                message=f"Thanks for your purchase. The URL is: {listing.url}",
                recipient_list=[customer_email],
                from_email="test@gmail.com",
            )

            PaymentHistory.objects.create(
                email=customer_email, listing=listing, payment_status="completed"
            ) # Add this
        # Can handle other events here.

        return HttpResponse(status=200)

class ListingsCreationView(ListView):
    model = Listing
    form_class = ListingCreationForm
    template_name ="listings/swapt_upload_form.html"

    def form_valid(self, form):
        listing = form.save()
        if self.request.user.is_swapt_user:
            listing.save()

        return super().form_valid(form)

    def get_success_url(self):
        return redirect("listings:confirm")

class CommMktListingCreationView(CreateView):
    model = Listing
    form_class = CommMktListingCreationForm
    template_name ="listings/cmnty_create_form.html"

    def form_valid(self, form):
        listing = form.save()
        if self.request.user.is_swapt_user:
            listing.save()

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("listings:review") + "#nav-commMkt-tab"

class ListingsConfirmationView(View):

    # Returns view of swaptuser's unconfirmed listings (this page is redirected to right after the upload page if successful)
    # SwaptUser can delete or edit listings
    def get(self, request):
        
        listings = Listing.objects.filter(swaptuser=request.user.swaptuser, confirmed=False)

        # Can't access page without unconfirmed listings
        if not listings:
            return redirect("listings:upload_swapt")

        template = "listings/confirm.html"
        context = {"listings": Listing.objects.filter(swaptuser=request.user.swaptuser, confirmed=False)}
        return render(request, template, context)
    
    def post(self, request):

        listings = Listing.objects.filter(swaptuser=request.user.swaptuser, confirmed=False)

        # Sets listings' and pairs' confirm fields to true if swaptuser selected the confirm button
        if request.POST.get('status') == "confirm":
            for listing in listings:
                listing.confirmed = True
                for pair in listing.campuspropertynamepair_set.all():
                    pair.confirmed = True
                    pair.save()

            Listing.objects.bulk_update(listings, ['confirmed'])
            return redirect("listings:review")

        # If selected the delete button for a specific list, deletes that listings
        elif request.POST.get('status') == "delete":
            id = request.POST['id']
            listings.get(id=id).delete()
            return redirect("listings:confirm")

        # The only other button that results in a post request is the cancel button, which deletes all unconfirmed listings
        else:
            listings.delete()
            return redirect("listings:upload_swapt")['Columbia, MD', 'ElonNC', 'Burlington, NC', 'College Park MD']

class ListingsReviewView(View):

    def get(self, request):
        template = "listings/review.html"
    
        # Gets different attributes from the query string, but by default will be the most expansive possible
        locations = self.request.GET.getlist('location', ['Columbia, MD', 'ElonNC', 'Burlington, NC', 'College Park MD'])
        propertynames = self.request.GET.getlist('propertyname', ['Oaks', 'Park Place', 'Mill Point'])
        lowCampus = int(self.request.GET.get('lowCampus', 1))
        highCampus = int(self.request.GET.get('highCampus', 12))
        lowItemsSold = float(self.request.GET.get('lowItemsSold', 0.0))
        highItemsSold = float(self.request.GET.get('highItemsSold', 100.0))
        showNA = self.request.GET.get('showNA', 'true')

        # Filters to relevant pairs, then when filtering listings filters by those pairs and other attributes
        # Also stage 1 is the review stage
        pairs = CampusPropertyNamePair.objects.filter(campus__gte=lowCampus, campus__lte=highCampus, propertyname__in=propertynames)
        queryset = Listing.objects.filter(stage=1, location__in=locations, percent_itemsSold__gte=lowItemsSold, percent_itemsSold__lte=highItemsSold, 
            campuspropertynamepair__in=pairs, confirmed=True).distinct()
        
        # If the user wants to see listings that have 0 in/itemsSold, add those into the queryset too
        if(showNA == "true"):
            queryset = queryset | Listing.objects.filter(stage=1, location__in=locations, percent_itemsSold=None, 
            campuspropertynamepair__in=pairs, confirmed=True).distinct()

        if request.user.is_swapt_user:
            context = {"user": request.user, "review": queryset.filter(swaptuser=request.user.swaptuser)}
        elif request.user.is_admin:
            context = {"user": request.user, "review": queryset[:3]} # Only show 3 at a time for admin
        return render(request, template, context)

    def post(self, request):
        id = request.POST['id']
        listing = Listing.objects.get(id=id)

        # Deletes listings or changes stage (i.e. if approve or reject button is pressed)
        if request.POST.get('status'):
            if request.POST.get('status') == "delete" and (request.user.is_admin or (request.user.is_swapt_user and listing.stage != 2)):
                listing.delete()
            elif request.user.is_admin:
                listing.stage = int(request.POST.get('status'))
                if listing.stage == 2:
                    listing.issue = None # If the list is approved again, don't keep previous issue in the database
                listing.save()
        
        return redirect("listings:review")

class ListingEditView(UpdateView):
    form_class = ListingEditForm
    model = Listing
    template_name = 'listings/edit_form.html'

    def get(self, request, *args, **kwargs):
        pk = self.kwargs['pk']
        listing = Listing.objects.get(id=pk)

        # Conditionals to make sure user has access to review page for the listing with the particular id requested
        if request.user.is_admin:
            return super().get(self, request, *args, **kwargs)
        if listing.swaptuser != request.user.swaptuser or (request.user.is_swapt_user and listing.stage == 2):
            return redirect('listings:review')
        return super().get(self, request, *args, **kwargs)
    
    # This function is used to get the initial values of form fields
    # Mostly used for pairs since those are part of a related model (through the manytomany field), so model fields
    # are for the most part automatically filled in with proper intial values
    def get_initial(self):
        pk = self.kwargs['pk']
        listing = Listing.objects.get(id=pk)
        pairs = listing.campuspropertynamepair_set.all()
        
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
        listing = Listing.objects.get(id=pk)

        # Go back to confirmation page if editing an unconfirmed list, otherwise return to the review page
        if self.request.user.is_swapt_user and not listing.confirmed:
            return reverse_lazy("listings:confirm")
        if (self.request.user.is_swapt_user and listing.confirmed) or self.request.user.is_admin:
            return reverse_lazy("listings:review")

    def form_valid(self, form):
        listing = form.save()

        # Change stage, either based on admin changing it or automatic changes when swaptuser updates rejected/reported listing
        if self.request.user.is_admin:
            listing.stage = int(form.cleaned_data["stage"])
        elif self.request.user.is_swapt_user and (listing.stage == 3 or listing.stage == 4):
            listing.stage = 1
        listing.save()

        return super().form_valid(form)

class ListingRejectView(UpdateView):
    form_class = ListingRejectForm
    model = Listing
    template_name = 'listings/reject.html'

    def form_valid(self, form):
        listing = form.save()
        listing.save()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("listings:review") + "#nav-review-tab" # Go back to the review tab after rejecting since can only reject from that tab

class ListListings(generics.ListAPIView):
    queryset = Listing.objects.filter(confirmed=True)
    serializer_class = ListingSerializer

    def get_queryset(self):

        # Get attibutes
        locations = self.request.GET.getlist('location')
        campuss = self.request.GET.getlist('campus')
        number = self.request.GET.get('number')

        # Get pairs with campus levels specified, then narrow down listings based on those pairs and other attributes
        pairs = CampusPropertyNamePair.objects.filter(campus__in=campuss)
        queryset = Listing.objects.filter(campuspropertynamepair__in=pairs).distinct()
        queryset = queryset.filter(confirmed=True, stage=2, location__in=locations) # Make sure listings returned in request are approved and confirmed
        queryset = sorted(queryset, key=lambda x: random.random()) # Randomize order as to not give same listings in same order every time to the app
        queryset = queryset[:int(int(number) * .85)] # Only give up to 85% number of listings specified
        queryset = sorted(queryset + sorted(Listing.objects.filter(stage=5), key=lambda x: random.random())[:int(int(number) * .15)], key=lambda x: random.random()) # Other 15% of listings are commMkt listings
       
        return queryset


    def list(self, request, **kwargs):
        # Note the use of `get_queryset()` instead of `self.queryset`
        queryset = self.get_queryset()
        # Passes campus list in so that serializer can randomly pick the propertyname levels to return in the request for the listings
        serializer = ListingSerializer(queryset, many=True, context={'campuss': self.request.GET.getlist('campus')})  
        data = serializer.data

        # This is for the animations in the app to work
        # i = int(self.request.GET.get('number'))
        i = int(request.GET.get('number')) - 1
        for entry in data:
            entry["index"] = i
            i -= 1
        return Response(serializer.data)

class ReportListing(generics.UpdateAPIView):
    queryset = Listing.objects.filter(stage=2, confirmed=True)
    serializer_class = ListingSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return Listing.objects.filter(stage=2, confirmed=True)

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

class UpdatePercentItemsSoldListing(generics.UpdateAPIView):
    queryset = Listing.objects.filter(stage=2, confirmed=True)
    serializer_class = ListingSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        return Listing.objects.filter(stage=2, confirmed=True)

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.get(pk=self.request.GET.get('id'))
        return obj
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)

        instance = self.get_object()
        
        # If itemsSold set to true, increment itemsSold count, otherwise (aka set to false), add incrment itemsUnSold count
        is_itemsSold = self.request.data["itemsSold"]
        if is_itemsSold:
            instance.itemsSold += 1
        else:
            instance.itemsUnSold += 1

        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
        
class ReviewListingsAPI(viewsets.ModelViewSet):
    queryset = Listing.objects.filter(confirmed=True)
    serializer_class = ListingReviewSerializer

    def get_queryset(self):

        # Get attributes from query string
        stage = int(self.request.GET.get('stage'))

        if(stage == 5): 
            return Listing.objects.filter(stage=5)
        
        locations = self.request.GET.getlist('location', ['Columbia, MD', 'ElonNC', 'Burlington, NC', 'College Park MD'])
        propertynames = self.request.GET.getlist('propertyname', ['Oaks', 'Park Place', 'Mill Point'])
        lowCampus = int(self.request.GET.get('lowCampus', 1))
        highCampus = int(self.request.GET.get('highCampus', 12))
        lowItemsSold = float(self.request.GET.get('lowItemsSold', 0.0))
        highItemsSold = float(self.request.GET.get('highItemsSold', 100.0))
        showNA = self.request.GET.get('showNA', 'true')

        # Same filtering as in the regular review view
        pairs = CampusPropertyNamePair.objects.filter(campus__gte=lowCampus, campus__lte=highCampus, propertyname__in=propertynames)
        queryset = Listing.objects.filter(stage=stage, location__in=locations, percent_itemsSold__gte=lowItemsSold, percent_itemsSold__lte=highItemsSold, 
            campuspropertynamepair__in=pairs, confirmed=True).distinct()
        
        if(showNA == "true"):
            queryset = queryset | Listing.objects.filter(stage=stage, location__in=locations, percent_itemsSold=None, 
            campuspropertynamepair__in=pairs, confirmed=True).distinct()
        
        if self.request._request.user.is_swapt_user:
            return queryset.filter(swaptuser=self.request._request.user.swaptuser)
        else:
            return queryset

class Index(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'listings/index.html')


class About(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'listings/about.html')


class Order(View):
    def get(self, request, *args, **kwargs):
        # get every item from each category
        DiningFurnitureSets = Listing.objects.filter(
            categoryV2__name__contains='DiningFurniture')
        BedroomFurnitureSets = Listing.objects.filter(categoryV2__name__contains='BedroomFurniture')
        OutdoorFurnituresSets = Listing.objects.filter(categoryV2__name__contains='OutdoorFurniture')
        LivingRmFurnitureSets = Listing.objects.filter(categoryV2__name__contains='LivingRmFurniture')

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
        name = request.POST.get('name')
        email = request.POST.get('email')
        street = request.POST.get('street')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip')

        order_items = {
            'items': []
        }

        items = request.POST.getlist('items[]')

        for item in items:
            swapt_item = Listing.objects.get(pk__contains=int(item))
            item_data = {
                'id': swapt_item.pk,
                'name': swapt_item.name,
                'price': swapt_item.itemPrice
            }

            order_items['items'].append(item_data)

            price = 0
            item_ids = []

        for item in order_items['items']:
            price += item['price']
            item_ids.append(item['id'])

        order = OrderModel.objects.create(
            price=price,
            name=name,
            email=email,
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

        send_mail(
            'Thank You For Your Order!',
            body,
            'example@example.com',
            [email],
            fail_silently=False
        )

        context = {
            'items': order_items['items'],
            'price': price
        }

        return redirect('listings:swapt_create-confirmation', pk=order.pk)


class OrderConfirmation(View):
    def get(self, request, pk, *args, **kwargs):
        order = OrderModel.objects.get(pk=pk)

        context = {
            'pk': order.pk,
            'items': order.items,
            'price': order.price,
        }

        return render(request, 'listings/swapt-confirmation.html', context)

    def post(self, request, pk, *args, **kwargs):
        data = json.loads(request.body)

        if data['isPaid']:
            order = OrderModel.objects.get(pk=pk)
            order.is_paid = True
            order.save()

        return redirect('listings:payment-confirmation')


class OrderPayConfirmation(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'listings/swapt_pay_confirmation.html')


class Menu(View):
    def get(self, request, *args, **kwargs):
        swapt_items = Listing.objects.all()

        context = {
            'swapt_items': swapt_items
        }

        return render(request, 'listings/cmnty_listings.html', context)


class MenuSearch(View):
    def get(self, request, *args, **kwargs):
        query = self.request.GET.get("q")

        swapt_items = Listing.objects.filter(
            Q(name__icontains=query) |
            Q(itemPrice__icontains=query) |
            Q(desc__icontains=query)
        )

        context = {
            'swapt_items': swapt_items
        }

        return render(request, 'listings/cmnty_listings.html', context)