from __future__ import annotations

from typing import Dict, Tuple, Sequence

import csv
import importlib.resources
import itertools
import json
import os

from openfisca_core import types

from .trace_node import TraceNode

Trace = Dict[str, dict]
Calculation = Tuple[str, dict]
SortedTrace = Sequence[Calculation]


class PerformanceLog:
    def __init__(self, full_tracer: types.FullTracer) -> None:
        self._full_tracer = full_tracer

    def generate_graph(self, dir_path: str) -> None:
        with open(os.path.join(dir_path, 'performance_graph.html'), 'w') as f:
            template = importlib.resources.read_text(
                'openfisca_core.scripts.assets',
                'index.html',
                )

            perf_graph_html = template.replace(
                '{{data}}',
                json.dumps(self._json()),
                )

            f.write(perf_graph_html)

    def generate_performance_tables(self, dir_path: str) -> None:
        flat_trace = self._full_tracer.get_flat_trace()

        csv_rows = [
            {
                'name': key,
                'calculation_time': trace['calculation_time'],
                'formula_time': trace['formula_time'],
                }
            for key, trace
            in flat_trace.items()
            ]

        self._write_csv(
            os.path.join(dir_path, 'performance_table.csv'),
            csv_rows,
            )

        aggregated_csv_rows = [
            {'name': key, **aggregated_time}
            for key, aggregated_time
            in self.aggregate_calculation_times(flat_trace).items()
            ]

        self._write_csv(
            os.path.join(dir_path, 'aggregated_performance_table.csv'),
            aggregated_csv_rows,
            )

    def aggregate_calculation_times(
            self,
            flat_trace: Trace,
            ) -> Dict[str, dict]:

        def _aggregate_calculations(calculations: list) -> dict:
            calculation_count = len(calculations)

            calculation_time = sum(
                calculation[1]['calculation_time']
                for calculation
                in calculations
                )

            formula_time = sum(
                calculation[1]['formula_time']
                for calculation
                in calculations
                )

            return {
                'calculation_count': calculation_count,
                'calculation_time': TraceNode.round(calculation_time),
                'formula_time': TraceNode.round(formula_time),
                'avg_calculation_time': TraceNode.round(calculation_time / calculation_count),
                'avg_formula_time': TraceNode.round(formula_time / calculation_count),
                }

        def _groupby(calculation: Calculation) -> str:
            return calculation[0].split('<')[0]

        all_calculations: SortedTrace = sorted(flat_trace.items())

        return {
            variable_name: _aggregate_calculations(list(calculations))
            for variable_name, calculations
            in itertools.groupby(all_calculations, _groupby)
            }

    def _json(self) -> dict:
        children = [self._json_tree(tree) for tree in self._full_tracer.trees]
        calculations_total_time = sum(child['value'] for child in children)

        return {
            'name': 'All calculations',
            'value': calculations_total_time,
            'children': children,
            }

    def _json_tree(self, tree: types.TraceNode) -> dict:
        calculation_total_time = tree.calculation_time()
        children = [self._json_tree(child) for child in tree.children]

        return {
            'name': f"{tree.name}<{tree.period}>",
            'value': calculation_total_time,
            'children': children,
            }

    def _write_csv(self, path: str, rows: Sequence[dict]) -> None:
        fieldnames = list(rows[0].keys())

        with open(path, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames = fieldnames)
            writer.writeheader()

            for row in rows:
                writer.writerow(row)
