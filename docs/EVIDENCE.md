# Evidence for the manuscript

In this guide, we identify the records that support the numerical results and explain how the stage annotations relate to our proposed stochastic reliability model. The evidence comes from the public Tracebench manifest. For each of the 646 selected trajectories, the source path begins with `swe_raw/` and the manifest supplies the stage annotations and terminal task outcome. Together, the selected trajectories cover 426 task identifiers and 47 repositories. The validation section presents the sampling and prediction procedures. The remaining sections give the result tables and identify the corresponding figures.

## Validation and provenance

For the uncertainty estimates and the predictive comparison, we use task identifiers and repository identifiers to define the units of analysis. For the primary uncertainty estimates, the application resamples whole tasks with their associated trajectories in 2,000 bootstrap replications using seed 20260918. The predictive comparison uses five folds. First, the application counts the trajectories from each repository and orders the repositories by decreasing trajectory count. Next, the Secure Hash Algorithm (SHA-256) digest of the repository identifier determines the order of repositories with equal counts. Then, the application assigns each repository to the fold that currently contains the fewest trajectories.

Afterward, the five folds contain 130, 129, 129, 129, and 129 trajectories from 9, 9, 9, 10, and 10 repositories, respectively. Finally, the application trains on the other folds and evaluates its predictions on the repositories in the held out fold. Each repository belongs to one fold. Thus, the [repository assignments](../results/repository_folds.json) identify the repositories in each test fold, and the stored run gives the corresponding trajectory counts.

For the numerical check, the application uses seed 20260918 and simulates 200,000 trajectories for each observed stage count. Agreement with the analytical recursion checks the implementation of the fitted process. This is because the simulation uses the same transition probabilities as the analytical recursion and introduces no further observed trajectories. In the [provenance record](../provenance/provenance.json), the execution identifiers come from the original archive. Those identifiers have no independent verification. For the recorded results, the verification command in the [README](../README.md) provides a separate check against the frozen reference values.

## Interpretation of the results

In this section, we describe how stage annotations qualify the final task outcome and how agent groups enter the comparison. A solved task can contain a stage with an incorrect annotation. However, the final task outcome identifies neither the first occurrence of an incorrect annotation nor its persistence across stages. Thus, two trajectories with the same final task outcome can differ in the sequence of stage annotations. To solve this issue, we report entry, persistence, return, and recurrence alongside the position of an incorrect annotation and the final stage annotation.

At each stage, the symbols `N` and `I` denote the absence and presence of an incorrect annotation, respectively. For immediate recurrence, the denominator counts returns from `I` to `N` for which the trajectory contains one more stage. Within that set, the numerator counts returns followed immediately by another incorrect annotation, which gives the pattern `I → N → I`. A later incorrect annotation alone does not satisfy this condition. Thus, the observable transitions describe changes in stage annotations without establishing confirmed correctness, latent failure, detected failure, or candidate repair.

For each agent group, the estimates describe the tasks and framework configuration represented in its recorded trajectories. In fact, the three groups differ in task mix and source group, which limits the comparison of their transition estimates. The analysis involves neither paid agent execution nor matched fault injection. A controlled comparison requires matched tasks and conditions. Compared with the homogeneous transition model, the position aware model gives lower calibration error on held out repositories. For the Brier score, it can be observed that the aggregate baseline gives the lower estimate, but the paired uncertainty interval includes zero. Thus, the recorded predictions do not establish a consistent Brier score advantage for the position aware model over the aggregate baseline.

## Result tables

In the table below, we identify the stored output that supports each comparison and indicate what the reader can recover from each file. For a new run, the application writes its aggregate estimates, repository assignments, and seven generated tables to the selected output directory. Alongside the generated tables, the distribution includes four archived manuscript tables with descriptive breakdowns and uncertainty estimates. For the predictive comparison, we report mean absolute error (MAE), root mean square error (RMSE), and expected calibration error (ECE) alongside the Brier score and log loss. The correspondence between the empirical claims and the stored files is as follows.

