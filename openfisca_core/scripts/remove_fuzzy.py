# remove_fuzzy.py : Remove the fuzzy attribute in xml files and add END tags.
# See https://github.com/openfisca/openfisca-core/issues/437

import re
import datetime
import sys

assert(len(sys.argv) == 2)
filename = sys.argv[1]

with open(filename, 'r') as f:
    lines = f.readlines()


# Remove fuzzy

lines_2 = [
    line.replace(' fuzzy="true"', '')
    for line in lines
    ]

regex_indent = '^(\s*)<VALUE '
regex_fin = ' fin="([0-9\-]+)"'
regex_iso8601 = '([0-9]+)-([0-9]+)-([0-9]+)'
one_day = datetime.timedelta(days=1)

lines_3 = []
for line in lines_2:
    if ' fin="' in line:
        m_indent = re.search(regex_indent, line)
        spaces = m_indent.groups()[0]

        m_fin = re.search(regex_fin, line)
        fin_date = m_fin.groups()[0]
        fin_left, fin_right = m_fin.span()

        m_date = re.match(regex_iso8601, fin_date)
        year_str, month_str, day_str = m_date.groups()
        date_parsed = datetime.date(int(year_str), int(month_str), int(day_str))
        date_parsed += one_day
        fin_date = date_parsed.isoformat()

        lines_3.append(spaces + '<END deb="' + fin_date + '" />\n')
        lines_3.append(line[:fin_left] + line[fin_right:])
    else:
        lines_3.append(line)


# Remove useless END tags

regex_code = '<(CODE|SEUIL|TAUX|ASSIETTE)'
regex_code_end = '</(CODE|SEUIL|TAUX|ASSIETTE)'
regex_value = '<VALUE'
regex_end = '<END'

bool_code = [
    bool(re.search(regex_code, line))
    for line in lines_3
    ]

bool_code_end = [
    bool(re.search(regex_code_end, line))
    for line in lines_3
    ]

bool_value = [
    bool(re.search(regex_value, line))
    for line in lines_3
    ]

bool_end = [
    bool(re.search(regex_end, line))
    for line in lines_3
    ]


index_code = [i + 1 for i, x in enumerate(bool_code) if x]
index_code_end = [i for i, x in enumerate(bool_code_end) if x]

assert len(index_code) == len(index_code_end)

position_code = list(zip(index_code, index_code_end))


end_to_remove = []
regex_deb = ' deb="([0-9\-]+)"'

for code_begining, code_end in position_code:
    deb_list = []

    for local_i, line in enumerate(lines_3[code_begining:code_end]):
        i = local_i + code_begining

        m_deb = re.search(regex_deb, line)
        if m_deb:
            deb_tmp = m_deb.groups()[0]
            deb_list.append(deb_tmp)
        else:
            deb_list.append(None)

    for repr_deb in set(deb_list) - {None}:
        part_list = [
            local_i + code_begining
            for local_i, deb in enumerate(deb_list)
            if deb == repr_deb
            ]

        assert len(part_list) <= 2

        if len(part_list) == 2:
            i1 = part_list[0]
            i2 = part_list[1]
            if bool_value[i1]:
                assert not bool_value[i2]
                assert not bool_end[i1]
                assert bool_end[i2]
                i_value = i1
                i_end = i2
            else:
                assert bool_value[i2]
                assert bool_end[i1]
                assert not bool_end[i2]
                i_value = i2
                i_end = i1

            end_to_remove.append(i_end)


end_to_remove_set = set(end_to_remove)


lines_4 = [
    line
    for j, line in enumerate(lines_3)
    if j not in end_to_remove_set
    ]


# Write

with open(filename, 'w') as f:
    for line in lines_4:
        f.write(line)
