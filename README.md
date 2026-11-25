# Agentic workflow reliability

In this repository, we provide the code and results for *Stochastic Reliability Model for Failure Propagation, Verification, and Recovery in Agentic Software Engineering Workflows*. For each recorded trajectory, the analysis reconstructs the sequence of stage annotations and relates that sequence to the final task outcome. The terminal task outcome gives the acceptance result, but it does not identify the stage at which an incorrect annotation first appears. To assess the observable process, we estimate uncertainty, evaluate predictions on held out repositories, and finally compare the analytical recursion with Monte Carlo estimates. Thus, the analysis uses the original agent runs without requiring access to hidden reliability states.

The installation section gives the software requirements. Next, the input section identifies the Tracebench manifest and the digest used to verify its contents before analysis. The reproduction section presents the commands for checking the implementation and reproducing the results from the public input. Finally, the results section summarizes the files that support the manuscript and gives an example of their use.

## Installation

For installation, the reproduction scripts require Python 3.11 or later and the package versions recorded in `requirements.txt`. In the repository directory, the researcher creates a virtual environment and activates it in the shell used for the analysis. For Linux and macOS, the activation command differs from the command used in Windows PowerShell. The commands for installing the tested package versions are as follows.

1. *Environment:* First, the researcher creates a virtual environment in the directory that contains this file.
   ```bash
   python -m venv .venv
   ```
2. *Activation:* Next, the researcher selects the command used by the current shell to activate the environment from the repository directory. The first and second commands apply to Bash and Windows PowerShell, respectively.
   ```bash
   source .venv/bin/activate
   ```
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
3. *Dependencies:* Then, the researcher installs the package versions used for the recorded analysis.
   ```bash
   python -m pip install -r requirements.txt
   ```

## Input data

For the empirical analysis, we use the [fixed revision of the Tracebench manifest](https://huggingface.co/datasets/Contextbench/Tracebench/resolve/7da2e4f45b330be8b6e8f1cff835247723cb3341/bench_manifest.full.jsonl) and verify the file before selecting the trajectories. Afterward, the researcher saves the downloaded file in the repository directory under its original name, `bench_manifest.full.jsonl`. The expected file size is 75,450,201 bytes. Before reading the records, the analysis compares the Secure Hash Algorithm (SHA-256) digest with `8f688bb147fb1840572887af10d137653b4b49523c5bbd3dc3ee9c333bbe082e`. Thus, the application accepts the downloaded manifest only when its digest matches the value recorded for the original input.

## Reproduction

In this section, we give the commands for testing stage reconstruction and reproducing the analysis from the matching manifest. Finally, the researcher runs the smoke test and the full analysis in the activated environment using the commands below. For the smoke test, the application checks stage reconstruction and fold assignment using small constructed examples. For the full analysis, the application computes the numerical results, checks them against the frozen reference values, and then writes the analysis figures. The commands, in execution order, are as follows.

```bash
python tests/test_smoke.py
python scripts/run_all.py --manifest bench_manifest.full.jsonl --out outputs
```

## Results

For a completed run, the numerical check reports `PASS` and the application places the new results in the specified output directory. The [evidence guide](docs/EVIDENCE.md) relates the manuscript claims to their supporting tables and gives the correspondence between the generated plots and the manuscript figures. In the filenames, `v23` identifies the analysis schema. For inspection of an existing result, the researcher can use the stored results without downloading the manifest. To locate evidence such as the fitted transition estimates and the validation scores, the reader can use the directory entries as follows.

| Directory or file | Contents |
| --- | --- |
| [scripts](scripts/) and [tests](tests/) | Analysis, numerical checks, figure generation, and smoke tests |
| [config](config/analysis_config.json) | Settings used for input selection, uncertainty estimates, validation, and simulation |
| [expected](expected/expected_results_v23.json) | Frozen targets used by the numerical checks |
| [results](results/) | Recorded run, repository assignments, and tables for the manuscript |
| [publication_figures](publication_figures/) | Figures used in the manuscript and the editable source for Figure 7 |
| [provenance](provenance/provenance.json) | Input identity, execution identifiers, and recorded software versions |
| [CHECKSUMS.sha256](CHECKSUMS.sha256) | File integrity checks for this distribution |

To check the recorded results, the researcher compares the stored run with the frozen reference values using the first command below. From the same stored results, the figure generation script reads the model estimates and tables and then writes the analysis plots. In both cases, the scripts read the recorded output without fitting the model or recomputing the bootstrap estimates. The commands for verification and figure generation are as follows.

```bash
python scripts/verify_expected.py --actual results/results_v23.json --expected expected/expected_results_v23.json
python scripts/generate_figures.py --outputs results --out outputs/figures
```
