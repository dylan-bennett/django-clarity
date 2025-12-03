import json

from django.core.exceptions import FieldDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django_ckeditor_5.widgets import CKEditor5Widget

# from mainsite.widgets import ThumbnailImageWidget


def _add_error(form, field_name, error_text):
    """
    Safely adds an error to a form field or form-wide errors.

    Django's form.add_error() removes the field from form.cleaned_data when adding
    an error, but raises AttributeError if cleaned_data doesn't exist yet. This method
    handles that case gracefully.

    Args:
        form: The Django form instance to add the error to
        field_name: Name of the field to attach error to, or None for non-field errors
        error_text: The error message to add
    """
    try:
        form.add_error(field_name, error_text)
    except AttributeError:
        pass


def get_form_errors(form):
    """
    Compiles all errors from a form into a list of formatted error messages.

    Collects both non-field errors and field-specific errors from the form.
    Field-specific errors are prefixed with the field label for context.

    Args:
        form: The Django form instance to get errors from

    Returns:
        list: A list of error message strings. Empty list if no errors or no form.
        Each error is formatted as either:
            - The error message directly (for non-field errors)
            - "{field_label}: {error}" (for field-specific errors)
    """
    all_errors = []

    # Quick way of testing out what errors messages will look like on the frontend
    # _add_error(form, None, "main form non-field error")
    # _add_error(form, "slug", "The slug is missing, ya dink")

    # No errors to return if there's no form nor errors
    if not (form and form.errors):
        return all_errors

    # Add non-field errors
    all_errors.extend(form.non_field_errors())

    # Add field-specific errors
    for field, errors in form.errors.items():
        if field != "__all__":  # Skip non-field errors as we already added them
            field_label = form.fields[field].label or field
            all_errors.extend(f"{field_label}: {error}" for error in errors)

    return all_errors


def get_formset_errors(formset):
    """
    Compiles all errors from a formset into a list of formatted error messages.

    Collects formset-level errors and form-specific errors from each form in the formset.
    For form-specific errors, includes the form title/number and field label for context.

    Args:
        formset: The Django formset instance to get errors from

    Returns:
        list: A list of error message strings. Empty list if no errors or no formset.
        Each error is formatted as one of:
            - The error message directly (for formset-level errors)
            - "{form_title}: {error}" (for form-level errors)
            - "{form_title} - {field_label}: {error}" (for field-specific errors)
    """
    all_errors = []

    # Quick way of testing out what errors messages will look like on the frontend
    # if formset.forms:
    #     _add_error(formset.forms[0], None, "formset non-field error")
    #     _add_error(formset.forms[0], "title", "No title, tsk tsk tsk")
    # formset._non_form_errors = ["formset non-form error message"]

    # No errors to return if there's no formset
    if not formset:
        return all_errors

    # Add non-form errors (formset-level errors)
    all_errors.extend(formset.non_form_errors())

    for i, form in enumerate(formset.forms):
        form_errors = form.errors

        if not form_errors:
            continue

        # Get the string of the formset's model instance if it exists,
        # otherwise use the index with the name of the formset's model
        form_title = (
            str(form.instance)
            if form.instance and form.instance.pk
            else f"{formset.model.__name__} {i + 1}"
        )

        # Add non-field errors for this form
        if "__all__" in form_errors:
            all_errors.extend(
                f"{form_title}: {error}" for error in form_errors["__all__"]
            )

        # Add field-specific errors for this form
        for field, errors in form_errors.items():
            if field != "__all__":
                field_label = form.fields[field].label or field
                all_errors.extend(
                    f"{form_title} - {field_label}: {error}" for error in errors
                )

    return all_errors


class BaseCreatorView:
    # Attributes to be sent into the .as_view() method
    slug = None
    form_class = None
    formsets = []

    def __init__(self, *args, **kwargs):
        # Extract the required data from .as_view()'s kwargs
        # Slug
        try:
            self.slug = kwargs.pop("slug")
        except KeyError:
            raise TypeError(
                "%s() missing required keyword argument: 'slug'"
                % (self.__class__.__name__,)
            )

        # Form
        try:
            self.form_class = kwargs.pop("form_class")
        except KeyError:
            raise TypeError(
                "%s() missing required keyword argument: 'form_class'"
                % (self.__class__.__name__,)
            )

        # (Optional) Formsets
        self.formsets = kwargs.pop("formsets", [])

        # Create the remaining needed data
        self.model = self.form_class.Meta.model
        self.create_url_name = f"creator-{self.slug}-create"
        self.delete_url_name = f"creator-{self.slug}-delete"
        self.index_url_name = f"creator-{self.slug}-index"
        self.update_url_name = f"creator-{self.slug}-update"
        self.index_redirect_url_name = f"{self.index_url_name}-redirect"
        self.success_url = reverse_lazy(self.index_url_name)

        super().__init__(*args, **kwargs)


