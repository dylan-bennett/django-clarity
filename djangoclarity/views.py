import json
import pprint

from django.core.exceptions import FieldDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.forms import model_to_dict
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.views.generic.base import TemplateView


class DjangoClarityIndexView(TemplateView):
    base_template = "djangoclarity/base.html"
    template_name = "djangoclarity/index.html"
    namespace = None
    app_label_models_dict = None

    def __init__(self, *args, **kwargs):
        # Extract the required data from .as_view()'s kwargs
        # Namespace
        try:
            self.namespace = kwargs.pop("namespace")
        except KeyError:
            raise TypeError(
                "%s() missing required keyword argument: 'namespace'"
                % (self.__class__.__name__,)
            )

        # Dictionary of app labels and their models
        try:
            self.app_label_models_dict = kwargs.pop("app_label_models_dict")
        except KeyError:
            raise TypeError(
                "%s() missing required keyword argument: 'app_label_models_dict'"
                % (self.__class__.__name__,)
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["app_labels_models"] = []

        for app_label, models in sorted(self.app_label_models_dict.items()):
            app_models_dict = {}

            app_models_dict["app_label"] = {
                "url": reverse(f"{self.namespace}:djangoclarity-{app_label}-index"),
                "title": app_label.upper(),
            }

            app_models_dict["models"] = []
            for model in sorted(models, key=lambda m: m.__name__):
                app_models_dict["models"].append(
                    {
                        "url": reverse(
                            f"{self.namespace}:djangoclarity-{app_label}-{model._meta.model_name}-index"
                        ),
                        "title": model._meta.verbose_name_plural.title(),
                    }
                )

            context["app_labels_models"].append(app_models_dict)

        return context


class DjangoClarityAppIndexView(TemplateView):
    base_template = "djangoclarity/base.html"
    template_name = "djangoclarity/app_index.html"
    namespace = None
    app_label = None
    models = None

    def __init__(self, *args, **kwargs):
        # Extract the required data from .as_view()'s kwargs
        # Namespace
        try:
            self.namespace = kwargs.pop("namespace")
        except KeyError:
            raise TypeError(
                "%s() missing required keyword argument: 'namespace'"
                % (self.__class__.__name__,)
            )

        # App Label
        try:
            self.app_label = kwargs.pop("app_label")
        except KeyError:
            raise TypeError(
                "%s() missing required keyword argument: 'app_label'"
                % (self.__class__.__name__,)
            )

        # Models
        try:
            self.models = kwargs.pop("models")
        except KeyError:
            raise TypeError(
                "%s() missing required keyword argument: 'models'"
                % (self.__class__.__name__,)
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["app_label"] = {
            "url": reverse(f"{self.namespace}:djangoclarity-{self.app_label}-index"),
            "title": self.app_label.upper(),
            "window_title": self.app_label.title(),
        }

        context["models"] = []
        for model in sorted(self.models, key=lambda m: m.__name__):
            context["models"].append(
                {
                    "url": reverse(
                        f"{self.namespace}:djangoclarity-{self.app_label}-{model._meta.model_name}-index"
                    ),
                    "title": model._meta.verbose_name_plural.title(),
                }
            )

        return context


class DjangoClarityModelBaseView:
    base_template = "djangoclarity/base.html"

    # Attributes to be sent into the .as_view() method
    slug = None
    # form_class_and_layout = None
    form_class = None
    form_layout = None
    formsets = []
    formset_layouts = []
    namespace = None

    def __init__(self, *args, **kwargs):
        # Extract the required data from .as_view()'s kwargs
        # Form
        try:
            self.form_class = kwargs.pop("form_class")
        except KeyError:
            raise TypeError(
                "%s() missing required keyword argument: 'form_class'"
                % (self.__class__.__name__,)
            )
        # self.form_class = self.form_class_and_layout["form_class"]

        # Form Layout
        try:
            self.form_layout = kwargs.pop("form_layout")
        except KeyError:
            raise TypeError(
                "%s() missing required keyword argument: 'form_layout'"
                % (self.__class__.__name__,)
            )

        # Formsets
        self.formsets = kwargs.pop("formsets", [])
        self.formset_layouts = kwargs.pop("formset_layouts", [])

        # Namespace
        try:
            self.namespace = kwargs.pop("namespace")
        except KeyError:
            raise TypeError(
                "%s() missing required keyword argument: 'namespace'"
                % (self.__class__.__name__,)
            )

        # Create the remaining needed data
        self.model = self.form_class.Meta.model
        url_name_prefix = (
            f"djangoclarity-{self.model._meta.app_label}-{self.model._meta.model_name}"
        )
        # self.create_url_name = self.form_class.Meta.url_names["create_url_name"]
        # self.delete_url_name = self.form_class.Meta.url_names["delete_url_name"]
        # self.index_url_name = self.form_class.Meta.url_names["index_url_name"]
        # self.update_url_name = self.form_class.Meta.url_names["update_url_name"]
        self.create_url_name = f"{url_name_prefix}-create"
        self.delete_url_name = f"{url_name_prefix}-delete"
        self.index_url_name = f"{url_name_prefix}-index"
        self.update_url_name = f"{url_name_prefix}-update"

        # Set a custom success_url for after updating the database
        # self.success_url = reverse(f"{self.namespace}:{self.index_url_name}")

        # TODO: do I need to do this? DjangoClarityModelBaseView doesn't have a superclass
        super().__init__(*args, **kwargs)

    def get_form_errors(self, form):
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

    def get_formset_errors(self, formset):
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


class DjangoClarityModelCreateView(DjangoClarityModelBaseView, CreateView):
    """
    Base view for creating a parent model instance (form).
    """

    template_name = "djangoclarity/base_create_template.html"
    formsets = []

    def get_context_data(self, **kwargs):
        """
        Adds the formset to the template context.
        Also collects all form and formset errors into a single list.
        """
        context = super().get_context_data(**kwargs)

        # Form layout
        context["form_layouts"] = [self.form_layout]

        # Collect all errors to display at the top
        all_errors = []
        all_errors.extend(self.get_form_errors(context.get("form")))
        context["all_errors"] = all_errors

        # Formset model names to let the user know about any child model relationships coming up
        context["formset_model_names"] = [
            formset.model._meta.verbose_name for formset in self.formsets
        ]

        # Index URL
        context["index_url"] = reverse(f"{self.namespace}:{self.index_url_name}")

        # Add model verbose name for template use
        context["model_verbose_name"] = self.model._meta.verbose_name

        return context

    def get_success_url(self):
        """
        After successful save, redirect to the update view for the parent model instance.
        """
        return reverse(
            f"{self.namespace}:{self.update_url_name}", kwargs={"pk": self.object.pk}
        )


class DjangoClarityModelUpdateView(DjangoClarityModelBaseView, UpdateView):
    """
    Base view for updating a parent model instance (form)
    and children model instances (formsets).
    """

    template_name = "djangoclarity/base_update_template.html"
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

        # Layouts for the formsets
        context["formset_layouts"] = self.formset_layouts

        # Form layout
        context["form_layouts"] = [self.form_layout]

        # Collect all errors to display at the top
        all_errors = []
        all_errors.extend(self.get_form_errors(context.get("form")))
        for formset in context["formsets"]:
            all_errors.extend(self.get_formset_errors(formset))
        context["all_errors"] = all_errors

        # Index URL
        context["index_url"] = reverse(f"{self.namespace}:{self.index_url_name}")

        # Delete URL
        context["delete_url"] = reverse(
            f"{self.namespace}:{self.delete_url_name}", kwargs={"pk": self.object.pk}
        )

        # Add model verbose name for template use
        context["model_verbose_name"] = self.model._meta.verbose_name

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
        return reverse(
            f"{self.namespace}:{self.update_url_name}", kwargs={"pk": self.object.pk}
        )


class DjangoClarityModelListView(DjangoClarityModelBaseView, ListView):
    template_name = "djangoclarity/base_index_template.html"
    items_per_page = 10
    order_by_fields = ("id",)
    paginate_by = 10

    def get_queryset(self):
        """
        Filter the queryset based on the search parameter if provided.
        """
        queryset = super().get_queryset().order_by(*self.order_by_fields)
        search_term = self.request.GET.get("q", "")

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
        These will be gotten from the form's fields.
        This also does not include the Update/Delete links.
        """
        field_names = []
        layout = self.form_layout
        # for field_name, field in layout:
        for field_name in layout:
            field_names.append(field_name)

        return field_names

    def _get_extra_items(self, obj):
        """Base method to return a dictionary of extra items, meant to be overridden."""
        return {}

    # def get_items(self):
    #     """Return the list of instance objects, ready for JSON serialization."""
    #     items = []

    #     # Get pagination data
    #     page, total_items = self._get_pagination_data()

    #     # Get the paginated queryset
    #     paginated_queryset = self._get_paginated_queryset(page, total_items)

    #     for obj in paginated_queryset:
    #         d = model_to_dict(obj, self._get_field_names())

    #         # Add in any extra items
    #         d.update(self._get_extra_items(obj))

    #         # Add in final columns of the Update & Delete URLs
    #         d[self.update_url_name] = (
    #             reverse(
    #                 f"{self.namespace}:{self.update_url_name}", kwargs={"pk": obj.pk}
    #             ),
    #         )
    #         d[self.delete_url_name] = (
    #             reverse(
    #                 f"{self.namespace}:{self.delete_url_name}", kwargs={"pk": obj.pk}
    #             ),
    #         )

    #         # Add the row of information to the list of items. Use the `get_{attr_name}_display()` method if it exists.
    #         items.append(
    #             {
    #                 key: (
    #                     getattr(obj, f"get_{key}_display")()
    #                     if hasattr(obj, f"get_{key}_display")
    #                     else value
    #                 )
    #                 for key, value in d.items()
    #             }
    #         )

    #     return items

    def _get_extra_fields(self):
        """Base method to return a list of extra fields, meant to be overridden."""
        return []

    # def get_fields(self):
    #     """Return the list of field headers for the index table."""
    #     fields = [
    #         {"key": field_name, "sortable": True}
    #         for field_name in self._get_field_names()
    #     ]

    #     # Add in any extra fields
    #     fields.extend(self._get_extra_fields())

    #     # Add in final columns for the Update & Delete URLs
    #     fields.append({"key": self.update_url_name, "label": "Update"})
    #     fields.append({"key": self.delete_url_name, "label": "Delete"})

    #     return fields

    def get_headers(self):
        """Return the list of field headers for the index table."""
        headers = self._get_field_names()

        # Add in any extra headers
        headers += self._get_extra_fields()

        # Add in final headers for the Update & Delete URLs
        headers.append(self.update_url_name)
        headers.append(self.delete_url_name)

        return headers

    def get_rows(self):
        """Return a list of dicts, one per object in the query"""
        items = []

        # Get pagination data
        page, total_items = self._get_pagination_data()

        # Get the paginated queryset
        paginated_queryset = self._get_paginated_queryset(page, total_items)

        for obj in paginated_queryset:
            # d = model_to_dict(obj, self._get_field_names())

            # Build dict manually from requested field names
            d = {}
            for field_name in self._get_field_names():
                try:
                    field = self.model._meta.get_field(field_name)
                    value = getattr(obj, field_name)
                    # Handle ForeignKey fields - convert to the string
                    if field.is_relation and not field.many_to_many:
                        d[field_name] = str(value) if value else None
                    else:
                        d[field_name] = value
                except (AttributeError, FieldDoesNotExist):
                    # Skip if field doesn't exist (might be a form-only field)
                    continue

            # Add in any extra items
            d.update(self._get_extra_items(obj))

            # Add in final columns of the Update & Delete URLs
            d[self.update_url_name] = reverse(
                f"{self.namespace}:{self.update_url_name}", kwargs={"pk": obj.pk}
            )
            d[self.delete_url_name] = reverse(
                f"{self.namespace}:{self.delete_url_name}", kwargs={"pk": obj.pk}
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

    def update_object_list(self, paginator):
        """Update the Paginator's object_list to include entries for the Update and Delete URLs"""
        items = []

        # # Get pagination data
        # page, total_items = self._get_pagination_data()

        # # Get the paginated queryset
        # paginated_queryset = self._get_paginated_queryset(page, total_items)

        for obj in paginator.object_list.all():
            d = model_to_dict(obj, self._get_field_names())

            # Add in any extra items
            d.update(self._get_extra_items(obj))

            # Add in final columns of the Update & Delete URLs
            d[self.update_url_name] = reverse(
                f"{self.namespace}:{self.update_url_name}", kwargs={"pk": obj.pk}
            )
            d[self.delete_url_name] = reverse(
                f"{self.namespace}:{self.delete_url_name}", kwargs={"pk": obj.pk}
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["base_template"] = getattr(
            self, "base_template", "djangoclarity/base.html"
        )

        # Add in the Update URL name for proper hyperlink rendering on the frontend
        context["update_url_name"] = self.update_url_name
        context["delete_url_name"] = self.delete_url_name

        # Add in the Create URL name
        context["create_url"] = reverse(f"{self.namespace}:{self.create_url_name}")

        # Add model verbose name for template use
        context["model_verbose_name"] = self.model._meta.verbose_name

        # Get the items and field for the table
        context["items"] = self.get_rows()
        context["fields"] = self.get_headers()

        # TODO: I'm definitely duplicating efforts with the pagination thing. Look into the Django Paginator class and see if there's a way to override its object_list or page_obj or whatever, so that we can add in the Delete and Update URLs as extra attributes. That way we won't have to write our own pagination methods.

        # pprint.pp(context, indent=2)
        # context["paginator"].object_list = self.update_object_list(context["paginator"])

        # pprint.pp(context["paginator"].object_list)

        return context


class DjangoClarityModelDeleteView(DjangoClarityModelBaseView, DeleteView):
    template_name = "djangoclarity/base_delete_template.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Index URL
        context["index_url"] = reverse(f"{self.namespace}:{self.index_url_name}")

        # Add model verbose name for template use
        context["model_verbose_name"] = self.model._meta.verbose_name

        return context

    def post(self, request, *args, **kwargs):
        """Override post to handle deletion with form_class present"""
        self.object = self.get_object()

        # Perform the deletion
        self.object.delete()

        return HttpResponseRedirect(self.get_success_url())
