# from django.db.models.base import ModelBase
from django.forms import ModelForm
from django.urls import path
from django.views.generic import RedirectView

from .options import ModelAdmin
from .views import (
    DjangoClarityCreateView,
    DjangoClarityDeleteView,
    DjangoClarityListView,
    DjangoClarityUpdateView,
)


class AdminSite:
    def __init__(self):
        self._registry = {}

    def register(self, model, admin_class=None):
        admin_class = admin_class or ModelAdmin
        self._registry[model] = admin_class(model)

    def create_model_form_class(self, model, admin_class, slug):
        Meta = type(
            "Meta",
            (),
            {
                "model": model,
                "fields": getattr(admin_class, "fields", "__all__"),
                "widgets": getattr(admin_class, "widgets", {}),
                "reverse_names": {
                    "create": f"djangoclarity-{slug}-create",
                    "delete": f"djangoclarity-{slug}-delete",
                    "index": f"djangoclarity-{slug}-index",
                    "update": f"djangoclarity-{slug}-update",
                },
            },
        )

        # Create a custom __init__ method to help deal with read-only fields
        # TODO
        # def __init__(self, *args, **kwargs):
        #     super_class = type("ModelFormSuperClass", (ModelForm,), {"Meta": Meta})
        #     super_class().__init__(*args, **kwargs)
        #     if self.instance and hasattr(admin_class, "readonly_fields"):
        #         for readonly_field in admin_class.readonly_fields:
        #             self.fields[readonly_field].initial = getattr(
        #                 self.instance, readonly_field
        #             )

        # attrs = {"Meta": Meta, "__init__": __init__}
        attrs = {"Meta": Meta}

        # Create the new model form class
        model_form_class = type(f"{model.__name__}Form", (ModelForm,), attrs)

        # Add any read-only fields in
        # TODO
        # if hasattr(admin_class, "readonly_fields"):
        #     for readonly_field in admin_class.readonly_fields:
        #         setattr(
        #             model_form_class,
        #             readonly_field,
        #             getattr(model, readonly_field).field(disabled=True),
        #         )

        # Return the class
        return model_form_class

    def get_urls(self):
        urlpatterns = []

        for model, admin_class in self._registry.items():
            formsets = getattr(admin_class, "inlines", [])
            create_view_class = getattr(
                admin_class, "create_view_class", DjangoClarityCreateView
            )
            delete_view_class = getattr(
                admin_class, "delete_view_class", DjangoClarityDeleteView
            )
            index_view_class = getattr(
                admin_class, "index_view_class", DjangoClarityListView
            )
            update_view_class = getattr(
                admin_class, "update_view_class", DjangoClarityUpdateView
            )
            app_label = model._meta.app_label
            slug = admin_class.get_slug()
            form = self.create_model_form_class(model, admin_class, slug)

            urlpatterns += [
                # Main paths
                path(
                    f"{app_label}/{slug}/add/",
                    create_view_class.as_view(
                        slug=slug, form_class=form, formsets=formsets
                    ),
                    # name=f"djangoclarity-{slug}-create",
                    name=form.Meta.reverse_names["create"],
                ),
                path(
                    f"{app_label}/{slug}/<int:pk>/delete/",
                    delete_view_class.as_view(
                        slug=slug, form_class=form, formsets=formsets
                    ),
                    # name=f"djangoclarity-{slug}-delete",
                    name=form.Meta.reverse_names["delete"],
                ),
                path(
                    f"{app_label}/{slug}/",
                    index_view_class.as_view(
                        slug=slug, form_class=form, formsets=formsets
                    ),
                    # name=f"djangoclarity-{slug}-index",
                    name=form.Meta.reverse_names["index"],
                ),
                path(
                    f"{app_label}/{slug}/<int:pk>/change/",
                    update_view_class.as_view(
                        slug=slug, form_class=form, formsets=formsets
                    ),
                    # name=f"djangoclarity-{slug}-update",
                    name=form.Meta.reverse_names["update"],
                ),
                # Redirect paths
                path(
                    f"{app_label}/{slug}/index/",
                    RedirectView.as_view(pattern_name=f"djangoclarity-{slug}-index"),
                    # name=f"djangoclarity-{slug}-index-redirect",
                ),
                path(
                    f"{app_label}/{slug}/delete/",
                    RedirectView.as_view(pattern_name=f"djangoclarity-{slug}-index"),
                    # name=f"djangoclarity-{slug}-delete-redirect",
                ),
                path(
                    f"{app_label}/{slug}/change/",
                    RedirectView.as_view(pattern_name=f"djangoclarity-{slug}-index"),
                    # name=f"djangoclarity-{slug}-index-redirect",
                ),
                path(
                    f"{app_label}/{slug}/<int:pk>/",
                    RedirectView.as_view(pattern_name=f"djangoclarity-{slug}-update"),
                    # name=f"djangoclarity-{slug}-index-redirect",
                ),
            ]

        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), "djangoclarity"


site = AdminSite()


def generate_djangoclarity_urls(
    slug,
    form,
    formsets=None,
    create_view_class=None,
    delete_view_class=None,
    index_view_class=None,
    update_view_class=None,
):
    # Set defaults
    if formsets is None:
        formsets = []
    if create_view_class is None:
        create_view_class = DjangoClarityCreateView
    if delete_view_class is None:
        delete_view_class = DjangoClarityDeleteView
    if index_view_class is None:
        index_view_class = DjangoClarityListView
    if update_view_class is None:
        update_view_class = DjangoClarityUpdateView

    app_label = form.Meta.model._meta.app_label

    # Return the URLs for the Views
    return [
        # Main paths
        path(
            f"djangoclarity/{app_label}/{slug}/add/",
            create_view_class.as_view(slug=slug, form_class=form, formsets=formsets),
            name=f"djangoclarity-{slug}-create",
        ),
        path(
            f"djangoclarity/{app_label}/{slug}/<int:pk>/delete/",
            delete_view_class.as_view(slug=slug, form_class=form, formsets=formsets),
            name=f"djangoclarity-{slug}-delete",
        ),
        path(
            f"djangoclarity/{app_label}/{slug}/",
            index_view_class.as_view(slug=slug, form_class=form, formsets=formsets),
            name=f"djangoclarity-{slug}-index",
        ),
        path(
            f"djangoclarity/{app_label}/{slug}/<int:pk>/change/",
            update_view_class.as_view(slug=slug, form_class=form, formsets=formsets),
            name=f"djangoclarity-{slug}-update",
        ),
        # Redirect paths
        path(
            f"djangoclarity/{app_label}/{slug}/index/",
            RedirectView.as_view(pattern_name=f"djangoclarity-{slug}-index"),
            # name=f"djangoclarity-{slug}-index-redirect",
        ),
        path(
            f"djangoclarity/{app_label}/{slug}/delete/",
            RedirectView.as_view(pattern_name=f"djangoclarity-{slug}-index"),
            # name=f"djangoclarity-{slug}-delete-redirect",
        ),
        path(
            f"djangoclarity/{app_label}/{slug}/change/",
            RedirectView.as_view(pattern_name=f"djangoclarity-{slug}-index"),
            # name=f"djangoclarity-{slug}-index-redirect",
        ),
        path(
            f"djangoclarity/{app_label}/{slug}/<int:pk>/",
            RedirectView.as_view(pattern_name=f"djangoclarity-{slug}-update"),
            # name=f"djangoclarity-{slug}-index-redirect",
        ),
    ]
