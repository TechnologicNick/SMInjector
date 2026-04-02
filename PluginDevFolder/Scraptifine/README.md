# Scraptifine Benchmarking

## Run Benchmarks

Run from [PluginDevFolder/Scraptifine](C:\Users\Nick\Source\repos\SMInjector\PluginDevFolder\Scraptifine).

Uncapped FPS, 2160p:

```powershell
python .\benchmark.py --settings-config .\settings_uncapped_2160p.json --description "Uncapped FPS, 2160p"
```

144 FPS cap, 1080p:

```powershell
python .\benchmark.py --settings-config .\settings_144fps_1080p.json --description "144 FPS cap, 1080p"
```

Useful filters:

```powershell
python .\benchmark.py --settings-config .\settings_uncapped_2160p.json --description "Uncapped FPS, 2160p" --save creative_flat --threads 1 4 32
```

```powershell
python .\benchmark.py --settings-config .\settings_144fps_1080p.json --description "144 FPS cap, 1080p" --save survival --threads 7 12 --max-empty-capture-retries 5
```

Each benchmark session creates:

- `benchmark_results/<timestamp>/metadata.json`
- `benchmark_results/<timestamp>/settings.json`
- one run folder per `save + thread_count`

## Generate Graphs

Generate graphs for the newest session:

```powershell
python .\benchmark_graphs.py
```

Generate graphs for a specific session:

```powershell
python .\benchmark_graphs.py --session .\benchmark_results\20260402-161710
```

Only power and CPU/GPU usage:

```powershell
python .\benchmark_graphs.py --session .\benchmark_results\20260402-161710 --plots power usage
```

## Merge Partial Reruns

If some runs were retried in separate sessions, merge them by passing multiple `--session` arguments. The newest run for each `save + thread_count` wins.

Example for the 144 FPS cap, 1080p reruns:

```powershell
python .\benchmark_graphs.py `
  --session .\benchmark_results\20260402-175601 `
  --session .\benchmark_results\20260402-184249 `
  --session .\benchmark_results\20260402-185300 `
  --plots power usage
```

This writes merged outputs to `benchmark_results/<newest-session>/graphs_merged`.

## Output Files

Graph generation writes:

- `summary.csv`
- `<save>_dashboard.png`

The PNG title uses:

- session `description`
- per-save display names from `metadata.json`
