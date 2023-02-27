from django.db import models
from django.db.models.deletion import CASCADE
from accounts.models import SwaptUser
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _

UserPending = settings.AUTH_USER_MODEL
#build a simple product model. A product can have tags. In addition, we also want to create a 
# price model so that we can track the changing prices of a product over time. Go to the models.py 
# file of the products app and add the following code:
def get_image_filename(instance, filename):
    name = instance.name
    slug = slugify(name)
    return f"listings/{slug}-{filename}"

class ListingTag(models.Model):
    name = models.CharField(
        max_length=100, help_text=_("Designates the name of the tag.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name

# class Product(models.Model):
#     name = models.CharField(max_length=200)
#     tags = models.ManyToManyField(ProductTag, blank=True)
#     desc = models.TextField(_("Description"), blank=True)
#     thumbnail = models.ImageField(upload_to=get_image_filename, blank=True)
#     url = models.URLField()
#     quantity = models.IntegerField(default=1)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ("-created_at",)

#     def __str__(self):
#         return self.name

class ListingManager(models.Manager):
    # Only shows the user rejected listings within last 30 days or listings from other stages
    # This is so that when listings are >= 30 days old, but daily cleansing hasn't run yet,
    # user still can't see those listings
    def get_queryset(self):
        return super().get_queryset().filter(
            publishing_date__gte=timezone.now()-timezone.timedelta(days=30), stage=3
        ) | super().get_queryset().filter(
            stage__in=[1,2,4,5]
        )

class Listing(models.Model):
    APPROVAL_STAGES = [
        (1, 'Under Review'),
        (2, 'Approved'),
        (3, 'Rejected'),
        (4, 'Reported'),
        (5, 'Community'),

    ]
    SELLING_STAGES = [
        (1, 'Available'),
        (2, 'Pending'),
        (3, 'Sold'),
    ]
    CATEGORY_CHOICES = [
        ('Bedroom Furniture', 'Bedroom Furniture'),
        ( 'Dining Room Furniture', 'Dining Room Furniture'),
        ( 'Living Room Furniture', 'Living Room Furniture'),
        ('Office Furniture', 'Office Furniture'),
        ('Outdoor Furniture', 'Outdoor Furniture'),
        ('Other Furniture', 'Other Furniture'),

    ]
    CONDITION_CHOICES = [
        (1, 'New'),
        (2, 'Used - Like New'),
        (3, 'Used - Good'),
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
    ]
    LOCATION_CHOICES = [
        ('ElonNC', 'ElonNC'),
        ('CollegeParkMD', 'CollegeParkMD'),
        ('BurlingtonNC', 'BurlingtonNC'),
        ('ColumbiaMD', 'ColumbiaMD')
    ]
    name = models.CharField(max_length=200, default='any_name')
    tags = models.ManyToManyField(ListingTag, blank=True)
    desc = models.TextField(_("Description"), blank=True)
    thumbnail = models.ImageField(upload_to=get_image_filename, blank=True)
    url = models.URLField()
    quantity = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
    title = models.CharField(max_length=250)
    description = models.CharField(max_length=250, null=True)
    color = models.CharField(
        max_length=30,
        choices= COLOR_CHOICES,
        null=True
    )
    location = models.CharField(
        max_length=30,
        choices=LOCATION_CHOICES,
        null=True
    )
    delivery = models.PositiveSmallIntegerField(choices=DELIVERYMETHOD_CHOICES, null=True)
    stage = models.PositiveSmallIntegerField(choices=APPROVAL_STAGES, null=True)
    selling_stage = models.PositiveSmallIntegerField(choices=SELLING_STAGES, null=True)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        null=True
    )
    categoryV2 = models.ManyToManyField('Category', related_name='item')
    condition = models.PositiveSmallIntegerField(choices=CONDITION_CHOICES , null=True)
    confirmed = models.BooleanField(default=False)
    swaptuser = models.ForeignKey(SwaptUser, on_delete=CASCADE, null=True)
    issue = models.CharField(max_length=250, blank=True, null=True) # Currently only using one field for both rejected and reported issues
    itemsSold = models.IntegerField(default=0)
    itemsUnSold = models.IntegerField(default=0)
    percent_itemsSold = models.DecimalField(default=None, blank=True, null=True, max_digits=5, decimal_places=2) # Max digits 5 instead of 4 because
    itemPrice = models.DecimalField(decimal_places=2, max_digits=10, default=0.00) # Max digits 5 instead of 4 because
    cover = models.ImageField(upload_to='images/')
    
    publishing_date = models.DateTimeField(
        default=timezone.now,
        blank=True,
    )
    objects = ListingManager() # Using manager above for reasons in comment

    # Updates percent_itemsSold field on save
    # def __str__(self):
    #     return self.name
    def save(self, *args, **kwargs):
        if(not (self.itemsSold == 0 and self.itemsUnSold == 0)):
            self.percent_itemsSold = round(100 * self.itemsSold/(self.itemsSold + self.itemsUnSold), 2)
        super(Listing, self).save(*args, **kwargs) # Call the "real" save() method.

class Price(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    price = models.DecimalField(decimal_places=2, max_digits=10)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.listing.name} {self.price}"  

#save customer order for future reference #TBD
class SwaptListing(models.Model):
    email = models.EmailField(max_length=254)
    paid = models.BooleanField(default="False")
    amount = models.IntegerField(default=0)
    description = models.CharField(default=None,max_length=800)
    def __str__(self):
        return self.email

class CampusPropertyNamePair(models.Model):
    listings = models.ManyToManyField('Listing')
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

class PaymentHistory(models.Model):
    PENDING = "P"
    COMPLETED = "C"
    FAILED = "F"

    STATUS_CHOICES = (
        (PENDING, _("pending")),
        (COMPLETED, _("completed")),
        (FAILED, _("failed")),
    )

    email = models.EmailField(unique=True)
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    payment_status = models.CharField(
        max_length=1, choices=STATUS_CHOICES, default=PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.listing.name

# class MenuItem(models.Model):
#     name = models.CharField(max_length=100)
#     description = models.TextField()
#     image = models.ImageField(upload_to='menu_images/')
#     price = models.DecimalField(max_digits=5, decimal_places=2)
#     category = models.ManyToManyField('Category', related_name='item')

#     def __str__(self):
#         return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class SwaptListingModel(models.Model):
    APPROVAL_STAGES = [
        (1, 'Under Review'),
        (2, 'Approved'),
        (3, 'Rejected'),
        (4, 'Reported'),
        (5, 'Community'),

    ]
    SELLING_STAGES = [
        (1, 'Available'),
        (2, 'Pending'),
        (3, 'Sold'),
    ]
    CATEGORY_CHOICES = [
        ('Bedroom Furniture', 'Bedroom Furniture'),
        ( 'Dining Room Furniture', 'Dining Room Furniture'),
        ( 'Living Room Furniture', 'Living Room Furniture'),
        ('Office Furniture', 'Office Furniture'),
        ('Outdoor Furniture', 'Outdoor Furniture'),
        ('Other Furniture', 'Other Furniture'),

    ]
    CONDITION_CHOICES = [
        (1, 'New'),
        (2, 'Used - Like New'),
        (3, 'Used - Good'),
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
    ]
    LOCATION_CHOICES = [
        ('ElonNC', 'ElonNC'),
        ('CollegeParkMD', 'CollegeParkMD'),
        ('BurlingtonNC', 'BurlingtonNC'),
        ('ColumbiaMD', 'ColumbiaMD')
    ]
    listings = models.ManyToManyField(
        'Listing', related_name='order', blank=True)
    name = models.CharField(max_length=200, default='any_name')
    tags = models.ManyToManyField(ListingTag, blank=True)
    desc = models.TextField(_("Description"), blank=True)
    thumbnail = models.ImageField(upload_to=get_image_filename, blank=True)
    url = models.URLField(default='anyurl.com')
    quantity = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
    title = models.CharField(max_length=250, default='any_name')
    description = models.CharField(max_length=250, null=True)
    color = models.CharField(
        max_length=30,
        choices= COLOR_CHOICES,
        null=True
    )
    location = models.CharField(
        max_length=30,
        choices=LOCATION_CHOICES,
        null=True
    )
    delivery = models.PositiveSmallIntegerField(choices=DELIVERYMETHOD_CHOICES, null=True)
    stage = models.PositiveSmallIntegerField(choices=APPROVAL_STAGES, null=True)
    selling_stage = models.PositiveSmallIntegerField(choices=SELLING_STAGES, null=True)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        null=True
    )
    categoryV2 = models.ManyToManyField('Category', related_name='swapt_item')
    condition = models.PositiveSmallIntegerField(choices=CONDITION_CHOICES , null=True)
    confirmed = models.BooleanField(default=False)
    swaptuser = models.ForeignKey(SwaptUser, on_delete=CASCADE, null=True)
    issue = models.CharField(max_length=250, blank=True, null=True) # Currently only using one field for both rejected and reported issues
    itemsSold = models.IntegerField(default=0)
    itemsUnSold = models.IntegerField(default=0)
    percent_itemsSold = models.DecimalField(default=None, blank=True, null=True, max_digits=5, decimal_places=2) # Max digits 5 instead of 4 because
    itemPrice = models.DecimalField(decimal_places=2, max_digits=10, default=0.00) # Max digits 5 instead of 4 because
    
    
    publishing_date = models.DateTimeField(
        default=timezone.now,
        blank=True,
    )
    objects = ListingManager() # Using manager above for reasons in comment

    # Updates percent_itemsSold field on save
    # def __str__(self):
    #     return self.name
    def save(self, *args, **kwargs):
        if(not (self.itemsSold == 0 and self.itemsUnSold == 0)):
            self.percent_itemsSold = round(100 * self.itemsSold/(self.itemsSold + self.itemsUnSold), 2)
        super(SwaptListingModel, self).save(*args, **kwargs) # Call the "real" save() method.


class Swapt_Bundle_Price(models.Model):
    swapt_bundle_listing = models.ForeignKey(SwaptListingModel, on_delete=models.CASCADE)
    price = models.DecimalField(decimal_places=2, max_digits=10)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.swapt_bundle_listing.name} {self.price}" 


class GradeDifficultyPair(models.Model):
    listings = models.ManyToManyField('SwaptListingModel')


    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]

    grade = models.IntegerField()
    difficulty = models.CharField(
        max_length=15,
        choices=DIFFICULTY_CHOICES,
    )
    confirmed = models.BooleanField(default=False)     