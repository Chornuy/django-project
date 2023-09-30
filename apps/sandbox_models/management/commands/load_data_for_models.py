import json
import logging
from collections import OrderedDict
from collections.abc import Sequence
from copy import copy, deepcopy
from enum import Enum
from typing import Any, List, Union

import factory
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import models
from django.utils.translation import gettext_lazy as _
from factory import post_generation
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice
from faker.providers import DynamicProvider
from rest_framework import fields, serializers
from rest_framework.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    DateField,
    DateTimeField,
    DurationField,
    EmailField,
    FileField,
    FilePathField,
    FloatField,
    ImageField,
    IntegerField,
    IPAddressField,
    SerializerMethodField,
    SlugField,
    TimeField,
    URLField,
    UUIDField,
    flatten_choices_dict,
    to_choices_dict,
)
from rest_framework.relations import HyperlinkedIdentityField, PrimaryKeyRelatedField, SlugRelatedField
from rest_framework.serializers import ListSerializer, ModelSerializer, Serializer
from rest_framework.utils.field_mapping import ClassLookupDict
from rest_framework.utils.serializer_helpers import BindingDict
from rest_framework.validators import UniqueValidator

from apps.sandbox_models.api.serializers import ProductSerializer
from apps.sandbox_models.management.commands.field_operation import (
    FIELDS_OPERATION_MAPPER,
    FIELDS_OPERATION_MAPPER_OPERATOR_LIST,
    NO_OPERATION_SUPPORTED,
    SERIALIZER_TYPES,
    OperatorEnum,
)
from apps.sandbox_models.management.commands.filter_operations import BaseFilterOperation, FilterOperationsRegister
from apps.sandbox_models.management.commands.filter_serializer import FilterMapperSerializer
from apps.sandbox_models.models import Category, Product, Tag
from apps.test_utils.factories import UserFactory

logger = logging.getLogger(__name__)


class ProductCategories(models.TextChoices):
    PHONE = "phone", _("Phone")


class PhoneTags(models.TextChoices):
    android = "android", _("Android Phone")
    smartphone = "smartphone", _("Smartphone")


class CategoryFactory(DjangoModelFactory):
    # name = factory.Faker('word')
    name = FuzzyChoice(ProductCategories)

    class Meta:
        model = Category
        django_get_or_create = ("name",)


class TagFactory(DjangoModelFactory):
    name = FuzzyChoice(PhoneTags)

    class Meta:
        model = Tag
        django_get_or_create = ("name",)


class ProductFactory(DjangoModelFactory):
    name = factory.Faker("sentence")
    created = factory.Faker("date_object")
    category = factory.SubFactory(CategoryFactory)

    @factory.post_generation
    def tags(self, create: bool, extracted: Sequence[Any], **kwargs):
        tags = extracted if extracted else TagFactory.create_batch(size=2, name=FuzzyChoice(PhoneTags))
        for tag in tags:
            self.tags.add(tag)

    @factory.post_generation
    def created_by(self, create: bool, extracted: Sequence[Any], **kwargs):
        user = extracted if extracted else UserFactory()
        self.created_by = user

    class Meta:
        model = Product
        django_get_or_create = ("name",)


class ElectronicsProductFactory(ProductFactory):
    category = factory.SubFactory(CategoryFactory(name="electronics"))


def clear_products():
    Product.objects.all().delete()
    Tag.objects.all().delete()
    Category.objects.all().delete()


def generate_products():
    user = UserFactory()

    category = CategoryFactory.create()
    print(category.name)
    print(len(Category.objects.all()))
    # tag = TagsFactory()
    #
    # print(tag.name)
    products = ProductFactory.create_batch(size=20, created_by=user)

    ElectronicsProductFactory.create_batch(size=30)
    print(len(Product.objects.all()))

    print(f"TAGS IN DB: {len(Tag.objects.all())}")
    # user.delete()
    # self.clear()
    print(len(Category.objects.all()))


ENTITY_SEPARATION = "."


class Field:
    def __init__(self, field_type, accepted_operations, field_name):
        self.field_type = field_type
        self.operations = accepted_operations
        self.field_name = field_name


class ApiTypeField(str, Enum):
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    CHARACTER = "chartype"
    DATETIME = "datetime"
    DATE = "date"
    DECIMAL = "decimal"
    DURATION = "duration"
    EMAIL = "email"
    FILE = "file"
    IMAGE = "image"
    SLUG = "slug"
    TIME = "time"
    URL = "url"
    UIID = "uiid"
    IPADDRESS = "ipaddress"
    FILEPATH = "filepath"


