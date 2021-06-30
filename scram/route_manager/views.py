from django.shortcuts import render

from .models import ActionType, Entry


def home_page(request, prefilter=Entry.objects.all()):
    num_entries = 20
    context = {"entries": {}}
    for at in ActionType.objects.all():
        queryset = prefilter.filter(actiontype=at).order_by("-pk")
        context["entries"][at] = {
            "objs": queryset[:num_entries],
            "total": queryset.count(),
        }

    return render(request, "route_manager/home.html", context)


def search_entries(request):
    # We call home_page because search is just a more specific case of the same view and template to return
    return home_page(
        request,
        Entry.objects.filter(
            route__route__net_contained_or_equal=request.POST.get("cidr")
        ),
    )
