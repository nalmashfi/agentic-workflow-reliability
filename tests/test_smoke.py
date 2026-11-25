from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reproduce import annotation_sequence, transition_counts, heldout_validation


def test_small_sequence_logic():
    rows = [
        {'stage_count': 4, 'incorrect_stages': [{'stage_id': 2}, {'stage_id': 4}], 'solved': True,
         'task_name': 'repoA__1'},
        {'stage_count': 4, 'incorrect_stages': [{'stage_id': 2}, {'stage_id': 3}], 'solved': False,
         'task_name': 'repoB__1'},
    ]
    assert annotation_sequence(rows[0]) == [0, 1, 0, 1]
    x = transition_counts(rows)
    assert x['NI'] == 3 and x['IN'] == 2 and x['II'] == 1 and x['NN'] == 0
    assert x['recurrence_count'] == 1 and x['return_followup_opportunities'] == 1


def test_balanced_group_assignment():
    rows = []
    sizes = [8, 7, 6, 5, 4, 3, 2, 1, 1, 1]
    for idx, n in enumerate(sizes):
        for j in range(n):
            rows.append({'stage_count': 3, 'incorrect_stages': [], 'solved': True,
                         'task_name': f'repo{idx}__task{j}'})
    _, _, foldmap, info = heldout_validation(rows, 5, 5, 10, 20, 20260918)
    assert len(foldmap) == len(sizes)
    assert max(info['trajectory_counts']) - min(info['trajectory_counts']) <= 1


if __name__ == '__main__':
    test_small_sequence_logic()
    test_balanced_group_assignment()
    print('PASS smoke tests')