DJANGO_FIELD_TYPE_API_MAPPER = {
    IntegerField: ApiTypeField.INTEGER.value,
    BooleanField: ApiTypeField.BOOLEAN.value,
    CharField: ApiTypeField.CHARACTER.value,
    DateField: ApiTypeField.DATE.value,
    DateTimeField: ApiTypeField.DATETIME.value,
    DurationField: ApiTypeField.DURATION.value,
    EmailField: ApiTypeField.EMAIL.value,
    FileField: ApiTypeField.FILE.value,
    FloatField: ApiTypeField.FLOAT.value,
    ImageField: ApiTypeField.IMAGE.value,
    SlugField: ApiTypeField.SLUG.value,
    TimeField: ApiTypeField.TIME.value,
    URLField: ApiTypeField.URL.value,
    UUIDField: ApiTypeField.UIID.value,
    IPAddressField: ApiTypeField.IPADDRESS.value,
    FilePathField: ApiTypeField.FILEPATH.value,
}


def convert_type_to_api(field_type):
    return DJANGO_FIELD_TYPE_API_MAPPER[field_type]


def unpack_serializer_fields(serializer, prefix: str = None) -> list:
    accepted_fields = []
    fields = serializer.get_fields()

    for field_name, field_type in fields.items():
        if isinstance(field_type, Serializer):
            sub_entity_fields = unpack_serializer_fields(field_type, prefix=f"{field_name}{ENTITY_SEPARATION}")
            accepted_fields.extend(sub_entity_fields)
        elif isinstance(field_type, ListSerializer):
            origin_serializer = field_type.child
            sub_entity_fields = unpack_serializer_fields(origin_serializer, prefix=f"{field_name}{ENTITY_SEPARATION}")
            accepted_fields.extend(sub_entity_fields)
        else:
            field_path = f"{prefix}{field_name}" if prefix else field_name
            accepted_fields.append(field_path)

    return accepted_fields


serializer_related_field = PrimaryKeyRelatedField
serializer_related_to_field = SlugRelatedField
serializer_url_field = HyperlinkedIdentityField
serializer_choice_field = ChoiceField


def get_operations_serializer_fields(serializer, prefix: str = None) -> list:
    accepted_fields = []
    fields = serializer.get_fields()

    for field_name, field_type in fields.items():
        if isinstance(field_type, NO_OPERATION_SUPPORTED):
            continue

        if isinstance(field_type, Serializer):
            sub_entity_fields = get_operations_serializer_fields(field_type, prefix=f"{field_name}{ENTITY_SEPARATION}")
            accepted_fields.extend(sub_entity_fields)
        elif isinstance(field_type, ListSerializer):
            origin_serializer = field_type.child
            sub_entity_fields = get_operations_serializer_fields(
                origin_serializer, prefix=f"{field_name}{ENTITY_SEPARATION}"
            )
            accepted_fields.extend(sub_entity_fields)
        else:
            field_path = f"{prefix}{field_name}" if prefix else field_name
            operator_obj = FIELDS_OPERATION_MAPPER[field_type.__class__]()

            api_struct = operator_obj.to_api_response(field_path)
            accepted_fields.append(api_struct)

    return accepted_fields


def build_filters_queryset(serializer, prefix: str = None):
    accepted_fields = []
    fields = serializer.get_fields()

    for field_name, field_type in fields.items():
        if isinstance(field_type, NO_OPERATION_SUPPORTED):
            continue

        if isinstance(field_type, Serializer):
            sub_entity_fields = get_operations_serializer_fields(field_type, prefix=f"{field_name}{ENTITY_SEPARATION}")
            accepted_fields.extend(sub_entity_fields)
        elif isinstance(field_type, ListSerializer):
            origin_serializer = field_type.child
            sub_entity_fields = get_operations_serializer_fields(
                origin_serializer, prefix=f"{field_name}{ENTITY_SEPARATION}"
            )
            accepted_fields.extend(sub_entity_fields)
        else:
            field_path = f"{prefix}{field_name}" if prefix else field_name
            operator_obj = FIELDS_OPERATION_MAPPER[field_type.__class__]()

            api_struct = operator_obj.to_api_response(field_path)
            accepted_fields.append(api_struct)

    return accepted_fields


