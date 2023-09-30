import logging
from copy import copy
from enum import Enum
from typing import Union

from django.db import models
from django.db.models.fields import Field as DjangoModelField
from rest_framework import fields, serializers
from rest_framework.compat import postgres_fields
from rest_framework.serializers import ListSerializer, ModelSerializer, Serializer
from rest_framework.utils.serializer_helpers import BindingDict
from rest_framework.validators import UniqueValidator

from apps.sandbox_models.management.commands.filter_operations import FilterOperationsRegister

from rest_framework.fields import (  # NOQA # isort:skip
    BooleanField,
    CharField,
    ChoiceField,
    DateField,
    DateTimeField,
    DecimalField,
    DictField,
    DurationField,
    EmailField,
    Field,
    FileField,
    FilePathField,
    FloatField,
    HiddenField,
    HStoreField,
    IPAddressField,
    ImageField,
    IntegerField,
    JSONField,
    ListField,
    ModelField,
    MultipleChoiceField,
    ReadOnlyField,
    RegexField,
    SerializerMethodField,
    SlugField,
    TimeField,
    URLField,
    UUIDField,
)
from rest_framework.relations import (  # NOQA # isort:skip
    HyperlinkedIdentityField,
    HyperlinkedRelatedField,
    ManyRelatedField,
    PrimaryKeyRelatedField,
    RelatedField,
    SlugRelatedField,
    StringRelatedField,
)



logger = logging.getLogger(__name__)

ENTITY_SEPARATION = "."

NO_OPERATION_SUPPORTED = (ModelField, SerializerMethodField, PrimaryKeyRelatedField, SlugRelatedField, HiddenField)

SERIALIZER_TYPES = (Serializer, ListSerializer)

field_operation_mapper = {
    fields.IntegerField: [
        "greater_than",
        "less_than",
        "equal",
        "not_equal",
        "in_range",
        "not_in_range",
        "in",
        "not_in",
        "contains",
        "not_contains",
    ],
    fields.FloatField: [
        "greater_than",
        "less_than",
        "equal",
        "not_equal",
        "in_range",
        "not_in_range",
        "in",
        "not_in",
        "contains",
        "not_contains",
    ],
    fields.BooleanField: ["equal", "not_equal"],
    fields.CharField: ["equal", "not_equal"],
    fields.DateField: [
        "greater_than",
        "less_than",
        "equal",
        "not_equal",
        "in_range",
        "not_in_range",
        "in",
        "not_in",
        "contains",
        "not_contains",
    ],
    fields.DateTimeField: [
        "greater_than",
        "less_than",
        "equal",
        "not_equal",
        "in_range",
        "not_in_range",
        "in",
        "not_in",
        "contains",
        "not_contains",
    ],
    fields.DurationField: [
        "greater_than",
        "less_than",
        "equal",
        "not_equal",
        "in_range",
        "not_in_range",
        "in",
        "not_in",
        "contains",
        "not_contains",
    ],
    fields.EmailField: ["equal", "not_equal"],
    fields.FileField: ["equal", "not_equal"],
    fields.ImageField: ["equal", "not_equal"],
    fields.SlugField: ["equal", "not_equal"],
    fields.URLField: ["equal", "not_equal"],
    fields.UUIDField: ["equal", "not_equal"],
    fields.IPAddressField: ["equal", "not_equal"],
    fields.FilePathField: ["equal", "not_equal"],
    fields.DecimalField: [
        "greater_than",
        "less_than",
        "equal",
        "not_equal",
        "in_range",
        "not_in_range",
        "in",
        "not_in",
        "contains",
        "not_contains",
    ],
    fields.JSONField: ["equal", "not_equal"],
    fields.ChoiceField: ["equal", "not_equal"],
}


def extract_db_field(field_name, field, entity_separator=ENTITY_SEPARATION, field_prefix: str = None):
    """
    Args:
        field_name:
        field:
        entity_separator:
        field_prefix:

    Returns:

    """

    db_field = field.source.replace(".", entity_separator) if field.source else field_name
    return f"{field_prefix}{entity_separator}{db_field}" if field_prefix else db_field


def check_if_field_is_root_subentity(
    field_parts: list, field_type: serializers.Field | serializers.Serializer
) -> bool:
    """Small checker. Check case when requested filter is sub-entity without referencing to it child fields.

    Examples:
        We got serializer with sub entity

        class CountrySerializer(serializers.Serializer):
            id = IntegerField()
            code = CharField()
            name = CharField()

        class UserSerializer(serializers.Serializer):
            email = CharField()
            country = CountrySerializer()

        In case we got arguments like:

        field_parts = ['country']
        field_type = Serializer

        in this case we skip, because target filter got no sense without field of sub-entity
        Function will return True

        In case :
        field_parts = ['country', 'code']
        field_type = Serializer

        Function will return False. First part is Serializer, and second part is looking field of sub entity
    Args:
        field_parts(list):
        field_type:

    Returns:
        bool: if looking part is sub entity or part not
    """
    return True if len(field_parts) <= 1 and isinstance(field_type, (Serializer, ListSerializer)) else False


