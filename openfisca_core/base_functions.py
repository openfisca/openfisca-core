from .enumerations import Enum

base_functions = Enum([
    'missing_value',
    'last_duration_last_value',
    'requested_period_added_value',
    'requested_period_default_value',
    'requested_period_last_or_next_value',
    'requested_period_last_value',
    ])

missing_value = base_functions['missing_value']
last_duration_last_value = base_functions['last_duration_last_value']
requested_period_added_value = base_functions['requested_period_added_value']
requested_period_default_value = base_functions['requested_period_default_value']
requested_period_last_or_next_value = base_functions['requested_period_last_or_next_value']
requested_period_last_value = base_functions['requested_period_last_value']