def filter_existing_fields(filters: list, model_serializer_fields):
    exits_fields = []

    for filter_field in filters:
        filter_field_name = filter_field.get("field_name")

        if filter_field_name in model_serializer_fields.keys():
            exits_fields.append(filter_field_name)

    return exits_fields


def get_filter_fields(serializer, prefix: str = None):
    accepted_fields = []
    fields = serializer.get_fields()

    for field_name, field_type in fields.items():
        if isinstance(field_type, NO_OPERATION_SUPPORTED):
            continue

        if isinstance(field_type, Serializer):
            sub_entity_fields = get_filter_fields(field_type, prefix=f"{field_name}{ENTITY_SEPARATION}")
            accepted_fields.extend(sub_entity_fields)
        elif isinstance(field_type, ListSerializer):
            origin_serializer = field_type.child
            sub_entity_fields = get_filter_fields(origin_serializer, prefix=f"{field_name}{ENTITY_SEPARATION}")
            accepted_fields.extend(sub_entity_fields)
        else:
            field_path = f"{prefix}{field_name}" if prefix else field_name
            accepted_fields.append(field_path)

    return accepted_fields


ENTITY_SEPARATION = "."


def get_serializer_fields(serializer, entity_prefix=None):
    model_class = serializer.Meta.model

    model_property_names = [
        attr for attr in dir(model_class) if isinstance(getattr(model_class, attr), property) and attr != "pk"
    ]

    serializer_fields = []

    for field_name, field in serializer.fields.items():
        if getattr(field, "write_only", False):
            continue

        if field.source in model_property_names:
            continue

        if isinstance(field, Serializer):
            fields = get_serializer_fields(field, entity_prefix=field_name)
            serializer_fields.extend(fields)
            continue

        if isinstance(field, ListSerializer) and isinstance(field.child, Serializer):
            fields = get_serializer_fields(field.child, entity_prefix=field_name)
            serializer_fields.extend(fields)

        if field.source == "*":
            continue
        else:
            # serializer_fields.append((field.source.replace('.', '__') or field_name, field.label))

            field_name = f"{entity_prefix}{ENTITY_SEPARATION}{field_name}" if entity_prefix else field_name
            serializer_fields.append((field_name, field))

    return serializer_fields


ACCEPTED_TYPES = (str, int, float, list, tuple, set)


class MixedTypesField(CharField):
    def __init__(self, **kwargs):
        self.field_types = kwargs.pop("field_types", None)
        if not self.field_types:
            self.field_types = ACCEPTED_TYPES

        super().__init__(**kwargs)

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        if not isinstance(data, self.field_types):
            self.fail("invalid")

        return data


class FilterSerializer(serializers.Serializer):
    field = serializers.CharField(required=True, min_length=0, max_length=255)
    operator = serializers.ChoiceField(choices=OperatorEnum.values())
    value = MixedTypesField(required=True)


def filters_to_field(filters_data, serializer):
    fields = serializer.fields
    nested_fields = {}
    db_fields = []
    source = serializer.source

    for filter_obj in filters_data:
        field_name = filter_obj["field"]
        filter_operator = filter_obj["operator"]
        filter_value = filter_obj["value"]
        # print(filter_obj["field"])
        field_name = field_name.rsplit(".", 1)

        try:
            field = fields[field_name[0]]
        except KeyError:
            continue

        if len(field_name) > 1:
            if isinstance(field, Serializer):
                try:
                    nested_fields[field].append(field_name[1])
                except KeyError:
                    nested_fields[field] = [field_name[1]]

            elif isinstance(field, ListSerializer):
                child_serializer = field.child
                try:
                    nested_fields[child_serializer].append(field_name[1])
                except KeyError:
                    nested_fields[child_serializer] = [field_name[1]]
        else:
            db_field = f"{source}.{field.source}" if source else field.source
            db_fields.append(db_field)

        # if nested_fields:
        #     for serializer, fields


class CountrySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    code = serializers.CharField()
    name = serializers.CharField()


class AddressesSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    geolocation = serializers.CharField()
    country = CountrySerializer()


class AccountsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    addresses = AddressesSerializer(many=True)
    accounts = AccountsSerializer(many=True)


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


