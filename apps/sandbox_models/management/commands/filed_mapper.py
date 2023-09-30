import inspect

from django.core import validators
from django.db import models
from django.utils.text import capfirst
from rest_framework.compat import postgres_fields
from rest_framework.utils.field_mapping import needs_label

NUMERIC_FIELD_TYPES = (
    models.IntegerField,
    models.FloatField,
    models.DecimalField,
    models.DurationField,
)


def get_field_kwargs(field_name, model_field):
    """
    Creates a default instance of a basic non-relational field.
    """
    kwargs = {}
    validator_kwarg = list(model_field.validators)

    # The following will only be used by ModelField classes.
    # Gets removed for everything else.
    kwargs["model_field"] = model_field

    if model_field.verbose_name and needs_label(model_field, field_name):
        kwargs["label"] = capfirst(model_field.verbose_name)

    if model_field.help_text:
        kwargs["help_text"] = model_field.help_text

    max_digits = getattr(model_field, "max_digits", None)
    if max_digits is not None:
        kwargs["max_digits"] = max_digits

    decimal_places = getattr(model_field, "decimal_places", None)
    if decimal_places is not None:
        kwargs["decimal_places"] = decimal_places

    if isinstance(model_field, models.SlugField):
        kwargs["allow_unicode"] = model_field.allow_unicode

    if (
        isinstance(model_field, models.TextField)
        and not model_field.choices
        or (postgres_fields and isinstance(model_field, postgres_fields.JSONField))
        or (hasattr(models, "JSONField") and isinstance(model_field, models.JSONField))
    ):
        kwargs["style"] = {"base_template": "textarea.html"}

    if model_field.null:
        kwargs["allow_null"] = True

    if isinstance(model_field, models.AutoField) or not model_field.editable:
        # If this field is read-only, then return early.
        # Further keyword arguments are not valid.
        kwargs["read_only"] = True
        return kwargs

    if model_field.has_default() or model_field.blank or model_field.null:
        kwargs["required"] = False

    if model_field.blank and (isinstance(model_field, (models.CharField, models.TextField))):
        kwargs["allow_blank"] = True

    if not model_field.blank and (postgres_fields and isinstance(model_field, postgres_fields.ArrayField)):
        kwargs["allow_empty"] = False

    if isinstance(model_field, models.FilePathField):
        kwargs["path"] = model_field.path

        if model_field.match is not None:
            kwargs["match"] = model_field.match

        if model_field.recursive is not False:
            kwargs["recursive"] = model_field.recursive

        if model_field.allow_files is not True:
            kwargs["allow_files"] = model_field.allow_files

        if model_field.allow_folders is not False:
            kwargs["allow_folders"] = model_field.allow_folders

    if model_field.choices:
        kwargs["choices"] = model_field.choices
    else:
        # Ensure that max_value is passed explicitly as a keyword arg,
        # rather than as a validator.
        max_value = next(
            (
                validator.limit_value
                for validator in validator_kwarg
                if isinstance(validator, validators.MaxValueValidator)
            ),
            None,
        )
        if max_value is not None and isinstance(model_field, NUMERIC_FIELD_TYPES):
            kwargs["max_value"] = max_value
            validator_kwarg = [
                validator for validator in validator_kwarg if not isinstance(validator, validators.MaxValueValidator)
            ]

        # Ensure that min_value is passed explicitly as a keyword arg,
        # rather than as a validator.
        min_value = next(
            (
                validator.limit_value
                for validator in validator_kwarg
                if isinstance(validator, validators.MinValueValidator)
            ),
            None,
        )
        if min_value is not None and isinstance(model_field, NUMERIC_FIELD_TYPES):
            kwargs["min_value"] = min_value
            validator_kwarg = [
                validator for validator in validator_kwarg if not isinstance(validator, validators.MinValueValidator)
            ]

        # URLField does not need to include the URLValidator argument,
        # as it is explicitly added in.
        if isinstance(model_field, models.URLField):
            validator_kwarg = [
                validator for validator in validator_kwarg if not isinstance(validator, validators.URLValidator)
            ]

        # EmailField does not need to include the validate_email argument,
        # as it is explicitly added in.
        if isinstance(model_field, models.EmailField):
            validator_kwarg = [
                validator for validator in validator_kwarg if validator is not validators.validate_email
            ]

        # SlugField do not need to include the 'validate_slug' argument,
        if isinstance(model_field, models.SlugField):
            validator_kwarg = [validator for validator in validator_kwarg if validator is not validators.validate_slug]

        # IPAddressField do not need to include the 'validate_ipv46_address' argument,
        if isinstance(model_field, models.GenericIPAddressField):
            validator_kwarg = [
                validator for validator in validator_kwarg if validator is not validators.validate_ipv46_address
            ]
        # Our decimal validation is handled in the field code, not validator code.
        if isinstance(model_field, models.DecimalField):
            validator_kwarg = [
                validator for validator in validator_kwarg if not isinstance(validator, validators.DecimalValidator)
            ]

    # Ensure that max_length is passed explicitly as a keyword arg,
    # rather than as a validator.
    max_length = getattr(model_field, "max_length", None)
    if max_length is not None and (isinstance(model_field, (models.CharField, models.TextField, models.FileField))):
        kwargs["max_length"] = max_length
        validator_kwarg = [
            validator for validator in validator_kwarg if not isinstance(validator, validators.MaxLengthValidator)
        ]

    # Ensure that min_length is passed explicitly as a keyword arg,
    # rather than as a validator.
    min_length = next(
        (
            validator.limit_value
            for validator in validator_kwarg
            if isinstance(validator, validators.MinLengthValidator)
        ),
        None,
    )
    if min_length is not None and isinstance(model_field, models.CharField):
        kwargs["min_length"] = min_length
        validator_kwarg = [
            validator for validator in validator_kwarg if not isinstance(validator, validators.MinLengthValidator)
        ]

    # if getattr(model_field, 'unique', False):
    #     validator = UniqueValidator(
    #         queryset=model_field.model._default_manager,
    #         message=get_unique_error_message(model_field))
    #     validator_kwarg.append(validator)

    if validator_kwarg:
        kwargs["validators"] = validator_kwarg

    return kwargs
