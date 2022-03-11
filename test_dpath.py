import dpath.util

def dict_creator(current, segments, i, hints=()):
    segment = segments[i]

    if isinstance(segment, int):
        dpath.segments.extend(current, segment)

    # Infer the type from the hints provided.
    if i < len(hints):
        current[segment] = hints[i][1]()
    else:
        current[segment] = {}


x={}
# dpath.util.new(x,'path/that/not/exist/2', 42, creator=dict_creator)

y={'path': {'that': {'exist': {'2': 50}}}}
dpath.util.new(x,'path/that/exist/2', 42, creator=dict_creator)
print(x)
print(y)
dpath.util.merge(y, x)
print(y)

#   File "/media/data/dev/src/LEXIMPACT/openfisca-core/.venv/lib/python3.8/site-packages/dpath/util.py", line 337, in merger
#     target += found
# TypeError: unsupported operand type(s) for +=: 'dict' and 'dict'

# input_data = {'persons': {'bill': {'birth': {'2017-12': '1980-01-01'}, 'age': {'2017-12': None},
#  'salary': {'2017-12': 2000},
#  'basic_income': {'2017-12': None},
#  'income_tax': {'2017-12': None}},
#  'bob': {
#      'salary': {    '2017-12': 15000},
#      'basic_income': {'2017-12': None},
#      'social_security_contribution': {'2017-12': None}
#  }},
#  'households': {
#      'first_household': {
#          'parents': ['bill', 'bob'],
#          'housing_tax': {'2017': None}, 'accommodation_size': {'2017-01': 300}}}}
# #input_data =          {'persons': {'bill': {'age': {'2017-12': None}}}}
# #computation_results = {'persons': {'bill': {'age': {'2017-12': 37}, 'basic_income': {'2017-12': 600.0}, 'income_tax': {'2017-12': 300.0}}, 'bob': {'basic_income': {'2017-12': 600.0}, 'social_security_contribution': {'2017-12': 816.0}}}, 'households': {'first_household': {'housing_tax': {2017: 3000.0}}}}
# computation_results = {'persons': {'bill': {'age': {'2017-12': 37},
#  'basic_income': {'2017-12': 600.0},
#  'income_tax': {'2017-12': 300.0}},
#  'bob': {'basic_income': {'2017-12': 600.0},
#  'social_security_contribution': {'2017-12': 816.0}}},
#  'households': {
#     'first_household': {
#             'housing_tax': {2017: 3000.0}
#         }
#     }
# }

# dpath.util.merge(input_data, computation_results)
# print(input_data)