class OperatorField(serializers.ChoiceField):
    def __init__(self, choices, *args, **kwargs):
        filed_mapper = kwargs.pop("mapper")
        self.choices = choices
        self.html_cutoff = kwargs.pop("html_cutoff", self.html_cutoff)
        self.html_cutoff_text = kwargs.pop("html_cutoff_text", self.html_cutoff_text)

        self.allow_blank = kwargs.pop("allow_blank", False)

        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if data == "" and self.allow_blank:
            return ""

        try:
            return self.choice_strings_to_values[str(data)]
        except KeyError:
            self.fail("invalid_choice", input=data)

    def to_representation(self, value):
        if value in ("", None):
            return value
        return self.choice_strings_to_values.get(str(value), value)

    def _get_choices(self):
        return self._choices

    def _set_choices(self, choices):
        self.grouped_choices = to_choices_dict(choices)
        self._choices = flatten_choices_dict(self.grouped_choices)

        # Map the string representation of choices to the underlying value.
        # Allows us to deal with eg. integer choices while supporting either
        # integer or string input, but still get the correct datatype out.
        self.choice_strings_to_values = {str(key): key for key in self.choices}

    choices = property(_get_choices, _set_choices)


def check_if_db_field(field_name, field, model_property_names: list):
    if field.source == "*":
        return False

    if getattr(field, "write_only", False):
        return False

    if field.source in model_property_names:
        return False

    return True


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


NESTED_ENTITY_STRATEGY_ENTITY_FIRST = "entity_first"
NESTED_ENTITY_STRATEGY_ENTITY_FIELDS = "entity_fields_first"


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