class BaseCreatorCreateView(CreateView):
    """
    Base view for creating a parent model instance (form).
    """

    template_name = "djangoclarity/base_creator_create_template.html"
    formsets = []

    def get_context_data(self, **kwargs):
        """
        Adds the formset to the template context.
        Also collects all form and formset errors into a single list.
        """
        context = super().get_context_data(**kwargs)

        # Collect all errors to display at the top
        all_errors = []
        all_errors.extend(get_form_errors(context.get("form")))
        context["all_errors"] = all_errors

        # Formset model names to let the user know about any child model relationships coming up
        context["formset_model_names"] = [
            formset.model._meta.verbose_name for formset in self.formsets
        ]

        # Index URL
        context["index_url"] = reverse(self.index_url_name)

        return context

    def get_success_url(self):
        """
        After successful save, redirect to the update view for the parent model instance.
        """
        return reverse(self.update_url_name, kwargs={"pk": self.object.pk})


class BaseCreatorUpdateView(UpdateView):
    """
    Base view for updating a parent model instance (form)
    and children model instances (formsets).
    """

    # The HTML template used to render the Creator frontend
    template_name = "djangoclarity/base_creator_update_template.html"
    formsets = []

    def get_context_data(self, **kwargs):
        """
        Adds the formset to the template context.
        Also collects all form and formset errors into a single list.
        """
        context = super().get_context_data(**kwargs)

        # If this is a POST request, put the POST and FILES data
        # into the child model's formset. The FILES data is for any images.
        # Otherwise, initialize an empty formset (or with existing instance data if updating).
        context["formsets"] = [
            formset(
                data=self.request.POST if self.request.POST else None,
                files=self.request.FILES if self.request.POST else None,
                instance=self.object,
            )
            for formset in self.formsets
        ]

        # Collect all errors to display at the top
        all_errors = []
        all_errors.extend(get_form_errors(context.get("form")))
        for formset in context["formsets"]:
            all_errors.extend(get_formset_errors(formset))
        context["all_errors"] = all_errors

        # Index URL
        context["index_url"] = reverse(self.index_url_name)

        # Delete URL
        context["delete_url"] = reverse(
            self.delete_url_name, kwargs={"pk": self.object.pk}
        )

        return context

    def form_valid(self, form):
        """
        Called when the form is valid.
        Also validates and saves the formset.
        """
        # Get the context which includes our formset
        context = self.get_context_data(form=form)
        formsets = context["formsets"]

        # Because form.is_valid() was already called and it passed,
        # we only need to check the validity of each formset in our formsets.
        if all(formset.is_valid() for formset in formsets):
            # Start a transaction to ensure the form and all formsets save together
            with transaction.atomic():
                # Save the form instance to the database
                form.save()

                # Go through each formset and save its instances to the database.
                # This will also take care of deleting instances from the formsets.
                for formset in formsets:
                    formset.save()

            return super().form_valid(form)
        else:
            # If anything is invalid, re-render with errors
            return self.render_to_response(context)

    def get_success_url(self):
        """
        After successful save, redirect to the update view for the parent model instance.
        """
        return reverse(self.update_url_name, kwargs={"pk": self.object.pk})

    def post(self, request, **kwargs):
        # April 21, 2025 -- dani@hatchcoding.com, dylan@hatchcoding.com

        # A Creator can contain a list of formsets, and each formset is a list of forms. A formset can also contain
        # "extra" forms (e.g., `extra=3`), in case you want to create new database records using the formset.

        # CKEditor has a bug where an empty, optional editor will actually contain a paragraph with a non-breaking space
        # (https://github.com/ckeditor/ckeditor5/issues/401).

        # The problem is that if a formset's empty form detects any content in any of the fields, it thinks that we want
        # that form to create a new record. And since an empty CKEditor's content is not actually an empty string, but
        # instead is a paragraph element with a non-breaking space, that means that none of our "empty" forms are
        # actually considered empty.

        # This fix is very hacky, but it works. We're basically grabbing the POST information immediately after the
        # form's Submit button is pressed and we're manipulating the data before Django's form validation is able to
        # check it.

        # Ideally we'd find a better way of doing this, but for now (and for this specific use case) this solution will
        # have to stay.

        request.POST = request.POST.copy()

        for key, value in request.POST.items():
            if value == "<p>&nbsp;</p>":
                request.POST[key] = ""

        return super().post(request, **kwargs)


