from django.urls import path
from django.views.generic import RedirectView

from .views import (
    CreatorCreateView,
    CreatorDeleteView,
    CreatorIndexView,
    CreatorUpdateView,
)


def generate_creator_urls(
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
        create_view_class = CreatorCreateView
    if delete_view_class is None:
        delete_view_class = CreatorDeleteView
    if index_view_class is None:
        index_view_class = CreatorIndexView
    if update_view_class is None:
        update_view_class = CreatorUpdateView

    # Return the URLs for the Views
    return [
        # Main paths
        path(
            f"creator/{slug}/create/",
            create_view_class.as_view(slug=slug, form_class=form, formsets=formsets),
            name=f"creator-{slug}-create",
        ),
        path(
            f"creator/{slug}/delete/<int:pk>/",
            delete_view_class.as_view(slug=slug, form_class=form, formsets=formsets),
            name=f"creator-{slug}-delete",
        ),
        path(
            f"creator/{slug}/index/",
            index_view_class.as_view(slug=slug, form_class=form, formsets=formsets),
            name=f"creator-{slug}-index",
        ),
        path(
            f"creator/{slug}/update/<int:pk>/",
            update_view_class.as_view(slug=slug, form_class=form, formsets=formsets),
            name=f"creator-{slug}-update",
        ),
        # Redirect paths
        path(
            f"creator/{slug}/",
            RedirectView.as_view(pattern_name=f"creator-{slug}-index"),
            name=f"creator-{slug}-index-redirect",
        ),
        path(
            f"creator/{slug}/delete/",
            RedirectView.as_view(pattern_name=f"creator-{slug}-index"),
            name=f"creator-{slug}-index-redirect",
        ),
        path(
            f"creator/{slug}/update/",
            RedirectView.as_view(pattern_name=f"creator-{slug}-index"),
            name=f"creator-{slug}-index-redirect",
        ),
    ]
