class ModelAdmin:
    def __init__(self, model):
        self.model = model
        # self.form

    def get_slug(self):
        return getattr(self, "slug", self.model._meta.model_name)


class InlineModelAdmin:
    pass


# def register(admin_class):
