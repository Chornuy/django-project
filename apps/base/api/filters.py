import json
from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.template import loader
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _
from rest_framework.compat import coreapi, coreschema
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend


class JsonFilterBase:
    expected_type = list
    expected_value = str
    field_param = None

    def is_valid_data(self, data: Any) -> bool:
        """

        Args:
            data:

        Raises:

        Returns:

        """
        if not isinstance(data, self.expected_type):
            raise ValidationError(_(f"Expected {self.expected_type.__name__} for query {self.field_param}"))

        if not all(isinstance(elem, self.expected_value) for elem in data):
            raise ValidationError(_(f"Expected {self.expected_value.__name__} for value in query {self.field_param}"))
        return True

    def parse_query_data(self, data: str) -> dict:
        """Transform data from query that decoded in Json format

        Args:
            data:

        Returns:

        """

        try:
            data = json.loads(data)
        except ValueError:
            raise ValidationError(_("Wrong format for query param, expected json decoded data"))

        self.is_valid_data(data)

        return data


class JsonSelectFilter(JsonFilterBase, BaseFilterBackend):
    select_param = "fields"

    select_title = _("Select")
    select_description = _("Which field to use in response.")
    template = "base/filters/json_select.html"

    def get_default_valid_fields(self, queryset, view, context={}):
        # If `ordering_fields` is not specified, then we determine a default
        # based on the serializer class, if one exists on the view.
        if hasattr(view, "get_serializer_class"):
            try:
                serializer_class = view.get_serializer_class()
            except AssertionError:
                # Raised by the default implementation if
                # no serializer_class was found
                serializer_class = None
        else:
            serializer_class = getattr(view, "serializer_class", None)

        if serializer_class is None:
            msg = (
                "Cannot use %s on a view which does not have either a "
                "'serializer_class', an overriding 'get_serializer_class' "
                "or 'ordering_fields' attribute."
            )
            raise ImproperlyConfigured(msg % self.__class__.__name__)

        model_class = queryset.model
        model_property_names = [
            # 'pk' is a property added in Django's Model class, however it is valid for ordering.
            attr
            for attr in dir(model_class)
            if isinstance(getattr(model_class, attr), property) and attr != "pk"
        ]

        return [
            (field.source.replace(".", "__") or field_name, field.label)
            for field_name, field in serializer_class(context=context).fields.items()
            if (
                not getattr(field, "write_only", False)
                and not field.source == "*"
                and field.source not in model_property_names
            )
        ]

    def remove_invalid_fields(self, queryset, fields, view, request):
        default_fields = self.get_default_valid_fields(queryset, view, {"request": request})
        valid_fields = []

        for field_name, __ in default_fields:
            if field_name in fields:
                valid_fields.append(field_name)

        return valid_fields

    def get_fields(self, request, queryset, view):
        """ """

        params = request.query_params.get(self.select_param, None)

        if params is None:
            return None

        fields = self.parse_query_data(params)

        selected_fields = self.remove_invalid_fields(queryset, fields, view, request)

        if selected_fields:
            return selected_fields

        return None

    def filter_queryset(self, request, queryset, view):
        selected_fields = self.get_fields(request, queryset, view)
        view.selected_fields = selected_fields

        if selected_fields:
            return queryset.only(*selected_fields)

        return queryset

    def get_template_context(self, request, queryset, view):
        current = self.get_fields(request, queryset, view)
        current = None if not current else current[0]
        options = []
        context = {
            "request": request,
            "current": current,
            "param": self.select_param,
        }
        for key, label in self.get_default_valid_fields(queryset, view, {"request": request}):
            options.append((key, "{} - {}".format(label, _("ascending"))))
            options.append(("-" + key, "{} - {}".format(label, _("descending"))))
        context["options"] = options
        return context

    def to_html(self, request, queryset, view):
        template = loader.get_template(self.template)
        context = self.get_template_context(request, queryset, view)
        return template.render(context)

    def get_schema_fields(self, view):
        assert coreapi is not None, "coreapi must be installed to use `get_schema_fields()`"
        assert coreschema is not None, "coreschema must be installed to use `get_schema_fields()`"
        return [
            coreapi.Field(
                name=self.select_param,
                required=False,
                location="query",
                schema=coreschema.String(
                    title=force_str(self.select_title), description=force_str(self.select_description)
                ),
            )
        ]

    def get_schema_operation_parameters(self, view):
        return [
            {
                "name": self.select_param,
                "required": False,
                "in": "query",
                "description": force_str(self.select_description),
                "schema": {
                    "type": "string",
                },
            },
        ]
