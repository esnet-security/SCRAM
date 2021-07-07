from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

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


@require_POST
def delete_entry(request, pk):
    query = get_object_or_404(Entry, pk=pk)
    query.delete()
    return redirect("route_manager:home")


class EntryDetailView(DetailView):
    model = Entry
    template_name = "route_manager/entry_detail.html"


class EntryListView(ListView):
    model = Entry
    template_name = "route_manager/entry_list.html"

    def get_context_data(self, **kwargs):
        context = {"entries": {}}
        for at in ActionType.objects.all():
            queryset = Entry.objects.filter(actiontype=at).order_by("-pk")
            context["entries"][at] = {
                "objs": queryset,
                "total": queryset.count(),
            }
        return context
