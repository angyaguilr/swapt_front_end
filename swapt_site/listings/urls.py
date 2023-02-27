from django.urls import include, path, re_path
from django.contrib.auth.decorators import login_required
from rest_framework import routers

from accounts.decorators import swapt_user_required, Swapt_admin_required
from . import views

# Setting up the reivew flashcards page API
router = routers.DefaultRouter()
router.register(r'review', views.SwaptReviewListingsAPI)
router.register(r'cmnty_listings_review', views.CmntyReviewListingsAPI) 

urlpatterns = [
    #all:
    path('index', views.Index.as_view(), name='index'),
    path('about/', views.About.as_view(), name='about'),
    path("create-checkout-session/<int:pk>/", swapt_user_required()(views.CreateStripeCheckoutSessionView.as_view()),name="create-checkout-session",),
    path('success/', swapt_user_required()(views.SuccessView.as_view()),name='success'),
    path('cancel/', swapt_user_required()(views.CancelView.as_view()),name='cancel'),
    path("webhooks/stripe/", views.StripeWebhookView.as_view(), name="stripe_webhook"), #updated line
    #community listings:
    path('cmnty-create-listing/', views.CmntyListingCreationView.as_view(), name="cmnty_create"),
    path('cmnty-create-listing-price/', views.CmntyListingPriceCreationView.as_view(), name="cmnty_create_price"),
    path('cmnty-confirm/', swapt_user_required()(views.CmntyListingsConfirmationView.as_view()), name="cmnty_confirm"),
    path('cmnty-review/', login_required()(views.CmntyListingsReviewView.as_view()), name="cmnty_review"),
    path('cmnty-edit/<int:pk>/', login_required()(views.CmntyListingEditView.as_view()), name="cmnty_edit"),
    path('cmnty-reject/<int:pk>/', Swapt_admin_required()(views.CmntyListingRejectView.as_view()), name="cmnty_reject"),
    path('cmnty-list/', views.CmntyListingListAPIView.as_view(), name="cmnty_list"),
    re_path('^api/', include(router.urls)),
    path('cmnty-report/', views.CmntyReportListingView.as_view(), name="cmnty_report"),
    path('cmnty-update-percent-itemssold/', views.CmntyUpdatePercentItemsSoldListingView.as_view(), name="cmnty_update_percent_itemssold"),
    path('cmnty-Listings/', views.CmntyListingsUploaded.as_view(), name='cmnty_listings'),
    path('cmnty-Listings/search/', views.CmntyListingsUploadedSearch.as_view(), name='cmnty_listings_search'),
    path("cmnty-listing", views.CmntyListingListView.as_view(), name="cmnty_listing_list"),
    path("cmnty-<int:pk>/", swapt_user_required()(views.CmntyListingDetailView.as_view()), name="cmnty_listing_detail"),

    #swapt listings:
    path('swapt-confirm/', swapt_user_required()(views.SwaptListingsConfirmationView.as_view()), name="swapt_confirm"),
    path('swapt-review/', login_required()(views.SwaptListingsReviewView.as_view()), name="swapt_review"),
    path('swapt-edit/<int:pk>/', login_required()(views.SwaptListingEditView.as_view()), name="swapt_edit"),
    path('swapt-reject/<int:pk>/', Swapt_admin_required()(views.SwaptListingRejectView.as_view()), name="swapt_reject"),
    path('swapt-list/', views.SwaptListingListAPIView.as_view(), name="swapt_list"),
    re_path('^api/', include(router.urls)),
    #TBD: url('^api/', include(router.urls)),
    path('swapt-report/', views.SwaptReportListingView.as_view(), name="swapt_report"),
    path('swapt-update-percent-itemssold/', views.SwaptUpdatePercentItemsSoldListingView.as_view(), name="swapt_update_percent_itemssold"),
    path('swapt-Listings/', views.SwaptListingsUploaded.as_view(), name='swapt_listings'),
    path('swapt-Listings/search/', views.SwaptListingsUploadedSearch.as_view(), name='swapt_listings_search'),
    path('swapt-create-listing/', views.SwaptListingCreation.as_view(), name='swapt_create'),
    path("swapt-listing", views.SwaptListingListView.as_view(), name="swapt_listing_list"),
    path("swapt-<int:pk>/", swapt_user_required()(views.SwaptListingDetailView.as_view()), name="swapt_listing_detail"),
    path('swapt-confirmation/<int:pk>', views.SwaptListingConfirmation.as_view(), name='swapt_confirmation'),
    path('swapt-pay-confirmation/', views.SwaptListingPayConfirmation.as_view(),name='payment-confirmation'),
    ]