| Evidence | Stored file | Quantities or use |
| --- | --- | --- |
| Corpus and terminal outcome | [Aggregate results](../results/results_v23.json) | 646 trajectories, 475 solved, three agent frameworks, overall estimates and confidence intervals |
| Agent groups | [Agent summary](../results/tables/agent_summary.csv) | Counts, solve rates, uncertainty intervals, and transition estimates by framework |
| Incorrect annotation and terminal outcome | [Conditional outcomes](../results/tables/incorrect_outcome.csv) | Solved and unsolved counts with and without an incorrect annotation, including the 311 trajectories with at least one incorrect stage |
| Workflow position | [Incorrect stages by position](../results/tables/incorrect_position.csv), [position parameters](../results/tables/position_parameters.csv) | Counts by workflow interval and fitted transition probabilities |
| Workflow length | [Workflow measures](../results/tables/workflow_dynamics.csv), [final stage by stage count](../results/tables/final_incorrect_by_stage_count.csv) | Distributions of actions and stage counts, final incorrect annotation by trajectory length |
| Observable transitions | [Transition counts](../results/tables/observed_transitions.csv) | Counts and probabilities for the four transitions between N and I |
| Return and recurrence | [Return and recurrence](../results/tables/return_recurrence.csv) | Return, persistence, immediate recurrence, repeated episodes, and solve rate after an observed return |
| Source groups | [Source composition](../results/tables/source_groups.csv) | Counts and outcomes by source group |
| Held out prediction | [Predictive metrics](../results/tables/heldout_validation.csv), [paired Brier score estimates](../results/results_v23.json) | MAE, RMSE, Brier score, log loss, ECE, mean prediction, and paired uncertainty intervals |
| Numerical agreement | [Analytical and simulated probabilities](../results/tables/analytical_monte_carlo.csv) | Final incorrect annotation probability by stage count, absolute differences, and simulation standard errors |

For the archived manuscript tables, we retain four descriptive breakdowns, namely, conditional outcomes, workflow measures, return and recurrence, and source composition. The above table gives a direct link to each archived file. In addition, the [analysis settings](../config/analysis_config.json) give the seeds and replication counts used for uncertainty estimates and simulation. To verify the stored run, the numerical check compares the input digest, corpus counts, transition estimates, predictive metrics, fold sizes, paired Brier score differences, and Monte Carlo agreement with the frozen reference values.

## Figure correspondence

In the table below, we identify the manuscript figure and the filename written by the figure generation script. For the regenerated figures, the filenames retain the numbering assigned by the analysis application before the manuscript figures were ordered. The first column links to the manuscript layout. To locate the corresponding generated plot, the reader can use the filename in the second column as follows.

| Manuscript figure | Generated filename |
| --- | --- |
| [Figure 1](../publication_figures/Figure1_reliability_framework_approved.png) | `Figure1_reliability_framework_v23.png` |
| [Figure 2](../publication_figures/Figure2_stage_count_distribution.png) | `Figure2_stage_count_distribution_v23.png` |
| [Figure 3](../publication_figures/Figure3_incorrect_stage_outcomes.png) | `Figure4_incorrect_stage_outcomes_v23.png` |
| [Figure 4](../publication_figures/Figure4_incorrect_stage_position.png) | `Figure5_incorrect_stage_position_v23.png` |
| [Figure 5](../publication_figures/Figure5_final_incorrect_by_stage_count.png) | `Figure9_final_incorrect_by_stage_count_v23.png` |
| [Figure 6](../publication_figures/Figure6_observed_transition_map.png) | `Figure6_observed_transition_map_v23.png` |
| [Figure 7](../publication_figures/Figure7_return_recurrence_serif.pdf) · [editable source](../publication_figures/Figure7_return_recurrence_serif.tex) | `Figure7_return_recurrence_v23.png` |
| [Figure 8](../publication_figures/Figure8_agent_solve_rates.png) | `Figure3_agent_solve_rates_v23.png` |
| [Figure 9](../publication_figures/Figure9_agent_transition_profiles.png) | `Figure8_agent_transition_profiles_v23.png` |
| [Figure 10](../publication_figures/Figure10_position_aware_parameters.png) | `Figure10_position_aware_parameters_v23.png` |
| [Figure 11](../publication_figures/Figure11_analytical_monte_carlo.png) | `Figure11_analytical_monte_carlo_v23.png` |
| [Figure 12](../publication_figures/Figure12_sensitivity.png) | `Figure12_sensitivity_v23.png` |

As shown in Figure 1, our proposed stochastic reliability model distinguishes five states that describe the condition of the software candidate. In Figures 6 and 7, the diagrams describe changes in the observed stage annotations and the conditions for counting recurrence. As discussed above, an unmarked stage alone cannot establish the condition of the software candidate. The generated plots reproduce the reported quantities using layouts that differ from the manuscript layouts. Thus, an observed return to an unmarked stage supplies evidence of a change in annotation, while confirmation of recovery requires evidence about the repaired candidate.
