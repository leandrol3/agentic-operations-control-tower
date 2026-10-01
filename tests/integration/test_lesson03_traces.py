"""Opt-in: compose stack with OTEL_ENABLED=true. Failures need the explicit failure profile."""
import importlib.util
import os
from pathlib import Path
import pytest
pytestmark=pytest.mark.skipif(os.getenv('LESSON03_TRACING_INTEGRATION')!='1', reason='Requires running Collector/Jaeger + runtime')


def test_distributed_trace_in_backend(tmp_path):
    path=Path(__file__).resolve().parents[2]/'scripts/trace_lesson03.py'
    spec=importlib.util.spec_from_file_location('trace_demo',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result=module.run(os.getenv('LESSON03_TRACE_DEMO','normal'),output=str(tmp_path))
    assert result['spans']>=20
