from django.urls import include, path, re_path
from django.contrib.auth.decorators import login_required
from rest_framework import routers

from accounts.decorators import swapt_user_required, Swapt_admin_required
from . import views

# Setting up the reivew flashcards page API
router = routers.DefaultRouter()
router.register(r'review', views.ReviewListingsAPI) 

urlpatterns = [
    #all:
    path('index', views.Index.as_view(), name='index'),
    path('about/', views.About.as_view(), name='about'),
    path("create-checkout-session/<int:pk>/", swapt_user_required()(views.CreateStripeCheckoutSessionView.as_view()),name="create-checkout-session",),
    path('success/', swapt_user_required()(views.SuccessView.as_view()),name='success'),
    path('cancel/', swapt_user_required()(views.CancelView.as_view()),name='cancel'),
    path("webhooks/stripe/", views.StripeWebhookView.as_view(), name="stripe_webhook"), #updated line
    #community listings:
    path("cmnty-listing", views.CmntyListingListView.as_view(), name="cmnty_listing_list"),
    path("cmnty-<int:pk>/", swapt_user_required()(views.CmntyListingDetailView.as_view()), name="cmnty_listing_detail"),
    path('cmnty-Listings/', views.CmntyListingsUploaded.as_view(), name='cmnty_listings'),
    path('cmnty-Listings/search/', views.CmntyListingsUploadedSearch.as_view(), name='cmnty_listings_search'),
    path('cmnty-create-listing/', views.CmntyListingCreationView.as_view(), name="cmnty_create"),
    path('cmnty-create-listing-price/', views.CmntyListingPriceCreationView.as_view(), name="cmnty_create_price"),
    #swapt listings:
    path("swapt-listing", views.SwaptListingListView.as_view(), name="swapt_listing_list"),
    path("swapt-<int:pk>/", swapt_user_required()(views.SwaptListingDetailView.as_view()), name="swapt_listing_detail"),
    path('swapt-Listings/', views.ListingsUploaded.as_view(), name='swapt_listings'),
    path('swapt-Listings/search/', views.ListingsUploadedSearch.as_view(), name='swapt_listings_search'),
    #path('swapt-upload-swapt/', swapt_user_required()(views.ListingsCreationView.as_view()), name="upload_swapt"),
    
    path('swapt-create-listing/', views.SwaptListing.as_view(), name='swapt_create'),
    path('swapt-confirmation/<int:pk>', views.SwaptListingConfirmation.as_view(), name='swapt-confirmation'),
    path('swapt-pay-confirmation/', views.SwaptListingPayConfirmation.as_view(),name='payment-confirmation'),
   
    #tbd
    path('confirm/', swapt_user_required()(views.ListingsConfirmationView.as_view()), name="confirm"),
    path('review/', login_required()(views.ListingsReviewView.as_view()), name="review"),
    path('edit/<int:pk>/', login_required()(views.ListingEditView.as_view()), name="edit"),
    path('reject/<int:pk>/', Swapt_admin_required()(views.ListingRejectView.as_view()), name="reject"),
    path('list/', views.ListListings.as_view(), name="list"),
    re_path('^api/', include(router.urls)),
    #TBD: url('^api/', include(router.urls)),
    path('report/', views.ReportListing.as_view(), name="report"),
    path('update-percent-itemssold/', views.UpdatePercentItemsSoldListing.as_view(), name="update_percent_itemssold"),
    ]