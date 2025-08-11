from django.shortcuts import redirect, render
from apps.models import WebviewIntegrations
from apps.forms import (WebviewIntegrationsAddForm,
                        WebviewIntegrationsUpdateForm,
                        APIIntegrationsAddForm
                        )
from django.contrib import messages
import webview
from rbac.decorators import has_permission
####################
# WEBVIEW
####################


@has_permission('apps.view_webviewintegrations')
def webview_urls_view(request):
    webview = WebviewIntegrations.objects.all().order_by("-favorite")
    if request.method == "POST":
        form = WebviewIntegrationsAddForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "App Integration inserted successfully!")
            return redirect("apps:webview.links")
        else:
            print(form.errors)
            messages.error(request, "Something went wrong!")
            return redirect("apps:webview.links")
    return render(request, "apps/webview/apps-webview.html", {"webview": webview})


@has_permission('apps.change_webviewintegrations')
def webview_update_view(request, pk):
    webview = WebviewIntegrations.objects.get(pk=pk)
    if request.method == "POST":
        form = WebviewIntegrationsUpdateForm(
            request.POST or None, request.FILES or None, instance=webview
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Webview Updated successfully!")
            return redirect("apps:webview.links")
        else:
            print(form.errors)
            messages.error(request, "Something went wrong!")
            return redirect("apps:crm.leads")
    return render(request, "apps/webview/apps-webview.html")


@has_permission('apps.delete_webviewintegrations')
def webview_delete_view(request, pk):
    webview = WebviewIntegrations.objects.get(pk=pk)
    webview.delete()
    messages.success(request, "Webview deleted successfully!")
    return redirect("apps:webview.links")


@has_permission('apps.view_webviewintegrations')
def webview_open_webview(request, pk):
    newwebview = WebviewIntegrations.objects.get(pk=pk)
    window = webview.create_window("Woah dude!", newwebview["url"])
    window.start()


def apps_apiadd_view(request):
    if request.method == "POST":
        form = APIIntegrationsAddForm(
            request.POST or None, request.FILES or None, instance=webview
        )
        if form.is_valid():
            form.save()
            messages.success(request, "API Added successfully!")
            return redirect("pages:profile_settings")
        else:
            print(form.errors)
            messages.error(request, "Something went wrong!")
            return redirect("pages:profile_settings")
    return render(request, "pages:profile_settings")

