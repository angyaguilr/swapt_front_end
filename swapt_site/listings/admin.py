from django.contrib import admin
from .models import Listing, GradeDifficultyPair, SwaptListing, Price, ListingTag, Category, SwaptListingModel, Swapt_Bundle_Price

# Registering the models in this app so the admin can view and edit these types of objects
admin.site.register(Listing)
admin.site.register(GradeDifficultyPair)
admin.site.register(SwaptListing)


admin.site.register(Category)
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