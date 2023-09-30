from typing import Any, Union

from django.db import models
from django.db.models import Field, Q, QuerySet
from rest_framework import serializers
from rest_framework.utils.field_mapping import ClassLookupDict


class BaseFilterOperator:
    api_operation = None
    db_operator = None

    @classmethod
    def query_filter(cls, queryset: QuerySet, db_field, data: Any):
        raise NotImplementedError("Class filter operator should implement method query_filter()")


class BaseQueryFilterOperator(BaseFilterOperator):
    @classmethod
    def query_filter(cls, queryset: QuerySet, db_field, data: Any):
        queryset.filter({f"{db_field}{cls.db_operator}": data})
        return queryset


class BaseExcludeQueryFilterOperator(BaseFilterOperator):
    @classmethod
    def query_filter(cls, queryset: QuerySet, db_field, data: Any):
        queryset.filter({f"{db_field}{cls.db_operator}": data})
        return queryset


class EqualFilterOperation(BaseQueryFilterOperator):
    api_operation = "equal"
    db_operator = "__exact"


class NotEqualFilterOperation(BaseExcludeQueryFilterOperator):
    api_operation = "not_equal"
    db_operator = "__exact"


class InFilterOperator(BaseQueryFilterOperator):
    api_operation = "in"
    db_operator = "__in"


class NotInFilterOperator(BaseExcludeQueryFilterOperator):
    api_operation = "not_in"
    db_operator = "__in"


class ContainsFilterOperator(BaseQueryFilterOperator):
    api_operation = "contains"
    db_operator = "__contains"


class NotContainsFilterOperator(BaseQueryFilterOperator):
    api_operation = "not_contains"
    db_operator = "__contains"


class FilterOperationsRegister:
    operations = {
        "equal": EqualFilterOperation,
        "not_equal": NotEqualFilterOperation,
        "in": InFilterOperator,
        "not_in": NotInFilterOperator,
        "contains": ContainsFilterOperator,
        "not_contains": NotContainsFilterOperator,
    }

    serializer_field_operations = ClassLookupDict(
        {
            serializers.IntegerField: ("equal", "not_equal", "in", "not_in"),
            serializers.CharField: ("equal", "not_equal", "in", "not_in", "contains", "not_contains"),
        }
    )

    @classmethod
    def register_filter_operation(cls, lookup_cls, lookup_name=None):
        lookup_operation = lookup_name if lookup_name else lookup_cls.api_operation
        cls.operations[lookup_operation] = lookup_cls

    @classmethod
    def build_filter(cls, api_operation, db_field, data: Any):
        try:
            cls.operations[api_operation].query_filter(db_field=db_field, data=data)
        except KeyError:
            raise Exception(f"Not register api operation {api_operation}")

    @classmethod
    def get_default_operations(cls, field_instance):
        return cls.serializer_field_operations[field_instance]


@FilterOperationsRegister.register_filter_operation
class BaseFilterOperation:
    api_operation = "nearest"

    def query_filter(self, queryset, db_field, data):
        pass


# FilterOperationsRegister.register_default_operations(serializers.IntegerField, ('equal',))
# FilterOperationsRegister.extend_default_operations(serializers.IntegerField, ('equal',))
