from django.contrib import admin
from .models import Banner, CmntyListingsCategory, Brand, Color, Dimensions, CmntyListingPrice, CmntyListingTag, CmntyListing, CmntyCampusPropertyNamePair, CmntyListingAttribute, Swapt_Prices, SwaptCampusPropertyNamePair, SwaptListingModel, SwaptListingTag, SwaptPropertyManager, SwaptPaymentHistory, SwaptListingTransactionRef

# Registering the models in this app so the admin can view and edit these types of objects
admin.site.register(Banner)
admin.site.register(Brand)
admin.site.register(Color)
admin.site.register(Dimensions)
admin.site.register(CmntyListing)
admin.site.register(CmntyListingAttribute)
admin.site.register(CmntyListingPrice)
admin.site.register(CmntyListingTag)

admin.site.register(CmntyListingsCategory)
admin.site.register(CmntyCampusPropertyNamePair)
admin.site.register(SwaptPropertyManager)
admin.site.register(SwaptListingTag)
admin.site.register(SwaptListingModel)

admin.site.register(Swapt_Prices)
admin.site.register(SwaptCampusPropertyNamePair)
admin.site.register(SwaptPaymentHistory)
admin.site.register(SwaptListingTransactionRef)


class PriceAdmin(admin.StackedInline):
    model = CmntyListingPrice

class ListingAdmin(admin.ModelAdmin):
    inlines = (PriceAdmin,)

    class Meta:
        model = CmntyListing

#The CmntyListingPrice model is registered inline with the Product model so that we can add the prices of a product while creating the product inside the admin panel.