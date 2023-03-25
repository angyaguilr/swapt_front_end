from django.db import models
from django.db.models.deletion import CASCADE
from accounts.models import SwaptUser
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.utils.html import mark_safe
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _

User = settings.AUTH_USER_MODEL
def get_image_filename(instance, filename):
    title = instance.title
    slug = slugify(title)
    return f"listings/{slug}-{filename}"

#COMMUNITYLISTINGS
#build a simple listing model. A listing can have tags. In addition, we also want to create a 
# price model so that we can track the changing prices of a listing over time. 
# Banner
class Banner(models.Model):
    img=models.ImageField(upload_to="banner_imgs/")
    alt_text=models.CharField(max_length=300)

    class Meta:
        verbose_name_plural='1. Banners'

    def image_tag(self):
        return mark_safe('<img src="%s" width="100" />' % (self.img.url))


    def __str__(self):
        return self.alt_text

# Category
class CmntyListingsCategory(models.Model):
    name=models.CharField(max_length=100)
    image=models.ImageField(upload_to="cat_imgs/")

    class Meta:
        verbose_name_plural='2. Categories'

    def image_tag(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))

    def __str__(self):
        return self.name
    
# Brand
class Brand(models.Model):
    title=models.CharField(max_length=100)
    image=models.ImageField(upload_to="brand_imgs/")

    class Meta:
        verbose_name_plural='3. Brands'

    def __str__(self):
        return self.title

# Color
class Color(models.Model):
    title=models.CharField(max_length=100)
    color_code=models.CharField(max_length=100)

    class Meta:
        verbose_name_plural='4. Colors'

    def color_bg(self):
        return mark_safe('<div style="width:30px; height:30px; background-color:%s"></div>' % (self.color_code))

    def __str__(self):
        return self.title

# Dimensions
class Dimensions(models.Model):
    title=models.CharField(max_length=100)

    class Meta:
        verbose_name_plural='5. Dimensions'

    def __str__(self):
        return self.title

