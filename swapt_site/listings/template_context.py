from .models import CmntyListing, CmntyListingAttribute, CmntyListingPrice
from django.db.models import Min,Max
def get_filters(request):
	cats=CmntyListing.objects.distinct().values('category__name','category__id')
	brands=CmntyListingAttribute.objects.distinct().values('brand__title','brand__id')
	colors=CmntyListingAttribute.objects.distinct().values('color__title','color__id','color__color_code')
	alldimensions=CmntyListingAttribute.objects.distinct().values('dimensions__title','dimensions__id')
	#minMaxPrice=CmntyListingPrice.objects.aggregate(Min('price'),Max('price'))
	data={
		'cats':cats,
		'brands':brands,
		'colors':colors,
		'alldimensions':alldimensions,
		#'minMaxPrice':minMaxPrice,
	}
	return data