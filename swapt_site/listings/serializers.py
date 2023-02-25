from rest_framework import serializers 
from .models import Listing, GradeDifficultyPair
import random
 

class GradeDifficultyPairSerializer(serializers.ModelSerializer):

    class Meta:
        model = GradeDifficultyPair
        fields = ('grade',
                  'difficulty',
                  )
 
class ListingSerializer(serializers.ModelSerializer):
    
    # Added fields up here to specify attributes (read_only or write_only)
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    location = serializers.CharField(read_only=True)
    difficulty = serializers.SerializerMethodField(read_only=True)
    stage = serializers.IntegerField(write_only=True)
    issue = serializers.CharField(write_only=True)
    
    class Meta:
        model = Listing
        fields = ('id',
                  'name',
                  'tags',
                  'desc',
                  'thumbnail',
                  'url',
                  'quantity',
                  'title',
                  'description',
                  'color',
                  'delivery',
                  'category',
                  'categoryV2',
                  'condition',
                  'cover',
                  'itemPrice',
                  'percent_itemsSold',
                  'itemsUnSold',
                  'itemsSold',
                  'location',
                  'difficulty',
                  'stage',
                  'issue'
                  )
        depth=1
      
    # Randomly selects a difficulty level to return in the API request based on grade levels
    # requested and grade levels that are in a grade/difficulty pair of the card
    def get_difficulty(self, obj):
        if(obj.stage == 5): 
            return "CommMkt"
            
        grades = self.context.get("grades")

        if grades == None:
            return "N/A"

        # Narrow down from grades requested to grades actually in the card's grade/difficulty pairs
        grades = obj.gradedifficultypair_set.filter(grade__in=grades).values("grade")

        if grades != None:
            grade = random.choice(grades)["grade"]
        else:
            return "N/A"

        difficulty = obj.gradedifficultypair_set.get(grade=grade).difficulty
        
        # Returns in this format because this is how the difficulty is displayed in the game
        if difficulty == "Easy":
            return "+1" 
        elif difficulty == "Medium": 
            return "+2"
        else:
            return "+3"

# Used only for the review page datatables
class ListingReviewSerializer(serializers.ModelSerializer):

    percent_itemsSold = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Listing
        fields = ('name',
                  'description',
                  'location',
                  'percent_itemsSold',
                  'id',
                  'gradedifficultypair_set',
                  'issue'
                  )
        depth=1 # Allows user to see grade and difficulty pairs from the set

        datatables_always_serialize = ('id')

    def get_percent_itemsSold(self, obj):
        percent_itemsSold = obj.percent_itemsSold
        # Returns N/A instead of blank for aesthetic purposes
        if(percent_itemsSold == None):
            return "N/A" 
        else:
            return percent_itemsSold