# CmntyListing Tags
class CmntyListingTag(models.Model):
    name = models.CharField(
        max_length=100, help_text=_("Designates the name of the tag.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name
    
class CmntyListingManager(models.Manager):
    # Only shows the user rejected listings within last 30 days or listings from other stages
    # This is so that when listings are >= 30 days old, but daily cleansing hasn't run yet,
    # user still can't see those listings
    def get_queryset(self):
        return super().get_queryset().filter(
            publishing_date__gte=timezone.now()-timezone.timedelta(days=30), stage=3
        ) | super().get_queryset().filter(
            stage__in=[1,2,4,5]
        )

class CmntyListing(models.Model):
    PICKUP_CHOICES = [
        (1, 'Public Pickup'),
        (2, 'Door Pickup'),
    ]
    APPROVAL_STAGES = [
        (1, 'Under Review'),
        (2, 'Approved'),
        (3, 'Rejected'),
        (4, 'Reported'),
        (5, 'Closed'),
    ]
    SELLING_STAGES = [
        (1, 'Available'),
        (2, 'Pending'),
        (3, 'Sold'),
    ]
    CATEGORY_CHOICES = [
        ('Bedroom Furniture', 'Bedroom Furniture'),
        ('Dining Room Furniture', 'Dining Room Furniture'),
        ('Living Room Furniture', 'Living Room Furniture'),
        ('Office Furniture', 'Office Furniture'),
        ('Bathroom Furniture', 'Bathroom Furniture'),
        ('Outdoor Furniture', 'Outdoor Furniture'),
        ('Other Furniture', 'Other Furniture'),
    ]
    CONDITION_CHOICES = [
        (1, 'New'),
        (2, 'Used - Like New'),
        (3, 'Used - Decent'),
        (4, 'Used - Fair'),
    ]
    DELIVERYMETHOD_CHOICES = [
        (1, 'Local Pickup'),
        (2, 'Swapt Delivery'),
    ]
    COLOR_CHOICES = [
        ('Beige', 'Beige'),
        ('Black', 'Black'),
        ('Blue', 'Blue'),
        ('Brown', 'Brown'),
        ('Clear', 'Clear'),
        ('Gold', 'Gold'),
        ('Gray', 'Gray'),
        ('Green', 'Green'),
        ('Multicolor', 'Multicolor'),
        ('Orange', 'Orange'),
        ('Pink', 'Pink'),
        ('Purple', 'Purple'),
        ('Red', 'Red'),
        ('Silver', 'Silver'),
        ('White', 'White'),
        ('Yellow', 'Yellow'),
        ('Wood', 'Wood'),
    ]
    LOCATION_CHOICES = [
        ('ElonNC', 'ElonNC'),
        ('BurlingtonNC', 'BurlingtonNC'),
    ]
    #field identifying seller who posted listing
    swaptuser = models.ForeignKey(SwaptUser, on_delete=CASCADE, null=True)
    #mandatory fields required with user input
    title = models.CharField(max_length=250, null=True)
    desc = models.TextField(_("desc"), blank=True)
    thumbnail = models.ImageField(upload_to=get_image_filename, blank=True)
    preloaded_category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        null=True
    )
    condition = models.PositiveSmallIntegerField(choices=CONDITION_CHOICES , null=True)
    category = models.ForeignKey(CmntyListingsCategory,on_delete=models.CASCADE, related_name='item')
    #mandatory location details
    location = models.CharField(
        max_length=30,
        choices=LOCATION_CHOICES,
        null=True
    )
    delivery = models.PositiveSmallIntegerField(choices=DELIVERYMETHOD_CHOICES, null=True)
    pickupmethod = models.PositiveSmallIntegerField(choices= PICKUP_CHOICES, null=True)
    #fields used to review listings
    stage = models.PositiveSmallIntegerField(choices=APPROVAL_STAGES, null=True)
    selling_stage = models.PositiveSmallIntegerField(choices=SELLING_STAGES, null=True)
    confirmed = models.BooleanField(default=False)
    issue = models.CharField(max_length=250, blank=True, null=True) # Currently only using one field for both rejected and reported issues
    #optional
    quantity = models.IntegerField(default=1, null=True)
    tags = models.ManyToManyField(CmntyListingTag, blank=True)
    
    #field to display listings in featured page 
    is_featured=models.BooleanField(default=False)

    #date/time fields
    publishing_date = models.DateTimeField(
        default=timezone.now,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
  
    objects = CmntyListingManager() # Using manager above for reasons in comment

    # def __str__(self):
    #     return self.name
    def save(self, *args, **kwargs):
        super(CmntyListing, self).save(*args, **kwargs) 

class CmntyCampusPropertyNamePair(models.Model):
    listings = models.ManyToManyField('CmntyListing')
    CAMPUS_CHOICES = [
        ('Elon', 'Elon'),
        ('UMD', 'UMD'),
        ('UNCG', 'UNCG')
    ]
    PROPERTYNAME_CHOICES = [
        ('Oaks', 'Oaks'),
        ('MillPoint', 'MillPoint'),
        ('OakHill', 'OakHill'),
    ]
    campus = models.CharField(
        max_length=30,
        choices=CAMPUS_CHOICES,
        default='Elon'
    )
    propertyname = models.CharField(
        max_length=30,
        choices=PROPERTYNAME_CHOICES,
    )
    confirmed = models.BooleanField(default=False)  

# CmntyListing Attribute
class CmntyListingAttribute(models.Model):
    listing=models.ForeignKey(CmntyListing,on_delete=models.CASCADE)
    color=models.ForeignKey(Color,on_delete=models.CASCADE)
    brand=models.ForeignKey(Brand,on_delete=models.CASCADE)
    dimensions=models.ForeignKey(Dimensions,on_delete=models.CASCADE)
    class Meta:
        verbose_name_plural='7. ListingAttributes'

    def __str__(self):
        return self.listing.title

    def image_tag(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))

class CmntyListingPrice(models.Model):
    listing = models.ForeignKey(CmntyListing, on_delete=models.CASCADE)
    price = models.DecimalField(decimal_places=2, max_digits=10)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.listing.title} {self.price}"  

