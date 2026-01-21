from django import forms
from django.conf import settings
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.html import format_html


class ThumbnailImageWidget(AdminFileWidget):
    template_with_initial = "%(input)s%(clear_template)s"
    clear_checkbox_label = "Delete Image"

    def __init__(self, attrs=None):
        # Set accept attribute to only allow jpeg and png files
        final_attrs = {"accept": "image/jpeg,image/png"}
        if attrs is not None:
            final_attrs.update(attrs)
        super().__init__(attrs=final_attrs)

    def _thumbnail(self, image_path):
        return format_html(
            '<img src="{}" class="imageupload-thumbnail" style="max-width: 100%;">',
            image_path,
        )

    def render(self, name, value, attrs=None, renderer=None):
        # We want to wrap the thumbnail, so add in the beginning of the wrapper
        output = format_html('<div class="thumbnail-image-widget-container">')

        # Put in the thumbnail, if it exists
        if value:
            file_path = f"{getattr(settings, "MEDIA_URL", "/media/")}{value}"
            try:
                output += format_html(
                    (
                        '<a target="_blank" href="{}" '
                        'class="imageupload-thumbcontainer">{}</a>'
                    ),
                    file_path,
                    self._thumbnail(file_path),
                )
            except IOError:
                output += format_html("Unable to display image preview")

        # Add the Django File Upload widget below the thumbnail
        output += format_html(
            super(ThumbnailImageWidget, self).render(name, value, attrs)
        )

        # Finally, put in the ending of the wrapper
        output += format_html("</div>")

        # Since all HTML code has been formatted, this is safe to return as-is
        return output


class RadioButtonsWidget(forms.RadioSelect):
    """
    A widget that renders a Bootstrap-style radio button group for use in forms.
    Mimics the appearance of b-form-radio-group with buttons.

    This widget creates a group of styled buttons that function as radio buttons.
    When a button is clicked, it becomes active and the corresponding radio input
    is selected. The buttons are styled using Bootstrap classes.
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

        # Start the Bootstrap form group
        output = format_html('<div class="form-group">')

        # Start the Bootstrap button group
        output += format_html(
            '<div class="btn-group" role="group" aria-label="{}">', name
        )

        # First, create all the visible button labels
        for i, (option_value, option_label) in enumerate(choices):
            radio_id = f"{id_}_{i}"
            is_selected = str(value) == str(option_value)

            # Add 'active' class if this option is currently selected
            active_class = " active" if is_selected else ""

            # Add the button label with Bootstrap styling to the HTML.
            # `btn-outline-{variant}` creates an outlined button style.
            output += format_html(
                '<label for="{}" class="btn btn-{} btn-outline-{}{}">{}</label>',
                radio_id,
                self.button_variant,
                self.button_variant,
                active_class,
                option_label,
            )

        # Close the button group
        output += format_html("</div>")

        # Now add all the hidden radio inputs that correspond to each button
        for i, (option_value, option_label) in enumerate(choices):
            radio_id = f"{id_}_{i}"
            is_selected = str(value) == str(option_value)

            # Create a hidden radio input that will be controlled by the button clicks
            output += format_html(
                (
                    '<input type="radio" name="{}" value="{}" id="{}" {} '
                    'style="display:none;">'
                ),
                name,
                option_value,
                radio_id,
                "checked" if is_selected else "",
            )

        # Close the form group
        output += format_html("</div>")

        # Finally, add JavaScript to handle the button clicks
        # and update the active state
        js_script = """
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            // Find the radio group container and all button labels
            const radioGroup = document.querySelector('[name="{}"]')
                               .closest('.form-group')
                               .querySelector('.btn-group');
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
        output += format_html(js_script, name)

        # Since all HTML code has been formatted, this is safe to return as-is
        return output