class BaseCreatorIndexView(ListView):
    template_name = "djangoclarity/base_creator_index_template.html"
    base_template = "djangoclarity/base.html"
    items_per_page = 10
    order_by_fields = ("id",)

    def get_queryset(self):
        """
        Filter the queryset based on the search parameter if provided.
        """
        queryset = super().get_queryset().order_by(*self.order_by_fields)
        search_term = self.request.GET.get("search", "")

        if search_term:
            # Get the field names to search in
            field_names = self._get_field_names()

            # Create a Q object for each field
            query = Q()
            for field_name in field_names:
                try:
                    # Skip foreign key fields
                    field = self.model._meta.get_field(field_name)
                    if field.is_relation:
                        continue

                    query |= Q(**{f"{field_name}__icontains": search_term})
                except FieldDoesNotExist:
                    # Skip fields that don't exist in the database
                    continue

            # Apply the filter
            queryset = queryset.filter(query)

        return queryset

    def _get_pagination_data(self):
        """
        Helper method to get pagination data.
        Returns a tuple of (page_number, total_items)
        """
        page = self.request.GET.get("page", 1)
        try:
            page = int(page)
        except (TypeError, ValueError):
            page = 1

        if page < 1:
            page = 1

        # Use the cached queryset from object_list for total
        total_items = self.object_list.count()

        return page, total_items

    def _get_paginated_queryset(self, page, total_items):
        """
        Helper method to get the queryset for the current page.
        """
        # Calculate the start and end indices for the current page
        start_index = (page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page

        return self.object_list[start_index:end_index]

    def _get_field_names(self):
        """
        Return the list of field names (column headers) for our index page.
        These will be gotten from the form's fields, and will exclude
        anything that wouldn't fit well on a table (e.g., images, TextField, etc.)
        This also does not include the Update/Delete links.
        """
        field_names = []
        for field_name, field in self.form_class().fields.items():
            # if isinstance(field.widget, CKEditor5Widget) or isinstance(
            #     field.widget, ThumbnailImageWidget
            # ):
            if isinstance(field.widget, CKEditor5Widget):
                continue
            field_names.append(field_name)

        return field_names

    def _get_extra_items(self, obj):
        """Base method to return a dictionary of extra items, meant to be overridden."""
        return {}

    def get_items(self):
        """Return the list of instance objects, ready for JSON serialization."""
        items = []

        # Get pagination data
        page, total_items = self._get_pagination_data()

        # Get the paginated queryset
        paginated_queryset = self._get_paginated_queryset(page, total_items)

        for obj in paginated_queryset:
            d = model_to_dict(obj, self._get_field_names())

            # Add in any extra items
            d.update(self._get_extra_items(obj))

            # Add in final columns of the Update & Delete URLs
            d[self.update_url_name] = (
                reverse(self.update_url_name, kwargs={"pk": obj.pk}),
            )
            d[self.delete_url_name] = (
                reverse(self.delete_url_name, kwargs={"pk": obj.pk}),
            )

            # Add the row of information to the list of items. Use the `get_{attr_name}_display()` method if it exists.
            items.append(
                {
                    key: (
                        getattr(obj, f"get_{key}_display")()
                        if hasattr(obj, f"get_{key}_display")
                        else value
                    )
                    for key, value in d.items()
                }
            )

        return items

    def _get_extra_fields(self):
        """Base method to return a list of extra fields, meant to be overridden."""
        return []

    def get_fields(self):
        """Return the list of field headers for the index table."""
        fields = [
            {"key": field_name, "sortable": True}
            for field_name in self._get_field_names()
        ]

        # Add in any extra fields
        fields.extend(self._get_extra_fields())

        # Add in final columns for the Update & Delete URLs
        fields.append({"key": self.update_url_name, "label": "Update"})
        fields.append({"key": self.delete_url_name, "label": "Delete"})

        return fields

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["base_template"] = getattr(
            self, "base_template", "djangoclarity/base.html"
        )

        # Add in the Update URL name for proper hyperlink rendering on the frontend
        context["update_url_name"] = self.update_url_name
        context["delete_url_name"] = self.delete_url_name

        # Add in the Create URL name
        context["create_url"] = reverse(self.create_url_name)

        # Add model verbose name for template use
        context["model_verbose_name"] = self.model._meta.verbose_name

        # Get pagination data
        page, total_items = self._get_pagination_data()

        # Set the JSONified context for the BootstrapVue app
        context["js_context"] = json.dumps(
            {
                "items": self.get_items(),
                "fields": self.get_fields(),
                "pagination": {
                    "total": total_items,
                    "per_page": self.items_per_page,
                    "current_page": page,
                },
            }
        )

        return context


class BaseCreatorDeleteView(DeleteView):
    template_name = "djangoclarity/base_creator_delete_template.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Index URL
        context["index_url"] = reverse(self.index_url_name)

        return context

    def post(self, request, *args, **kwargs):
        """Override post to handle deletion with form_class present"""
        self.object = self.get_object()

        # Perform the deletion
        self.object.delete()

        return HttpResponseRedirect(self.get_success_url())


class CreatorCreateView(BaseCreatorView, BaseCreatorCreateView):
    pass


class CreatorDeleteView(BaseCreatorView, BaseCreatorDeleteView):
    pass


class CreatorIndexView(BaseCreatorView, BaseCreatorIndexView):
    pass


class CreatorUpdateView(BaseCreatorView, BaseCreatorUpdateView):
    pass