#SWAPTLISTINGS
class SwaptListingTag(models.Model):
    name = models.CharField(
        max_length=100, help_text=_("Designates the name of the tag.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name
class SwaptPropertyManager(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique= True)
    propertyname = models.CharField(max_length=30)

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)

#save customer order for future reference #TBD
class SwaptListingTransactionRef(models.Model):
    email = models.EmailField(max_length=254)
    paid = models.BooleanField(default="False")
    amount = models.IntegerField(default=0)
    description = models.CharField(default=None,max_length=800)
    def __str__(self):
        return self.email 

class SwaptPaymentHistory(models.Model):
    PENDING = "P"
    COMPLETED = "C"
    FAILED = "F"

    STATUS_CHOICES = (
        (PENDING, _("pending")),
        (COMPLETED, _("completed")),
        (FAILED, _("failed")),
    )

    email = models.EmailField(unique=True)
    listing = models.ForeignKey(CmntyListing, on_delete=models.CASCADE)
    payment_status = models.CharField(
        max_length=1, choices=STATUS_CHOICES, default=PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.listing.title
    
class SwaptListingManager(models.Manager):
    # Only shows the user rejected listings within last 30 days or listings from other stages
    # This is so that when listings are >= 30 days old, but daily cleansing hasn't run yet,
    # user still can't see those listings
    def get_queryset(self):
        return super().get_queryset().filter(
            publishing_date__gte=timezone.now()-timezone.timedelta(days=30), stage=3
        ) | super().get_queryset().filter(
            stage__in=[1,2,4,5]
        )
class SwaptListingModel(models.Model):
    APPROVAL_STAGES = [
        (1, 'Under Review'),
        (2, 'Approved'),
        (3, 'Rejected'),
        (4, 'Reported'),
        (5, 'Closed'),
    ]
    SELLING_STAGES = [
        (1, 'Available'),
        (2, 'Pending'),
        (3, 'Sold'),
    ]
    CATEGORY_CHOICES = [
        ('Bedroom Furniture', 'Bedroom Furniture'),
        ('Dining Room Furniture', 'Dining Room Furniture'),
        ('Living Room Furniture', 'Living Room Furniture'),
        ('Office Furniture', 'Office Furniture'),
        ('Bathroom Furniture', 'Bathroom Furniture'),
        ('Outdoor Furniture', 'Outdoor Furniture'),
        ('Other Furniture', 'Other Furniture'),
    ]
    CONDITION_CHOICES = [
        (1, 'New'),
        (2, 'Used - Like New'),
        (3, 'Used - Decent'),
        (4, 'Used - Fair'),
    ]
    DELIVERYMETHOD_CHOICES = [
        (1, 'Local Pickup'),
        (2, 'Swapt Delivery'),
    ]
    COLOR_CHOICES = [
        ('Beige', 'Beige'),
        ('Black', 'Black'),
        ('Blue', 'Blue'),
        ('Brown', 'Brown'),
        ('Clear', 'Clear'),
        ('Gold', 'Gold'),
        ('Gray', 'Gray'),
        ('Green', 'Green'),
        ('Multicolor', 'Multicolor'),
        ('Orange', 'Orange'),
        ('Pink', 'Pink'),
        ('Purple', 'Purple'),
        ('Red', 'Red'),
        ('Silver', 'Silver'),
        ('White', 'White'),
        ('Yellow', 'Yellow'),
        ('Wood', 'Wood'),
    ]
    LOCATION_CHOICES = [
        ('ElonNC', 'ElonNC'),
        ('BurlingtonNC', 'BurlingtonNC'),
    ]
    #unique fields for swaptlistingsmodel
    propertymanager = models.ForeignKey(SwaptPropertyManager, on_delete=models.CASCADE )
    #field identifying seller who posted listing
    swaptuser = models.ForeignKey(SwaptUser, on_delete=CASCADE, null=True)
    
    #mandatory fields required with user input
    title = models.CharField(max_length=250)
    desc = models.TextField(_("desc"), blank=True)
    thumbnail = models.ImageField(upload_to=get_image_filename, blank=True)
    preloaded_category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        null=True
    )
    condition = models.PositiveSmallIntegerField(choices=CONDITION_CHOICES , null=True)
    #mandatory location details
    location = models.CharField(
        max_length=30,
        choices=LOCATION_CHOICES,
        null=True
    )
    delivery = models.PositiveSmallIntegerField(choices=DELIVERYMETHOD_CHOICES, null=True)
    
    #fields used to review listings
    stage = models.PositiveSmallIntegerField(choices=APPROVAL_STAGES, null=True)
    selling_stage = models.PositiveSmallIntegerField(choices=SELLING_STAGES, null=True)
    confirmed = models.BooleanField(default=False)
    issue = models.CharField(max_length=250, blank=True, null=True) # Currently only using one field for both rejected and reported issues
    #optional
    quantity = models.IntegerField(default=1)
    tags = models.ManyToManyField(SwaptListingTag, blank=True)
    
    #field to display listings in featured page 
    is_featured=models.BooleanField(default=False)

    #date/time fields
    publishing_date = models.DateTimeField(
        default=timezone.now,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
  
    objects = CmntyListingManager() # Using manager above for reasons in comment

    # def __str__(self):
    #     return self.name
    def save(self, *args, **kwargs):
        super(SwaptListingModel, self).save(*args, **kwargs) 

class Swapt_Prices(models.Model):
    swapt_bundle_listing = models.ForeignKey(SwaptListingModel, on_delete=models.CASCADE)
    price = models.DecimalField(decimal_places=2, max_digits=10)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.swapt_bundle_listing.title} {self.price}" 

class SwaptCampusPropertyNamePair(models.Model):
    listings = models.ManyToManyField('SwaptListingModel')
    CAMPUS_CHOICES = [
        ('Elon', 'Elon'),
        ('UMD', 'UMD'),
        ('UNCG', 'UNCG')
    ]
    PROPERTYNAME_CHOICES = [
        ('Oaks', 'Oaks'),
        ('MillPoint', 'MillPoint'),
        ('OakHill', 'OakHill'),
    ]
    campus = models.CharField(
        max_length=30,
        choices=CAMPUS_CHOICES,
        default='Elon'
    )
    propertyname = models.CharField(
        max_length=30,
        choices=PROPERTYNAME_CHOICES,
    )
    confirmed = models.BooleanField(default=False)  
            