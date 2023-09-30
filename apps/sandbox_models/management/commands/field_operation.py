from enum import Enum

from django.db.models import Q
from rest_framework.fields import (
    BooleanField,
    CharField,
    ChoiceField,
    DateField,
    DateTimeField,
    DecimalField,
    DurationField,
    EmailField,
    FileField,
    FilePathField,
    FloatField,
    HiddenField,
    ImageField,
    IntegerField,
    IPAddressField,
    JSONField,
    ListField,
    ModelField,
    SerializerMethodField,
    SlugField,
    TimeField,
    URLField,
    UUIDField,
)
from rest_framework.relations import PrimaryKeyRelatedField, SlugRelatedField
from rest_framework.serializers import ListSerializer, Serializer


class ApiTypeField(str, Enum):
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    CHARACTER = "char"
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
    RESOURCE = "resource"


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


LIST_OPERATORS_MAX_ELEMENTS = 10
LIST_OPERATORS = [OperatorEnum.IN.value, OperatorEnum.NOT_IN.value]


class FieldOperationBase:
    django_rest_field = None
    api_field_type = None
    support_operations = OperatorEnum.values()

    OPERATOR_MAPPER = {
        OperatorEnum.GREATER_THAN.value: ("__gte", False),
        OperatorEnum.LESS_THAN.value: ("__lte", False),
        OperatorEnum.EQUAL.value: ("__exact", False),
        OperatorEnum.NOT_EQUAL.value: ("__exact", True),
        OperatorEnum.IN.value: ("__in", False),
        OperatorEnum.NOT_IN.value: ("__in", True),
        OperatorEnum.IN_RANGE.value: ("__range", False),
        OperatorEnum.NOT_IN_RANGE.value: ("__range", True),
        OperatorEnum.CONTAINS.value: ("__contains", False),
        OperatorEnum.NOT_CONTAINS.value: ("__contains", True),
    }

    def transform_to_query(self, field, operator_value, value):
        django_operation, is_exclusion = self.OPERATOR_MAPPER[operator_value]

        operation_kwarg = {f"{field}{django_operation}": value}

        if not is_exclusion:
            return Q(**operation_kwarg)
        else:
            return ~Q(**operation_kwarg)

    def validate(self, operator: str, field, value):
        if operator not in self.support_operations:
            ValueError("Not supported operation")

        if operator in LIST_OPERATORS:
            field_source = field.source
            field.source = None
            list_values = ListField(child=field, max_length=LIST_OPERATORS_MAX_ELEMENTS)
            field.source = field_source
            print(value)
            return list_values.run_validation(value)
        else:
            return field.run_validation(value)

    def to_api_response(self, field):
        return {"field_name": field, "operations": self.support_operations, "field_type": self.api_field_type}


class IntegerFieldOperation(FieldOperationBase):
    django_rest_field = IntegerField
    api_field_type = ApiTypeField.INTEGER.value


class FloatFieldOperation(FieldOperationBase):
    django_rest_field = FloatField
    api_field_type = ApiTypeField.FLOAT.value


class DecimalFieldOperation(FieldOperationBase):
    django_rest_field = DecimalField
    api_field_type = ApiTypeField.DECIMAL.value


class BooleanFieldOperation(FieldOperationBase):
    django_rest_field = BooleanField
    api_field_type = ApiTypeField.BOOLEAN.value
    support_operations = [OperatorEnum.EQUAL.value, OperatorEnum.NOT_EQUAL.value]


class CharFieldFieldOperation(FieldOperationBase):
    django_rest_field = CharField
    api_field_type = ApiTypeField.CHARACTER.value
    support_operations = [OperatorEnum.EQUAL.value, OperatorEnum.NOT_EQUAL.value]


class DateFieldOperation(FieldOperationBase):
    django_rest_field = DateField
    api_field_type = ApiTypeField.DATE.value


class DateTimeFieldOperation(FieldOperationBase):
    django_rest_field = DateTimeField
    api_field_type = ApiTypeField.DATETIME.value


class DurationFieldOperation(FieldOperationBase):
    django_rest_field = DurationField
    api_field_type = ApiTypeField.DURATION.value


class EmailFieldFieldOperation(CharFieldFieldOperation):
    django_rest_field = EmailField


class FileFieldOperation(CharFieldFieldOperation):
    django_rest_field = FileField


class ImageFieldOperation(CharFieldFieldOperation):
    django_rest_field = ImageField


class SlugFieldOperation(CharFieldFieldOperation):
    django_rest_field = SlugField


class URLFieldOperation(CharFieldFieldOperation):
    django_rest_field = URLField


class UUIDFieldOperation(CharFieldFieldOperation):
    django_rest_field = UUIDField


class IPAddressFieldOperation(CharFieldFieldOperation):
    django_rest_field = IPAddressField


class FilePathFieldOperation(CharFieldFieldOperation):
    django_rest_field = FilePathField


class JSONFieldFieldOperation(CharFieldFieldOperation):
    django_rest_field = JSONField


class ChoiceFieldOperation(CharFieldFieldOperation):
    django_rest_field = ChoiceField


class ResourceFieldOperation(FieldOperationBase):
    django_rest_field = PrimaryKeyRelatedField
    api_field_type = ApiTypeField.RESOURCE.value
    support_operations = [OperatorEnum.EQUAL.value, OperatorEnum.NOT_EQUAL.value]


FIELDS_OPERATION_LIST = [
    IntegerFieldOperation,
    FloatFieldOperation,
    BooleanFieldOperation,
    CharFieldFieldOperation,
    DateFieldOperation,
    DateTimeFieldOperation,
    DurationFieldOperation,
    EmailFieldFieldOperation,
    FileFieldOperation,
    ImageFieldOperation,
    SlugFieldOperation,
    URLFieldOperation,
    UUIDFieldOperation,
    IPAddressFieldOperation,
    FilePathFieldOperation,
    DecimalFieldOperation,
    JSONFieldFieldOperation,
    ChoiceFieldOperation,
]

NO_OPERATION_SUPPORTED = (ModelField, SerializerMethodField, PrimaryKeyRelatedField, SlugRelatedField, HiddenField)

SERIALIZER_TYPES = (Serializer, ListSerializer)

FIELDS_OPERATION_MAPPER = {operator_cls.django_rest_field: operator_cls for operator_cls in FIELDS_OPERATION_LIST}

FIELDS_OPERATION_MAPPER_OPERATOR_LIST = {
    operator_cls.django_rest_field: operator_cls.support_operations for operator_cls in FIELDS_OPERATION_LIST
}
