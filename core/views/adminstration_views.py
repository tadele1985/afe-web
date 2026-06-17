from django.http.response import HttpResponse


def users(request):
    return HttpResponse("<h1>Hello</h1>")