def process_filter_sub_serializers(
    field_path_parts: list,
    filter_dict: dict,
    serializer: serializers.Serializer | serializers.ListSerializer,
    nested_serializers_fields_store: dict,
    entity_separator: str = ENTITY_SEPARATION,
    field_prefix: str = None,
) -> bool:
    """

    Args:
        filter_dict (dict):
        field_path_parts (list):
        serializer (serializers.Serializer | serializers.ListSerializer):
        nested_serializers_fields_store (dict):
        field_prefix(str):
        entity_separator(str):

    Returns:
        bool:
    """

    if isinstance(serializer, serializers.ListSerializer):
        serializer_obj = serializer.child
    else:
        serializer_obj = serializer

    if check_if_field_is_root_subentity(field_path_parts, serializer_obj):
        return False

    nested_entity_db_path = extract_db_field(
        field_name=field_path_parts[0],
        field=serializer_obj,
        field_prefix=field_prefix,
        entity_separator=entity_separator,
    )
    filter_dict["field"] = field_path_parts[1]

    try:
        nested_serializers_fields_store[(nested_entity_db_path, serializer_obj)].append(filter_dict)
    except KeyError:
        nested_serializers_fields_store[(nested_entity_db_path, serializer_obj)] = [filter_dict]

    return True


def get_field_from_serializer_fields(
    field_name: str, serializer_fields_list: BindingDict
) -> serializers.Field | serializers.Serializer | None:
    """
    Args:
        field_name:
        serializer_fields_list:

    Returns:

    """

    try:
        serializer_field = serializer_fields_list[field_name]
    except KeyError:
        logger.info(f" No field {field_name} found in Serializer")
        return None

    if isinstance(serializer_field, NO_OPERATION_SUPPORTED):
        logger.info(f" Not supported operation for field {field_name} class of {serializer_field.__class__.__name__}")
        return None

    if serializer_field.write_only:
        # Skip fields that used only for creation
        return None

    return serializer_field


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
        return [str(value.value) for value in cls._value2member_map_.values()]

    @classmethod
    def is_list_type(cls, value):
        return value in [cls.IN, cls.NOT_IN]


def build_fields_filter(
    serializer: ModelSerializer, request_filters: list, field_prefix=None, entity_separator=ENTITY_SEPARATION
):
    """

    Args:
        serializer:
        request_filters:
        field_prefix:
        entity_separator:

    Returns:
        list:
    """
    serializer_fields = serializer.fields
    nested_serializers = {}
    db_fields_list = []

    for filter_dict in request_filters:
        ###
        # Take first part of str, and analyze it
        # Example "products.category.name" will split in ["products", "category.name"]
        # Where "products" is current looking field or nested serializer other part is path that need to resolved
        # in another context

        field_parts = filter_dict["field"].split(".", 1)

        field_type = get_field_from_serializer_fields(field_parts[0], serializer_fields)

        # Skip process if we found no field for filter
        if not field_type:
            continue

        if isinstance(field_type, SERIALIZER_TYPES):
            process_filter_sub_serializers(
                field_parts,
                filter_dict=filter_dict,
                serializer=field_type,
                nested_serializers_fields_store=nested_serializers,
                field_prefix=field_prefix,
                entity_separator=entity_separator,
            )
        else:
            db_field = extract_db_field(
                filter_dict["field"], field_type, field_prefix=field_prefix, entity_separator=entity_separator
            )
            operator_field, value_field = build_filter_fields(field_type=field_type, operator=filter_dict["operator"])
            filter_dict = {
                "database_field": db_field,
                "model_serializer_field": value_field,
                "operator": filter_dict["operator"],
                "value": filter_dict["value"],
            }
            db_fields_list.append(filter_dict)

    if nested_serializers:
        for nested_serializer, request_filters in nested_serializers.items():
            nested_fields = build_fields_filter(
                serializer=nested_serializer[1],
                request_filters=request_filters,
                field_prefix=nested_serializer[0],
                entity_separator=entity_separator,
            )
            db_fields_list.extend(nested_fields)

    return db_fields_list


def build_filter_fields(field_type: serializers.Field, operator: str):
    operator_field = serializers.ChoiceField(choices=OperatorEnum.values())

    if OperatorEnum.is_list_type(operator):
        if field_type.source:
            field_type.source = None
        value_field = field_type
        # value_field = serializers.ListField(child=field_type)
    else:
        value_field = field_type

    return operator_field, value_field


class FiterSerializer(serializers.Serializer):
    operator = serializers.CharField()
    model_serializer_field = serializers.CharField()
    value = serializers.CharField()
    database_field = serializers.CharField()


class FilterMapperSerializer(Serializer):
    entity_separator = "__"

    def __init__(self, request_filters, model_serializer):
        self.request_filters = request_filters
        self.model_serializer = model_serializer
        self.init_filters = build_fields_filter(
            request_filters=request_filters, serializer=model_serializer, entity_separator=self.entity_separator
        )

    def is_valid(self):
        pass

    def to_query(self, queryset):
        for model_filter in self.init_filters:
            print(model_filter["model_serializer_field"])

            model_field = model_filter["model_serializer_field"]

            # Validate operation against field
            accepted_operations = FilterOperationsRegister.get_default_operations(model_field)
            field_operation = model_filter["operator"]
            if field_operation not in accepted_operations:
                raise Exception("NOT SUPPORTED OPERATION")

            print(model_filter["database_field"])
            copy_field = copy(model_field)
            print(copy_field)
