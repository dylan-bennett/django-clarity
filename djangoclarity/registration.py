from django.forms import ModelForm
from django.urls import path
from django.views.generic import RedirectView

from .views import (
    DjangoClarityCreateView,
    DjangoClarityDeleteView,
    DjangoClarityListView,
    DjangoClarityUpdateView,
)


def create_model_form_class(model, model_admin):
    url_name_prefix = f"djangoclarity-{model._meta.app_label}-{model._meta.model_name}"

    # Create the Meta class dynamically
    Meta = type(
        "Meta",
        (),
        {
            "model": model,
            "fields": model_admin.fields,
            "widgets": model_admin.widgets,
            "url_names": {
                "create_url_name": f"{url_name_prefix}-create",
                "delete_url_name": f"{url_name_prefix}-delete",
                "index_url_name": f"{url_name_prefix}-index",
                "update_url_name": f"{url_name_prefix}-update",
                # "index_redirect_url_name": f"{self.index_url_name}-redirect",
            },
        },
    )

    # Create the new ModelForm class
    attrs = {"Meta": Meta}
    form_class = type(
        f"DjangoClarity{model._meta.app_label}{model._meta.model_name}ModelForm",
        (ModelForm,),
        attrs,
    )

    return form_class


class ModelAdmin:
    fields = "__all__"
    readonly_fields = ()
    widgets = {}
    inlines = []
    # slug = None
    create_view_class = DjangoClarityCreateView
    delete_view_class = DjangoClarityDeleteView
    index_view_class = DjangoClarityListView
    update_view_class = DjangoClarityUpdateView


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

        # Go through each registered model
        for model, model_admin in self._registry.items():
            formsets = model_admin.inlines
            create_view_class = model_admin.create_view_class
            delete_view_class = model_admin.delete_view_class
            index_view_class = model_admin.index_view_class
            update_view_class = model_admin.update_view_class
            form = create_model_form_class(model, model_admin)
            url_prefix = f"{model._meta.app_label}/{model._meta.model_name}"
            # url_prefix = (
            #     f"djangoclarity/{model._meta.app_label}/{model._meta.model_name}"
            # )

            urlpatterns += [
                # Main paths
                path(
                    f"{url_prefix}/add/",
                    create_view_class.as_view(
                        form_class=form, formsets=formsets, namespace=self._namespace
                    ),
                    name=form.Meta.url_names["create_url_name"],
                ),
                path(
                    f"{url_prefix}/<int:pk>/delete/",
                    delete_view_class.as_view(
                        form_class=form, formsets=formsets, namespace=self._namespace
                    ),
                    name=form.Meta.url_names["delete_url_name"],
                ),
                path(
                    f"{url_prefix}/",
                    index_view_class.as_view(
                        form_class=form, formsets=formsets, namespace=self._namespace
                    ),
                    name=form.Meta.url_names["index_url_name"],
                ),
                path(
                    f"{url_prefix}/<int:pk>/change/",
                    update_view_class.as_view(
                        form_class=form, formsets=formsets, namespace=self._namespace
                    ),
                    name=form.Meta.url_names["update_url_name"],
                ),
                # Redirect paths
                path(
                    f"{url_prefix}/index/",
                    RedirectView.as_view(
                        pattern_name=form.Meta.url_names["index_url_name"]
                    ),
                ),
                path(
                    f"{url_prefix}/delete/",
                    RedirectView.as_view(
                        pattern_name=form.Meta.url_names["index_url_name"]
                    ),
                ),
                path(
                    f"{url_prefix}/change/",
                    RedirectView.as_view(
                        pattern_name=form.Meta.url_names["index_url_name"]
                    ),
                ),
                path(
                    f"{url_prefix}/<int:pk>/",
                    RedirectView.as_view(
                        pattern_name=form.Meta.url_names["update_url_name"]
                    ),
                ),
            ]

        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), self._namespace


site = AdminSite()
