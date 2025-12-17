from django import forms
from django.conf import settings
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.html import format_html
from django.utils.safestring import mark_safe


def thumbnail(image_path):
    return (
        '<img src="{}" class="imageupload-thumbnail" style="max-width: 100%;">'.format(
            image_path
        )
    )


class ThumbnailImageWidget(AdminFileWidget):
    template_with_initial = "%(input)s%(clear_template)s"
    clear_checkbox_label = "Delete Image"

    def __init__(self, attrs=None):
        # Set accept attribute to only allow jpeg and png files
        final_attrs = {"accept": "image/jpeg,image/png"}
        if attrs is not None:
            final_attrs.update(attrs)
        super().__init__(attrs=final_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        output = []
        if value:
            file_path = "{}{}".format(getattr(settings, "MEDIA_URL", "/media/"), value)
            try:
                output.append(
                    '<a target="_blank" href="{}" class="imageupload-thumbcontainer">{}</a>'.format(
                        file_path, thumbnail(file_path)
                    )
                )
            except IOError:
                output.append(
                    '{} <a target="_blank" href="{}">{}</a> <br />{} '.format(
                        "Currently:", file_path, value, "Change:"
                    )
                )
        else:
            output.append(
                thumbnail(
                    "{}admin_tools/images/missing_image.png".format(
                        getattr(settings, "STATIC_URL", "/static/")
                    )
                )
            )

        output.append(
            '<div class="imageupload-widget"><p class="file-upload">%s</p></div>'
            % super(ThumbnailImageWidget, self).render(name, value, attrs)
        )
        return mark_safe(
            '<div class="thumbnail-image-widget-container">%s</div>' % "".join(output)
        )


class RadioButtonsWidget(forms.RadioSelect):
    """
    A widget that renders a Bootstrap-style radio button group for use in forms.
    Mimics the appearance of b-form-radio-group with buttons.

    This widget creates a group of styled buttons that function as radio buttons.
    When a button is clicked, it becomes active and the corresponding radio input is selected.
    The buttons are styled using Bootstrap classes.
    """

    def __init__(self, attrs=None, choices=(), button_variant="outline-primary"):
        """
        Args:
            attrs: HTML attributes to apply to the widget
            choices: List of tuples (value, label) for the radio options
            button_variant: Bootstrap button style variant (default: "outline-primary")
        """
        self.button_variant = button_variant
        super(RadioButtonsWidget, self).__init__(attrs, choices)

    def render(self, name, value, attrs=None, renderer=None, choices=()):
        """
        Render the radio button group as HTML.

        This method creates:
        1. A container div with form-group class
        2. A button group containing styled labels for each option
        3. Hidden radio inputs that correspond to each button
        4. JavaScript to handle button clicks and update the active state

        Args:
            name: The name attribute for the form field
            value: The currently selected value
            attrs: Additional HTML attributes
            renderer: The form renderer (not used in this implementation)
            choices: List of tuples (value, label) for the radio options

        Returns:
            A marked safe HTML string containing the complete widget
        """
        if attrs is None:
            attrs = {}

        # Use provided choices or fall back to the widget's choices
        choices = list(choices) if choices else list(self.choices)

        # Create a unique ID for the radio group
        id_ = attrs.get("id")
        if not id_:
            id_ = "id_%s" % name

        # Start building the HTML output
        output = [
            '<div class="form-group">',
            f'  <div class="btn-group" role="group" aria-label="{name}">',
        ]

        # First, create all the visible button labels
        for i, (option_value, option_label) in enumerate(choices):
            radio_id = f"{id_}_{i}"
            is_selected = str(value) == str(option_value)

            # Add 'active' class if this option is currently selected
            active_class = " active" if is_selected else ""

            # Create the button label with Bootstrap styling
            # btn-outline-{variant} creates an outlined button style
            button = format_html(
                '<label for="{}" class="btn btn-{} btn-outline-{}{}">{}</label>',
                radio_id,
                self.button_variant,
                self.button_variant,
                active_class,
                option_label,
            )

            # Add the button to the output
            output.append(button)

        # Close the button group
        output.append("</div>")

        # Now add all the hidden radio inputs that correspond to each button
        for i, (option_value, option_label) in enumerate(choices):
            radio_id = f"{id_}_{i}"
            is_selected = str(value) == str(option_value)

            # Create a hidden radio input that will be controlled by the button clicks
            radio_input = format_html(
                '<input type="radio" name="{}" value="{}" id="{}" {} style="display:none;">',
                name,
                option_value,
                radio_id,
                "checked" if is_selected else "",
            )

            output.append(radio_input)

        output.append("</div>")

        # Add JavaScript to handle the button clicks and update the active state
        output.append(
            f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            // Find the radio group container and all button labels
            const radioGroup = document.querySelector('[name="{name}"]').closest('.form-group').querySelector('.btn-group');
            const buttons = radioGroup.querySelectorAll('label');

            // Add click event listener to each button
            buttons.forEach(function(button) {{
                button.addEventListener('click', function() {{
                    // Remove 'active' class from all buttons
                    buttons.forEach(function(btn) {{
                        btn.classList.remove('active');
                    }});

                    // Add 'active' class to the clicked button
                    this.classList.add('active');
                }});
            }});
        }});
        </script>
        """
        )

        # Return the complete HTML as a marked safe string
        return mark_safe("\n".join(output))
