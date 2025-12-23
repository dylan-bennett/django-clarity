from django.forms import ModelForm
from django.forms.models import inlineformset_factory, modelform_factory
from django.urls import path
from django.views.generic import RedirectView

from .dataclasses import ReadOnlyField
from .views import (
    DjangoClarityAppIndexView,
    DjangoClarityIndexView,
    DjangoClarityModelCreateView,
    DjangoClarityModelDeleteView,
    DjangoClarityModelListView,
    DjangoClarityModelUpdateView,
)


def create_inline_formsets(model, inlines):
    formsets = []
    formset_layouts = []
    for inline in inlines:
        # Meta = type(
        #     "Meta",
        #     (),
        #     {
        #         "model": inline.model,
        #         "fields": inline.fields,
        #         "widgets": inline.widgets,
        #     },
        # )
        # attrs = {"Meta": Meta}

        # formset_form_class = type(
        #     f"DjangoClarity{model._meta.model_name}{inline.model._meta.model_name}InlineModelForm",
        #     (ModelForm,),
        #     attrs,
        # )

        # All fields
        if inline.fields == "__all__":
            # Show only the editable fields, except for the FK relationship to the model
            # TODO: currently this shows the ID field, which we should maybe not show?
            formset_layout = tuple(
                field.name
                for field in inline.model._meta.fields
                if field.editable
                and getattr(field, "related_model", None) != model
                and getattr(field, "name", None) != "id"
            )

            # Send the string "__all__" to the model form factory
            formset_form_class = modelform_factory(
                inline.model,
                ModelForm,
                fields=inline.fields,
                widgets=inline.widgets,
            )

        # Select subset of fields (both editable and readonly)
        else:
            # Show both editable and readonly fields, except for the FK relationship to the model, but mark which ones are readonly
            formset_layout = tuple(
                (
                    ReadOnlyField(name=field, label_tag=field, value=None)
                    if field in inline.readonly_fields
                    else field
                )
                for field in inline.fields
                if getattr(field, "related_model", None) != model
                and getattr(field, "name", None) != "id"
            )

            # Send only the editable fields in to the model form factory
            # TODO: put this in a try..except to properly show the error if a readonly field is not in readonly_fields
            formset_form_class = modelform_factory(
                inline.model,
                ModelForm,
                # fields=inline.fields,
                fields=tuple(
                    field
                    for field in inline.fields
                    if field not in inline.readonly_fields
                ),
                widgets=inline.widgets,
            )

        formsets.append(
            inlineformset_factory(
                model,
                inline.model,
                form=formset_form_class,
                extra=inline.extra,
            )
        )
        formset_layouts.append(formset_layout)

    return formsets, formset_layouts


def create_model_form_class(model, model_admin):
    # url_name_prefix = f"djangoclarity-{model._meta.app_label}-{model._meta.model_name}"

    # # Create the Meta class dynamically
    # Meta = type(
    #     "Meta",
    #     (),
    #     {
    #         "model": model,
    #         # "fields": tuple(
    #         #     field
    #         #     for field in model_admin.fields
    #         #     if field not in model_admin.readonly_fields
    #         # ),
    #         "fields": model_admin.fields,
    #         "widgets": model_admin.widgets,
    #         # "readonly_fields": model_admin.readonly_fields,
    #         "url_names": {
    #             "create_url_name": f"{url_name_prefix}-create",
    #             "delete_url_name": f"{url_name_prefix}-delete",
    #             "index_url_name": f"{url_name_prefix}-index",
    #             "update_url_name": f"{url_name_prefix}-update",
    #         },
    #     },
    # )

    # Create the new ModelForm class
    # attrs = {"Meta": Meta}
    # FormClass = type(
    #     f"DjangoClarity{model._meta.app_label}{model._meta.model_name}ModelForm",
    #     (ModelForm,),
    #     attrs,
    # )

    # All fields
    if model_admin.fields == "__all__":
        # Show only the editable fields
        # TODO: currently this shows the ID field, which we should maybe not show?
        form_layout = tuple(
            field.name
            for field in model._meta.fields
            if field.editable and field.name != "id"
        )

        # Send the string "__all__" to the model form factory
        FormClass = modelform_factory(
            model,
            ModelForm,
            fields=model_admin.fields,
            widgets=model_admin.widgets,
        )

    # Select subset of fields (both editable and readonly)
    else:
        # Show both editable and readonly fields, but mark which ones are readonly
        form_layout = tuple(
            (
                ReadOnlyField(name=field, label_tag=field, value=None)
                if field in model_admin.readonly_fields
                else field
            )
            for field in model_admin.fields
            # if field != "id"
        )

        # Send only the editable fields in to the model form factory
        # TODO: put this in a try..except to properly show the error if a readonly field is not in readonly_fields
        FormClass = modelform_factory(
            model,
            ModelForm,
            fields=tuple(
                field
                for field in model_admin.fields
                if field not in model_admin.readonly_fields
            ),
            widgets=model_admin.widgets,
        )

    # fields = model_admin.fields
    # if fields != "__all__":
    #     # fields = tuple(field.name for field in model._meta.fields if field.editable)
    #     fields = tuple(
    #         field for field in fields if field not in model_admin.readonly_fields
    #     )
    # # fields = (
    # #     model._meta.fields if model_admin.fields == "__all__" else model_admin.fields
    # # )

    # FormClass = modelform_factory(
    #     model,
    #     ModelForm,
    #     fields=fields,
    #     # fields=fields,
    #     widgets=model_admin.widgets,
    # )

    # # Extend the class to add in the __init__ function for any readonly fields
    # class FormClass(FormClass):
    #     def __init__(self, *args, **kwargs):
    #         super().__init__(*args, **kwargs)
    #         if self.instance:
    #             for readonly_field in model_admin.readonly_fields:
    #                 self.fields[readonly_field].disabled = True
    #                 self.fields[readonly_field].initial = getattr(
    #                     self.instance, readonly_field
    #                 )

    # for readonly_field in model_admin.readonly_fields:
    #     setattr(form_class, readonly_field, )

    # TODO: denote which fields in "form_layout" are readonly -- dataclass?
    # return {"form_class": FormClass, "form_layout": form_layout}
    return FormClass, form_layout


