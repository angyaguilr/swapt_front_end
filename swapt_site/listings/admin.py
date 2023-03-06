from django.contrib import admin
from .models import Color, Size, Brand, Listing, SwaptListing, Banner, Price, ListingTag, Category, SwaptListingModel, Swapt_Bundle_Price, CampusPropertyNamePair,  SwaptCampusPropertyNamePair, ListingAttribute, CmntyListingsCategory

# Registering the models in this app so the admin can view and edit these types of objects
admin.site.register(Listing)
admin.site.register(ListingAttribute)
admin.site.register(SwaptCampusPropertyNamePair)
admin.site.register(CampusPropertyNamePair)
admin.site.register(SwaptListing)
admin.site.register(Banner)
admin.site.register(Brand)
admin.site.register(Color)
admin.site.register(Size)


admin.site.register(Category)
admin.site.register(CmntyListingsCategory)
admin.site.register(SwaptListingModel)

class PriceAdmin(admin.StackedInline):
    model = Price

class ListingAdmin(admin.ModelAdmin):
    inlines = (PriceAdmin,)

    class Meta:
        model = Listing

admin.site.register(ListingTag)
admin.site.register(Price)
admin.site.register(Swapt_Bundle_Price)
#The Price model is registered inline with the Product model so that we can add the prices of a product while creating the product inside the admin panel.