from .models import Listing, ListingAttribute
from django.db.models import Min,Max
def get_filters(request):
	cats=Listing.objects.distinct().values('categoryV3__title','categoryV3__id')
	brands=Listing.objects.distinct().values('brand__title','brand__id')
	colors=ListingAttribute.objects.distinct().values('color__title','color__id','color__color_code')
	sizes=ListingAttribute.objects.distinct().values('size__title','size__id')
	minMaxPrice=ListingAttribute.objects.aggregate(Min('price'),Max('price'))
	data={
		'cats':cats,
		'brands':brands,
		'colors':colors,
		'sizes':sizes,
		'minMaxPrice':minMaxPrice,
	}
	return data