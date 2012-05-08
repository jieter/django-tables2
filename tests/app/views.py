from django.shortcuts import render_to_response


def view(request):
    return render_to_response("template.html")