def process_sub_serializers(
    field_path_parts: list,
    serializer: serializers.Serializer | serializers.ListSerializer,
    nested_serializers_fields_store: dict,
    entity_separator: str = ENTITY_SEPARATION,
    field_prefix: str = None,
) -> bool:
    """

    Args:
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

    try:
        nested_serializers_fields_store[(nested_entity_db_path, serializer_obj)].append(field_path_parts[1])
    except KeyError:
        nested_serializers_fields_store[(nested_entity_db_path, serializer_obj)] = [field_path_parts[1]]

    return True


def get_fields_filter(serializer: Serializer, request_fields, field_prefix=None, entity_separator=ENTITY_SEPARATION):
    """

    Args:
        serializer:
        request_fields:
        field_prefix:
        entity_separator:

    Returns:

    """
    serializer_fields = serializer.fields
    nested_serializers = {}
    db_fields_list = []

    for field in request_fields:
        ###
        # Take first part of str, and analyze it
        # Example "products.category.name" will split in ["products", "category.name"]
        # Where "products" is current looking field or nested serializer other part is path that need to resolved
        # in another context

        field_parts = field.split(".", 1)

        field_type = get_field_from_serializer_fields(field_parts[0], serializer_fields)

        # Skip process if we found no field for filter
        if not field_type:
            continue

        if isinstance(field_type, SERIALIZER_TYPES):
            process_sub_serializers(
                field_parts,
                serializer=field_type,
                nested_serializers_fields_store=nested_serializers,
                field_prefix=field_prefix,
                entity_separator=entity_separator,
            )
        else:
            db_field = extract_db_field(
                field, field_type, field_prefix=field_prefix, entity_separator=entity_separator
            )
            db_fields_list.append((db_field, field_type))

    if nested_serializers:
        for nested_serializer, fields in nested_serializers.items():
            nested_fields = get_fields_filter(
                serializer=nested_serializer[1],
                request_fields=fields,
                field_prefix=nested_serializer[0],
                entity_separator=entity_separator,
            )
            db_fields_list.extend(nested_fields)

    return db_fields_list


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
    model_filters = deepcopy(request_filters)

    for filter_dict in model_filters:
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
            db_fields_list.append([db_field, operator_field, value_field, filter_dict["value"]])

    if nested_serializers:
        for nested_serializer, model_filters in nested_serializers.items():
            nested_fields = build_fields_filter(
                serializer=nested_serializer[1],
                request_filters=model_filters,
                field_prefix=nested_serializer[0],
                entity_separator=entity_separator,
            )
            db_fields_list.extend(nested_fields)

    return db_fields_list


def build_filter_fields(field_type: serializers.Field, operator: str):
    operator_field = serializers.ChoiceField(choices=OperatorEnum.values())

    if UniqueValidator in field_type.validators:
        print("FOUND ")

    if OperatorEnum.is_list_type(operator):
        if field_type.source:
            field_type.source = None

        value_field = serializers.ListField(child=field_type)
    else:
        value_field = field_type

    return operator_field, value_field


class PositiveInteger(serializers.IntegerField):
    pass


class Command(BaseCommand):
    def handle(self, *args, **options):
        field_instance = PositiveInteger(max_value=100, min_value=0)
        operations = FilterOperationsRegister.get_default_operations(field_instance)
        print(operations)
        queryset = Product.objects.all()
        # print(queryset.query)
        product = queryset[1]
        serializer = ProductSerializer(instance=queryset[19:], many=True)
        # print(serializer.data)
        fields = ProductSerializer().get_fields()
        # print(ProductSerializer().get_fields())
        # print(serializer.get_fields())

        accepted_fields = []
        # field_filters = get_operations_serializer_fields(ProductSerializer())
        #
        # fields_filter = json.dumps(field_filters, indent=4)

        test_data = {
            "id": 1,
            "email": "chornuy.s@gmail.com",
            "addresses": [
                {"id": 1, "name": "home", "country": {"id": 1, "name": "USA", "code": "USA"}, "geolocation": "asdasd"}
            ],
            "accounts": [{"id": 1, "type": "Google"}],
        }

        request_fields = [
            "name",
            "email",
            "addresses.id",
            "addresses.name",
            "addresses.country.name",
            "addresses.geolocation",
            "accounts.type",
            # Not working cases
            # Skip in filters can be only fields, not entities
            "addresses.country",
            # Skip, not exists
            "accounts.noize",
            # Skip on subentity, not exist field
            "addresses.country.noize",
            "addresses",
        ]

        request_fields = ["id", "category.name", "product_tags.id", "category_name", "tags.name", "created_by.id"]

        filters_data = [
            {"field": "id", "operator": "in", "value": [123, 123123]},
            {"field": "category_name", "operator": "equal", "value": "phone"},
            {"field": "category.name", "operator": "in", "value": ["phone", "qqqqq"]},
            {"field": "category.id", "operator": "in", "value": [123]},
            {"field": "product_tags.id", "operator": "in", "value": [123]},
            {"field": "tags.name", "operator": "in", "value": ["android", "smartphone"]},
        ]

        # filter_serializer = FilterSerializer(data=filters_data, many=True, max_length=10)
        # filter_serializer.is_valid(raise_exception=True)
        # print(filters_data)
        # filters = build_fields_filter(ProductSerializer(), request_filters=filters_data, entity_separator="__")
        # print(filters_data)

        filter_serializer = FilterMapperSerializer(request_filters=filters_data, model_serializer=ProductSerializer())
        print(filter_serializer.init_filters)
        queryset = Product.objects.all()

        queryset = filter_serializer.to_query(queryset)
        print(FilterOperationsRegister.operations)
        # serializer = FilterSerializer(instance=ProductSerializer(), data=filters_data)
        # filters = serializer.data

        # for serializer_filter in filters:
        #     print(serializer_filter[0])
        #     print(serializer_filter[1])
        #     print(serializer_filter[2])
        #     print(serializer_filter[3])
        #     filter_type = serializer_filter[2]
        #     filter_value = serializer_filter[3]
        #     print(filter_value)
        #     # db_values = filter_type.to_internal_value(filter_value)

        exit()
        # model_fields = get_filter_fields(ProductSerializer())

        nested_fields = {}
        db_fields = []

        for filter_obj in filter_serializer.data:
            field_name = filter_obj["field"]
            filter_operator = filter_obj["operator"]
            filter_value = filter_obj["value"]
            # print(filter_obj["field"])
            field_name = field_name.rsplit(".", 1)
            print(field_name)
            try:
                field = fields[field_name[0]]
            except KeyError:
                continue

            if len(field_name) > 1:
                if isinstance(field, Serializer):
                    try:
                        nested_fields[field].append(field_name[1])
                    except KeyError:
                        nested_fields[field] = [field_name[1]]

                elif isinstance(field, ListSerializer):
                    child_serializer = field.child
                    try:
                        nested_fields[child_serializer].append(field_name[1])
                    except KeyError:
                        nested_fields[child_serializer] = [field_name[1]]
            else:
                db_fields.append(field.source)

            # data_base_operator = FIELDS_OPERATION_MAPPER[field.__class__]()
            # filter_value = data_base_operator.validate(filter_operator, field, filter_value)
            # print(field)
            # print(field_name)
            # print(filter_value)
        print(nested_fields)
        print(db_fields)
        # fields = get_serializer_fields(ProductSerializer())
        # print(fields)

        # print(fields)

        # potential_filters = filter_existing_fields(filters_data)
