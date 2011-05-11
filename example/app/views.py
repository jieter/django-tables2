from django.shortcuts import render_to_response
from django.template import RequestContext
from .tables import CountryTable, ThemedCountryTable
from .models import Country


def home(request):
    order_by = request.GET.get('sort')
    queryset = Country.objects.all()
    #
    example1 = CountryTable(queryset, order_by=order_by)
    #
    example2 = CountryTable(queryset, order_by=order_by)
    example2.paginate(page=request.GET.get('page', 1), per_page=3)
    #
    example3 = ThemedCountryTable(queryset, order_by=order_by)
    #
    example4 = ThemedCountryTable(queryset, order_by=order_by)
    example4.paginate(page=request.GET.get('page', 1), per_page=3)

    return render_to_response('example.html', {
        'example1': example1,
        'example2': example2,
        'example3': example3,
        'example4': example4,
    }, context_instance=RequestContext(request))
