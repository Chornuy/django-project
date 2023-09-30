from rest_framework import serializers


class DynamicFieldModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        context = kwargs.get("context")
        selected_fields = None

        if context:
            selected_fields = context.get("selected_fields", [])

        super().__init__(*args, **kwargs)

        if selected_fields:
            # Drop any fields that are not specified in the `fields` argument.
            remove_fields = set(self.fields.keys()) - set(selected_fields)
            remove_fields.discard("id")

            for field_name in remove_fields:
                self.fields.pop(field_name)
