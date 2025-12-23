from django import template

from ..dataclasses import ReadOnlyField

register = template.Library()


# Filter for accessing an entry in a dictionary
@register.filter
def get_item(d, key):
    return d.get(key)


# Inclusion tag for rendering a single form field
@register.inclusion_tag("djangoclarity/includes/render_field.html")
def djangoclarity_render_field(field):
    # Handle the widget attributes with form-control default
    widget_attrs = field.field.widget.attrs.copy()
    if "class" not in widget_attrs:
        widget_attrs["class"] = "form-control"

    return {"field": field, "widget_attrs": widget_attrs}


# Inclusion tag for rendering a single readonly form field
@register.inclusion_tag("djangoclarity/includes/render_readonly_field.html")
def djangoclarity_render_readonly_field(field):
    return {"field": field}


# Inclusion tag for rendering a form
@register.inclusion_tag("djangoclarity/includes/render_form.html")
def djangoclarity_render_form(
    form, form_layouts, form_layout_counter, is_formset_form=False
):
    form_layout = form_layouts[form_layout_counter]

    # Make a dictionary for faster lookup of the visible fields
    visible_fields_dict = {field.name: field for field in form.visible_fields()}

    # Get the desired fields
    visible_fields = []
    for layout_field_name in form_layout:
        # If it's a readonly field, then put in our custom dataclass.
        # Otherwise, put in the visible field object.
        if type(layout_field_name) is ReadOnlyField:
            # Grab the value of the field to display
            layout_field_name.value = getattr(form.instance, layout_field_name.name)
            visible_fields.append(layout_field_name)
        else:
            visible_fields.append(visible_fields_dict[layout_field_name])

    # Calculate the col_md_width for each field
    field_list = []
    visible_count = len(visible_fields)

    for idx, field in enumerate(visible_fields):
        readonly = type(field) is ReadOnlyField

        # Use the custom setting, if provided
        col_md_width = None
        if not readonly:
            col_md_width = field.field.widget.attrs.get("col_md_width")

        # Otherwise, figure it out
        if col_md_width is None:
            # Default: 12 if last in odd-length list, otherwise 6
            if visible_count % 2 == 1 and idx == visible_count - 1:
                col_md_width = "12"
            else:
                col_md_width = "6"

        field_list.append(
            {"field": field, "col_md_width": col_md_width, "readonly": readonly}
        )

    return {
        "visible_fields": field_list,
        "hidden_fields": list(form.hidden_fields()),
        "has_visible_fields": len(visible_fields) > 0,
        "model_verbose_name": (
            form._meta.model._meta.verbose_name
            if hasattr(form, "_meta") and hasattr(form._meta, "model")
            else ""
        ),
    }


# Inclusion tag for rendering a formset form
@register.inclusion_tag("djangoclarity/includes/render_formset_form.html")
def djangoclarity_render_formset_form(
    formset_form, formset_layouts, layout_counter, new_form=False
):
    return {
        "formset_form": formset_form,
        "formset_layouts": formset_layouts,
        "layout_counter": layout_counter,
        "new_form": new_form,
        "model_verbose_name": (
            formset_form._meta.model._meta.verbose_name
            if hasattr(formset_form, "_meta") and hasattr(formset_form._meta, "model")
            else ""
        ),
    }


# Inclusion tag for rendering a formset
@register.inclusion_tag("djangoclarity/includes/render_formset.html")
def djangoclarity_render_formset(formset, formset_layouts, formset_layout_counter):
    formset_forms = []
    for idx, formset_form in enumerate(formset):
        formset_forms.append(
            {
                "form": formset_form,
                "is_new": (
                    formset_form.instance.pk is None
                    if hasattr(formset_form, "instance")
                    else True
                ),
            }
        )

    return {
        "formset": formset,
        "formset_forms": formset_forms,
        "formset_layouts": formset_layouts,
        "formset_layout_counter": formset_layout_counter,
        "model_verbose_name": (
            formset.model._meta.verbose_name if hasattr(formset, "model") else ""
        ),
    }


# Inclusion tag for rendering an inline formset
@register.inclusion_tag("djangoclarity/includes/render_inline_formset.html")
def djangoclarity_render_inline_formset(formset):
    formset_forms = []
    for formset_form in formset:
        formset_forms.append(
            {
                "form": formset_form,
                "has_delete": hasattr(formset_form, "DELETE")
                and formset_form.DELETE is not None,
                "has_instance_pk": hasattr(formset_form, "instance")
                and formset_form.instance
                and formset_form.instance.pk is not None,
            }
        )

    verbose_name_plural = getattr(formset.form, "verbose_name_plural", None)
    if not verbose_name_plural:
        verbose_name_plural = (
            formset.model._meta.verbose_name_plural if hasattr(formset, "model") else ""
        )

    verbose_name = getattr(formset.form, "verbose_name", None)
    if not verbose_name:
        verbose_name = (
            formset.model._meta.verbose_name if hasattr(formset, "model") else ""
        )

    return {
        "formset": formset,
        "formset_forms": formset_forms,
        "verbose_name_plural": verbose_name_plural,
        "verbose_name": verbose_name,
        "model_verbose_name": (
            formset.model._meta.verbose_name if hasattr(formset, "model") else ""
        ),
    }
