import json

import pytest

from src.manager import Manager
from src.models import Parameters


@pytest.fixture
def make_manager(tmp_path):
    def _make(apartments=None, tenants=None, transfers=None, bills=None) -> Manager:
        files = {
            'apartments': apartments or {},
            'tenants': tenants or {},
            'transfers': transfers or [],
            'bills': bills or [],
        }
        paths = {}
        for name, content in files.items():
            path = tmp_path / f'{name}.json'
            path.write_text(json.dumps(content))
            paths[f'{name}_json_path'] = str(path)
        return Manager(Parameters(**paths))
    return _make