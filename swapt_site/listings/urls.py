from django.urls import include, path, re_path
from django.contrib.auth.decorators import login_required
from rest_framework import routers
from django.conf.urls import include

from django.conf import settings
from django.conf.urls.static import static

from accounts.decorators import swapt_user_required, Swapt_admin_required
from . import views

# Setting up the reivew listings page API
router = routers.DefaultRouter()
router.register(r'review', views.ReviewListingsAPI) 

urlpatterns = [
    #all:
    path('index', views.Index.as_view(), name='index'),
    path('about/', views.About.as_view(), name='about'),
    #community listings:
    path("cmnty-create-checkout-session/<int:pk>/", swapt_user_required()(views.CreateStripeCheckoutSessionView.as_view()),name="create-checkout-session",),
    path('cmnty-success/', swapt_user_required()(views.SuccessView.as_view()),name='cmnty_success'),
    path('cmnty-cancel/', swapt_user_required()(views.CancelView.as_view()),name='cmnty_cancel'),
    path("cmnty-webhooks/stripe/", views.StripeWebhookView.as_view(), name="cmnty_stripe_webhook"), #updated line
    path("cmnty-listing", views.ListingListView.as_view(), name="cmnty_listing_list"),
    path("cmnty-<int:pk>/", swapt_user_required()(views.ListingDetailView.as_view()), name="cmnty_listing_detail"),
    path('cmnty-Listings/', views.Menu.as_view(), name='cmnty_listings'),
    path('cmnty-Listings/search/', views.MenuSearch.as_view(), name='cmnty_listings_search'),
    path('cmnty-create-listing/', swapt_user_required()(views.CommMktListingCreationView.as_view()), name="cmnty_create"),
    #swapt listings:
    path("swapt-create-checkout-session/<int:pk>/", swapt_user_required()(views.CreateStripeCheckoutSessionView.as_view()),name="swapt-create-checkout-session",),
    path('swapt-success/', swapt_user_required()(views.SuccessView.as_view()),name='swapt_success'),
    path('swapt-cancel/', swapt_user_required()(views.CancelView.as_view()),name='swapt_cancel'),
     path("swapt-webhooks/stripe/", views.StripeWebhookView.as_view(), name="swapt_stripe_webhook"), #updated line
    path("swapt-listing", views.ListingListView.as_view(), name="swapt_listing_list"),
    path("swapt-<int:pk>/", swapt_user_required()(views.ListingDetailView.as_view()), name="swapt_listing_detail"),
    path('swapt-Listings/', views.Menu.as_view(), name='swapt_listings'),
    path('swapt-Listings/search/', views.MenuSearch.as_view(), name='swapt_listings_search'),
    path('swapt-upload-swapt/', swapt_user_required()(views.ListingsCreationView.as_view()), name="upload_swapt"),
    path('swapt-create-listing/', views.Order.as_view(), name='swapt_create'),
    path('swapt-confirmation/<int:pk>', views.OrderConfirmation.as_view(), name='swapt-confirmation'),
    path('swapt-pay-confirmation/', views.OrderPayConfirmation.as_view(),name='payment-confirmation'),
   
    #tbd
    path('confirm/', swapt_user_required()(views.ListingsConfirmationView.as_view()), name="confirm"),
    path('review/', login_required()(views.ListingsReviewView.as_view()), name="review"),
    path('edit/<int:pk>/', login_required()(views.ListingEditView.as_view()), name="edit"),
    path('reject/<int:pk>/', Swapt_admin_required()(views.ListingRejectView.as_view()), name="reject"),
    path('list/', views.ListListings.as_view(), name="list"),
    re_path('^api/', include(router.urls)),
    path('report/', views.ReportListing.as_view(), name="report"),
    path('update-percent-itemssold/', views.UpdatePercentItemsSoldListing.as_view(), name="update_percent_itemssold"),
    ]