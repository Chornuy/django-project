import json
from enum import Enum
from typing import Any

import rest_framework_filters as filters
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_filters import AllValuesMultipleFilter, Filter, NumberFilter
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend, OrderingFilter
from rest_framework.serializers import ModelSerializer
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.utils import model_meta
from rest_framework.utils.field_mapping import ClassLookupDict
from rest_framework.viewsets import GenericViewSet, ReadOnlyModelViewSet

from apps.base.api.filters import JsonSelectFilter
from apps.base.api.serializers import DynamicFieldModelSerializer
from apps.base.api.views import DynamicFieldApiViewMixin
from apps.base.response import ActionResponse
from apps.users.api.views import UserViewSet

# import rest_framework_filters.backends.RestFrameworkFilterBackend
User = get_user_model()


class UserSerializer(DynamicFieldModelSerializer):
    class Meta:
        model = User
        fields = ["id", "is_active", "email", "is_verified", "date_joined", "last_login"]
        # fields = '__all__'
        # extra_kwargs = {
        #     'password': {'write_only': False, 'read_only': False}
        # }


class OperatorEnum(str, Enum):
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"

    EQUAL = "equal"
    NOT_EQUAL = "not_equal"

    IN_RANGE = "in_range"
    NOT_IN_RANGE = "not_in_range"

    IN = "in"
    NOT_IN = "not_in"

    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"

    # ANY = "any"
    # ALL = "all"
    # NONE = "none"

    @classmethod
    def values(cls):
        return cls._value2member_map_.values()


class EntityFilters:
    def __init__(self):
        self.entity_fields = []
        self.filters = []
        self.limit = []
        self.order = []


