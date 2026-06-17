from django_tables2 import SingleTableView, Column
from core.models import FormSubmission
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.messages import success
from core.forms import UserForm
from django_filters import FilterSet
from django_filters.views import FilterView
import django_tables2 as tables
from django.middleware import csrf
from django.template.loader import render_to_string
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse

class FormSubmissionTable(tables.Table):
    name = tables.Column(
        accessor="name", verbose_name="name"
    )
    actions = tables.Column(accessor="id", verbose_name="Actions", orderable=False)

    class Meta:
        model = FormSubmission
        fields = ['name'] 
        attrs = {"class": "table"}

    def render_actions(self, value):
        csrf_token = csrf.get_token(self.request)
        user_form = UserForm(initial={"id": value})
        return render_to_string(
            "partials/form-submission-action.html",
            {"id": value, "csrf_token": csrf_token, "form": user_form},
        )


class FormSubmissionFilter(FilterSet):
    class Meta:
        model = FormSubmission
        fields = {
            "name": ["exact"],
        }
        form = UserForm


class FormSubmissionListView(SingleTableView, FilterView):
    model = FormSubmission
    table_class = FormSubmissionTable  # To be defined later
    template_name = 'core/form_submission_list.html'
    filterset_class = FormSubmissionFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = "Form submission list"
        return context

@login_required
def form_submission_detail(request, uuid):
    form_submission = FormSubmission.objects.get(id=uuid)
    return render(request, 'core/form_submission_detail.html', {"form_submission": form_submission})
