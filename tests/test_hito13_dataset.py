import copy
import hashlib
from pathlib import Path

import pytest

from scripts.hito13.preparar_datos import ROOT, dataset_module, digest, missing_for_match


def small_config():
    return dict(schema_version=1,seed=1209,matches=4,minutes=2,step_seconds=5,
                start_utc='2030-06-08T19:00:00Z',database='hito12_g09',measurement='estadisticas_equipo')


def test_reuses_generator_without_changing_or_importing_blocked_common(tmp_path):
    import sys
    before=hashlib.sha256((ROOT/'hito12/common.py').read_bytes()).hexdigest()
    dataset=dataset_module()
    cfg=small_config()
    a=dataset.generate(cfg,tmp_path/'a')
    b=dataset.generate(cfg,tmp_path/'b')
    assert a==b and a['rows']==192
    assert (tmp_path/'a/dataset.lp').read_bytes()==(tmp_path/'b/dataset.lp').read_bytes()
    assert 'hito12.common' not in sys.modules
    assert hashlib.sha256((ROOT/'hito12/common.py').read_bytes()).hexdigest()==before


def test_writes_only_missing_and_rejects_foreign_or_changed_data():
    dataset=dataset_module();cfg=small_config()
    rows=list(dataset.rows_for_match(cfg,1))
    assert len(missing_for_match(dataset,cfg,1,[]))==48
    assert len(missing_for_match(dataset,cfg,1,rows[:10]))==38
    assert missing_for_match(dataset,cfg,1,rows)==[]
    for bad in [rows+[rows[0]], [dict(rows[0],partido_id='P099')], [dict(rows[0],posesion_pct=0)]]:
        with pytest.raises(RuntimeError):
            missing_for_match(dataset,cfg,1,bad)
