#!/usr/bin/env python3
"""Analyze OVO per-stage logs without changing experiment artifacts.

Usage:
  python scripts/analyze_performance.py \
    --logger data/output/Replica/exp01_replica_office0_fixed10/office0/logger
"""
import argparse
import ast
import csv
import json
import math
from pathlib import Path

import numpy as np

STAGE_A = ('t_sam', 't_obj', 'n_matches')
STAGE_B = ('t_clip', 't_up')
METRICS = ('t_sam', 't_obj', 't_clip', 't_up', 'n_matches', 'vram', 'ram', 'spf')


def read_lines(path):
    if not path.exists():
        return []
    return [s.strip() for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]


def read_numbers(path):
    result = []
    for n, line in enumerate(read_lines(path), 1):
        try:
            result.append(float(line))
        except ValueError as exc:
            raise ValueError(f'{path}:{n}: not a number: {line[:80]}') from exc
    return result


def read_spf(path):
    if not path.exists():
        return []
    content = path.read_text(encoding='utf-8').strip()
    if not content:
        return []
    if content.startswith('['):
        obj = ast.literal_eval(content)
        if isinstance(obj, list) and len(obj) == 1 and isinstance(obj[0], list):
            obj = obj[0]
        if not isinstance(obj, list):
            raise ValueError('SPF must be a list or one value per line')
        return [float(x) for x in obj]
    return read_numbers(path)


def stats(values):
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if not len(arr):
        return {'count': 0}
    return {
        'count': int(len(arr)), 'mean': float(np.mean(arr)),
        'median': float(np.median(arr)), 'p95': float(np.percentile(arr, 95)),
        'p99': float(np.percentile(arr, 99)), 'min': float(np.min(arr)),
        'max': float(np.max(arr)), 'sum': float(np.sum(arr)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--logger', type=Path, required=True, help='Path to OVO logger directory')
    parser.add_argument('--out', type=Path, default=None, help='Output directory (default: sibling performance_analysis)')
    args = parser.parse_args()
    folder = args.logger
    if not folder.is_dir():
        parser.error(f'Logger directory not found: {folder}')
    out = args.out or folder.parent / 'performance_analysis'
    out.mkdir(parents=True, exist_ok=True)

    data = {name: read_spf(folder / 'spf.log') if name == 'spf' else read_numbers(folder / f'{name}.log') for name in METRICS}
    ids = [int(v) for v in read_numbers(folder / 'frame_id.log')]
    n_a = len(data['t_sam'])
    n_b = len(data['t_clip'])
    counts = {name: len(vals) for name, vals in data.items()}
    counts['frame_id'] = len(ids)
    warnings = []

    # OVO's log_ovo_stats() appends a frame ID for each event: stage A and stage B.
    # The event order is retained in frame_id.log but event type is not. Infer a unique
    # partition only if ordering and known stage counts constrain it sufficiently.
    # Stage A frames must be monotonic; B frames can lag A due to queue processing.
    # Ambiguity is common, so do not silently claim an exact mapping.
    if len(ids) != n_a + n_b:
        warnings.append(f'frame_id count ({len(ids)}) differs from stage A+B events ({n_a+n_b}); exact frame assignment unavailable')
    else:
        warnings.append('frame_id has no event-type labels; exact stage-to-frame assignment cannot be guaranteed from separate logs')

    if len({len(data[k]) for k in STAGE_A}) != 1:
        warnings.append('Stage A metric lengths differ; index alignment may be invalid')
    if len({len(data[k]) for k in STAGE_B}) != 1:
        warnings.append('Stage B metric lengths differ; index alignment may be invalid')
    if len(data['vram']) != n_a:
        warnings.append('VRAM length differs from SAM; VRAM-to-SAM index mapping is unverified')
    if not data['t_sam']:
        warnings.append('No SAM samples found')

    # Index-based table, NOT a verified frame-ID alignment.
    n_rows = max((len(data[k]) for k in METRICS), default=0)
    fields = ['sample_index', 'frame_id_verified'] + list(METRICS)
    with (out / 'performance_samples.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for i in range(n_rows):
            row = {'sample_index': i, 'frame_id_verified': ''}
            row.update({k: data[k][i] if i < len(data[k]) else '' for k in METRICS})
            writer.writerow(row)

    duration = sum(data['t_sam']) + sum(data['t_obj']) + sum(data['t_clip']) + sum(data['t_up'])
    report = {
        'logger_path': str(folder), 'counts': counts,
        'metrics': {key: stats(vals) for key, vals in data.items()},
        'derived': {
            'sum_sam_obj_clip_up_seconds': duration,
            'sum_sam_obj_seconds': sum(data['t_sam']) + sum(data['t_obj']),
            'sum_clip_up_seconds': sum(data['t_clip']) + sum(data['t_up']),
            'note': 'Sum of separately timed stages; not end-to-end wall time and may omit overhead.'
        },
        'alignment': 'unverified', 'warnings': warnings,
    }
    for key in ('avg_fps', 'max_vram', 'max_ram'):
        vals = read_numbers(folder / f'{key}.log')
        if vals:
            report['derived'][key] = vals[-1]
    (out / 'performance_summary.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        for keys, name, ylabel in [
            (('t_sam', 't_clip', 't_obj', 't_up'), 'timing.png', 'Time (s)'),
            (('vram', 'ram'), 'memory.png', 'Memory (GB)'),
        ]:
            fig, ax = plt.subplots(figsize=(10, 4))
            plotted = False
            for key in keys:
                if data[key]:
                    ax.plot(range(len(data[key])), data[key], label=key, linewidth=1)
                    plotted = True
            if plotted:
                ax.set(xlabel='Metric sample index (not verified frame ID)', ylabel=ylabel)
                ax.legend()
                ax.grid(alpha=0.2)
                fig.tight_layout()
                fig.savefig(out / name, dpi=160)
            plt.close(fig)
    except ImportError:
        warnings.append('matplotlib missing; plots skipped')
        (out / 'performance_summary.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f'Analysis saved: {out}')
    print('Counts:', counts)
    for key in ('t_sam', 't_clip', 't_obj', 't_up', 'spf'):
        s = report['metrics'][key]
        if s['count']:
            print(f'{key:8s} n={s["count"]:3d} mean={s["mean"]:.3f}s p95={s["p95"]:.3f}s sum={s["sum"]:.2f}s')
    print(f'Sum of timed stages: {duration:.2f}s (not wall-clock time)')
    for warning in warnings:
        print('WARNING:', warning)


if __name__ == '__main__':
    main()
