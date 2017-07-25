import re


# NOTE: We could use a serialisation library like marshmallow, but it was
# outside the scope of the brief
EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[A-Za-z]+$')


def validate_address_email(datum):
    if 'email' not in datum:
        return 'Email is required'

    email = datum['email']

    if not email:
        return 'Email cannot be empty'

    if not EMAIL_PATTERN.match(email):
        return 'Invalid email format'

    return None


def validate(data, validators=None):
    """
    Validates data against given validators.

    :param data: Data to be validated
    :type data: list of dict

    :param validators: List of validators
    :type validators: list of functions

    :returns: Validation results for each record
    :rtype: dict
    """
    validations = {}

    if validators:
        for index, datum in enumerate(data):
            for validator in validators:
                error = validator(datum)
                if error is not None:
                    validations[index] = error

    return validations
