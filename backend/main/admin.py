from django.contrib import admin
from .models import CmntyCampusPropertyNamePair, Banner,Category,Brand,Color,Dimension,CmntyListing,ProductAttribute,CartOrder,CartOrderItems,ProductReview,Wishlist,UserAddressBook, Swapt_Prices, SwaptCampusPropertyNamePair, SwaptListingModel, SwaptListingTag, SwaptPropertyManager, SwaptListingTransactionRef, SwaptPaymentHistory, CmntyListingTag, CmntyListingPrice

# admin.site.register(Banner)
admin.site.register(Brand)
admin.site.register(Dimension)
#swapt
admin.site.register(Swapt_Prices)
admin.site.register(SwaptListingModel)
admin.site.register(SwaptListingTag)
admin.site.register(SwaptListingTransactionRef)
admin.site.register(SwaptPaymentHistory)
admin.site.register(SwaptCampusPropertyNamePair)
admin.site.register(SwaptPropertyManager)
#community listings
admin.site.register(CmntyListingTag)
admin.site.register(CmntyCampusPropertyNamePair)


class BannerAdmin(admin.ModelAdmin):
	list_display=('alt_text','image_tag')
admin.site.register(Banner,BannerAdmin)

class CategoryAdmin(admin.ModelAdmin):
	list_display=('title','image_tag')
admin.site.register(Category,CategoryAdmin)

class ColorAdmin(admin.ModelAdmin):
	list_display=('title','color_bg')
admin.site.register(Color,ColorAdmin)

class ProductAdmin(admin.ModelAdmin):
    list_display=('id','title','category','brand','status','is_featured')
    list_editable=('status','is_featured')
admin.site.register(CmntyListing,ProductAdmin)

# CmntyListing Attribute
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display=('id','image_tag','product','price','color','size')
admin.site.register(ProductAttribute,ProductAttributeAdmin)

# Order
class CartOrderAdmin(admin.ModelAdmin):
	list_editable=('paid_status','order_status')
	list_display=('user','total_amt','paid_status','order_dt','order_status')
admin.site.register(CartOrder,CartOrderAdmin)

class CartOrderItemsAdmin(admin.ModelAdmin):
	list_display=('invoice_no','item','image_tag','qty','price','total')
admin.site.register(CartOrderItems,CartOrderItemsAdmin)


class ProductReviewAdmin(admin.ModelAdmin):
	list_display=('user','product','review_text','get_review_rating')
admin.site.register(ProductReview,ProductReviewAdmin)


admin.site.register(Wishlist)


class UserAddressBookAdmin(admin.ModelAdmin):
	list_display=('user','address','status')
admin.site.register(UserAddressBook,UserAddressBookAdmin)

class PriceAdmin(admin.StackedInline):
    model = CmntyListingPrice

class ListingAdmin(admin.ModelAdmin):
    inlines = (PriceAdmin,)

    class Meta:
        model = CmntyListing
