from rest_framework import serializers 
from .models import Listing, CampusPropertyNamePair
import random
 

class CampusPropertyNamePairSerializer(serializers.ModelSerializer):

    class Meta:
        model = CampusPropertyNamePair
        fields = ('campus',
                  'propertyname',
                  )
 
class ListingSerializer(serializers.ModelSerializer):
    
    # Added fields up here to specify attributes (read_only or write_only)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    location = serializers.CharField(read_only=True)
    propertyname = serializers.SerializerMethodField(read_only=True)
    stage = serializers.IntegerField(write_only=True)
    issue = serializers.CharField(write_only=True)
    
    class Meta:
        model = Listing
        fields = ('id',
                  'title',
                  'description',
                  'location',
                  'propertyname',
                  'stage',
                  'issue'
                  )
        depth=1
      
    # Randomly selects a propertyname level to return in the API request based on campus levels
    # requested and campus levels that are in a campus/propertyname pair of the listing
    def get_propertyname(self, obj):
        if(obj.stage == 5): 
            return "CommMkt"
            
        campuss = self.context.get("campuss")

        if campuss == None:
            return "N/A"

        # Narrow down from campuss requested to campuss actually in the listing's campus/propertyname pairs
        campuss = obj.campuspropertynamepair_set.filter(campus__in=campuss).values("campus")

        if campuss != None:
            campus = random.choice(campuss)["campus"]
        else:
            return "N/A"

        propertyname = obj.campuspropertynamepair_set.get(campus=campus).propertyname
        
        # Returns in this format because this is how the propertyname is displayed in the game
        if propertyname == "Oaks":
            return "+1" 
        elif propertyname == "ParkPlace": 
            return "+2"
        else:
            return "+3"

# Used only for the review page datatables
class ListingReviewSerializer(serializers.ModelSerializer):

    percent_itemsSold = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Listing
        fields = ('title',
                  'description',
                  'location',
                  'percent_itemsSold',
                  'id',
                  'campuspropertynamepair_set',
                  'issue'
                  )
        depth=1 # Allows user to see campus and propertyname pairs from the set

        datatables_always_serialize = ('id')

    def get_percent_itemsSold(self, obj):
        percent_itemsSold = obj.percent_itemsSold
        # Returns N/A instead of blank for aesthetic purposes
        if(percent_itemsSold == None):
            return "N/A" 
        else:
            return percent_itemsSold