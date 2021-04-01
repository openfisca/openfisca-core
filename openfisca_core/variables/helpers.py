def _partition(dict, predicate):
    true_dict = {}
    false_dict = {}

    for key, value in dict.items():
        if predicate(key, value):
            true_dict[key] = value
        else:
            false_dict[key] = value

    return true_dict, false_dict