class ModelAdmin:
    fields = "__all__"
    readonly_fields = ()
    widgets = {}
    inlines = []
    create_view_class = DjangoClarityModelCreateView
    delete_view_class = DjangoClarityModelDeleteView
    index_view_class = DjangoClarityModelListView
    update_view_class = DjangoClarityModelUpdateView


class InlineModelAdmin:
    model = None
    fields = "__all__"
    readonly_fields = ()
    widgets = {}
    extra = 3


class AdminSite:
    _registry = {}
    _namespace = "djangoclarity"

    def register(self, model, model_admin=None):
        # Set up the default Model Admin class, if necessary
        model_admin = model_admin or ModelAdmin

        # Add these to the registry
        self._registry[model] = model_admin

    def get_urls(self):
        urlpatterns = []
        app_label_models_dict = {}

        # Go through each registered model
        for model, model_admin in self._registry.items():
            # Keep track of the model and its app label, for later
            if model._meta.app_label not in app_label_models_dict:
                app_label_models_dict[model._meta.app_label] = []
            app_label_models_dict[model._meta.app_label].append(model)

            form_class, form_layout = create_model_form_class(model, model_admin)
            formsets, formset_layouts = create_inline_formsets(
                model, model_admin.inlines
            )
            create_view_class = model_admin.create_view_class
            delete_view_class = model_admin.delete_view_class
            index_view_class = model_admin.index_view_class
            update_view_class = model_admin.update_view_class
            url_prefix = f"{model._meta.app_label}/{model._meta.model_name}"

            url_name_prefix = (
                f"djangoclarity-{model._meta.app_label}-{model._meta.model_name}"
            )

            urlpatterns += [
                # Main paths
                path(
                    f"{url_prefix}/add/",
                    create_view_class.as_view(
                        form_class=form_class,
                        form_layout=form_layout,
                        formsets=formsets,
                        formset_layouts=formset_layouts,
                        namespace=self._namespace,
                    ),
                    # name=form_class.Meta.url_names["create_url_name"],
                    name=f"{url_name_prefix}-create",
                ),
                path(
                    f"{url_prefix}/<int:pk>/delete/",
                    delete_view_class.as_view(
                        form_class=form_class,
                        form_layout=form_layout,
                        formsets=formsets,
                        formset_layouts=formset_layouts,
                        namespace=self._namespace,
                    ),
                    # name=form_class.Meta.url_names["delete_url_name"],
                    name=f"{url_name_prefix}-delete",
                ),
                path(
                    f"{url_prefix}/",
                    index_view_class.as_view(
                        form_class=form_class,
                        form_layout=form_layout,
                        formsets=formsets,
                        formset_layouts=formset_layouts,
                        namespace=self._namespace,
                    ),
                    # name=form_class.Meta.url_names["index_url_name"],
                    name=f"{url_name_prefix}-index",
                ),
                path(
                    f"{url_prefix}/<int:pk>/change/",
                    update_view_class.as_view(
                        form_class=form_class,
                        form_layout=form_layout,
                        formsets=formsets,
                        formset_layouts=formset_layouts,
                        namespace=self._namespace,
                    ),
                    # name=form_class.Meta.url_names["update_url_name"],
                    name=f"{url_name_prefix}-update",
                ),
                # Redirect paths
                path(
                    f"{url_prefix}/index/",
                    RedirectView.as_view(
                        pattern_name=f"{self._namespace}:{url_name_prefix}-index"
                    ),
                ),
                path(
                    f"{url_prefix}/delete/",
                    RedirectView.as_view(
                        pattern_name=f"{self._namespace}:{url_name_prefix}-index"
                    ),
                ),
                path(
                    f"{url_prefix}/change/",
                    RedirectView.as_view(
                        pattern_name=f"{self._namespace}:{url_name_prefix}-index"
                    ),
                ),
                path(
                    f"{url_prefix}/<int:pk>/",
                    RedirectView.as_view(
                        pattern_name=f"{self._namespace}:{url_name_prefix}-update"
                    ),
                ),
            ]

        # Create URL patterns for each app label
        for app_label, models in app_label_models_dict.items():
            urlpatterns.append(
                path(
                    f"{app_label}/",
                    DjangoClarityAppIndexView.as_view(
                        namespace=self._namespace, app_label=app_label, models=models
                    ),
                    name=f"djangoclarity-{app_label}-index",
                )
            )

        # Create a final URL pattern for the overview index
        urlpatterns.append(
            path(
                "",
                DjangoClarityIndexView.as_view(
                    namespace=self._namespace,
                    app_label_models_dict=app_label_models_dict,
                ),
                name="djangoclarity-index",
            )
        )

        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), self._namespace


site = AdminSite()