class UserListView(DynamicFieldApiViewMixin, ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [
        JsonSelectFilter,
    ]


class JsonFiltersEntity(BaseFilterBackend):
    filed_name = "filters"


operation_mapper = {"": {}}


class OperatorField(serializers.ChoiceField):
    default_error_messages = {"invalid_operator": _('"{input}" is not a valid operator.')}

    def to_internal_value(self, data):
        if data == "" and self.allow_blank:
            return ""

        try:
            return self.choice_strings_to_values[str(data)]
        except KeyError:
            self.fail("invalid_operator", input=data)


class ModelFields(serializers.CharField):
    def __init__(self, *args, **kwargs):
        self._model = kwargs.pop("model")

        super().__init__(**kwargs)


class DependendField(serializers.CharField):
    pass


class FilterOperator(serializers.Serializer):
    field = ModelFields(model=User)
    operator = OperatorField(allow_null=False, allow_blank=False, choices=OperatorEnum.values())
    value = DependendField(on_field="field")


operation_list = OperatorEnum.values()


class FilterOptionsSerializer(serializers.Serializer):
    field = serializers.CharField(required=True)
    operation = serializers.ChoiceField(required=True, choices=OperatorEnum.values())

    MAX_LIST_ELEMENTS = 10

    list_type_operators = [
        OperatorEnum.IN_RANGE.value,
        OperatorEnum.NOT_IN_RANGE,
        OperatorEnum.IN,
        OperatorEnum.NOT_IN,
    ]


list_type_operators = [OperatorEnum.IN_RANGE.value, OperatorEnum.NOT_IN_RANGE, OperatorEnum.IN, OperatorEnum.NOT_IN]


SUPPORTED_OPERATIONS_ON_FIELD = {
    serializers.IntegerField: [OperatorEnum.EQUAL.value, OperatorEnum.NOT_EQUAL.value],
    serializers.BooleanField: [OperatorEnum.EQUAL.value, OperatorEnum.NOT_EQUAL.value],
    serializers.EmailField: [OperatorEnum.EQUAL.value, OperatorEnum.NOT_EQUAL.value],
    serializers.CharField: [OperatorEnum.EQUAL],
    serializers.DateField: [OperatorEnum.EQUAL],
    serializers.DateTimeField: [OperatorEnum.EQUAL],
    serializers.DecimalField: [OperatorEnum.EQUAL],
    serializers.DurationField: [OperatorEnum.EQUAL],
    serializers.ModelField: [OperatorEnum.EQUAL],
    serializers.FileField: [OperatorEnum.EQUAL],
    serializers.FloatField: [OperatorEnum.EQUAL],
    serializers.ImageField: [OperatorEnum.EQUAL],
    serializers.SlugField: [OperatorEnum.EQUAL],
    serializers.TimeField: [OperatorEnum.EQUAL],
    serializers.URLField: [OperatorEnum.EQUAL],
    serializers.UUIDField: [OperatorEnum.EQUAL],
    serializers.IPAddressField: [OperatorEnum.EQUAL],
    serializers.FilePathField: [OperatorEnum.EQUAL],
}


class ModelOperationMetaSerializer:
    pass


def transform_to_query(field, operator_value, value):
    is_exclusion = True if operator_value in exclusion_operators else False
    django_orm_operator = operator_mapper[operator_value]
    operation_kwarg = {f"{field}{django_orm_operator}": value}

    if not is_exclusion:
        return Q(**operation_kwarg)
    else:
        return ~Q(**operation_kwarg)


class Command(BaseCommand):
    def handle(self, *args, **options):
        # users = User.objects.filter(email='chornuy.s@gmail.com').only('last_login', 'date_joined', 'email')
        # list_serializer = serializers.ListSerializer(instance=users, child=UserSerializer())
        # for user in list_serializer.data:
        #     print(user)
        # print(reverse('v1:user-register'))
        filter_backends = [
            JsonSelectFilter,
        ]

        query_params = {
            "filters": json.dumps([{"field": "email", "operator": "equal", "value": "chornuy.s@gmail.com"}]),
            "order": json.dumps([{"field": "", "value": "desc"}]),
            "search": json.dumps({"field": "", "value": ""}),
            "limit": 100,
        }

        # target_model = User
        # fields = target_model._meta.fields
        # primary_key = target_model._meta.pk.name
        # model_fields_name = [field.name for field in fields]
        # request_factory = APIRequestFactory()

        # users = User.objects.filter(email='chornuy.s@gmail.com').only('last_login', 'date_joined', 'email')
        # request = request_factory.get('', data=query_params, content_type='application/json')
        #
        # view = UserListView.as_view({
        #     'get': 'list'
        # })
        # response = view(request)
        # view.action_map = {
        #     "get": "list"
        # }
        # print(view.http_method_names)
        # # request = view.initialize_request(request)
        # response = view.dispatch(request)
        # view.request = request
        # response = view.list(request, [], {})
        user_fields = UserSerializer().get_fields()

        print(operation_list)

        fields_value = {"email": 123123, "is_active": "true", "id": "12", "password": "123123123", "hui": "pizda"}

        filters_data = [
            {"field": "email", "operator": "equal", "value": "chornuy.s@gmail.com"},
            {"field": "email", "operator": "equal", "value": "vasya"},
            {"field": "is_verified", "operator": "equal", "value": "t"},
        ]

        filters_query = []
        fields = list(user_fields.keys())
        model_fields = serializers.ChoiceField(choices=fields)
        field_mappers = ClassLookupDict(ModelSerializer.serializer_field_mapping)
        django_filter_list = {}

        for filter_dict in filters_data:
            field_name = model_fields.to_internal_value(filter_dict["field"])
            print(field_name)

            field = user_fields[field_name]
            supported_operations = SUPPORTED_OPERATIONS_ON_FIELD.get(type(field))

            operator_value = serializers.ChoiceField(choices=supported_operations).to_internal_value(
                filter_dict["operator"]
            )

            value_is_list = True if operator_value in list_type_operators else False

            if value_is_list:
                value_field = serializers.ListField(child=field)
            else:
                value_field = field

            value = value_field.to_internal_value(filter_dict["value"])
            django_orm_filter = transform_to_query(field_name, operator_value, value)
            django_filter_list[django_orm_filter] = value
            print(value)

        users = User.objects.filter(*django_filter_list)
        print(users.query)
        for user in users:
            print(user)

        # for filter_dict in filters:
        #
        #     try:
        #         field_obj = user_fields[field_name]
        #     except KeyError:
        #         continue
        #
        #     if not field_obj.write_only:
        #         type(field_obj)
        #         filter_value = user_fields[field_name].to_internal_value(field_value)
        #         print(filter_value)

        # filters_serializer = FilterOptionsSerializer(data=filters, many=True)
        # filters_serializer.is_valid()
        # print(filters_serializer.data)

        # print(user_fields)
        # print(user_fields["is_active"].run_validation("true"))
        #
        # model = getattr(UserSerializer.Meta, 'model')
        # info = model_meta.get_field_info(model)
        # print(info)

        # queryset = User.objects.all()
        #
        #
        # for backend in filter_backends:
        #     queryset = backend().filter_queryset(request=request, queryset=queryset, view=view)
        # print(queryset.query)
        # user = queryset
        # user_serializer = UserSerializer(user, many=True)
        # print(user_serializer.data)
        # for user in user_serializer.data:
        #     print(user)
        # print(model_fields_name)
        # for field in fields:
        #
        #     print(field)
        #     print(type(field))
        #
        # print(UserFilter().get_filters())
        # users = User.objects.filter(email='chornuy.s@gmail.com').only('last_login', 'date_joined', 'email')
        # user_list_serializer = UserSerializer(instance=users, many=True)
        # for user in user_list_serializer.data:
        #     print(user)

        # print(list_serializer.data)
        # users_serializer = UserSerializer(instance=users)
        # print(users_serializer.fields)
        # for user in users_data:
        #     print(user)
