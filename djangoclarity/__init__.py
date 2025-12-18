from django.urls import path
from django.views.generic import RedirectView

from .registration import InlineModelAdmin, ModelAdmin, site
from .views import (
    DjangoClarityCreateView,
    DjangoClarityDeleteView,
    DjangoClarityListView,
    DjangoClarityUpdateView,
)

__all__ = [
    "site",
    "ModelAdmin",
    "InlineModelAdmin",
]


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
