from django.shortcuts import redirect, render_to_response


def view(request):
    return render_to_response("template.html")


def bouncer(request):
    return redirect("https://example.com:1234/foo/?a=b#bar")
