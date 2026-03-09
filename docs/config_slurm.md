# SLURM profile

These commands were used to set up the SLURM profile on the bwForCluster Helix.

## Run cookiecutter template for SLURM profile

```shell
# Set to your username
profile_dir="/home/<username>/.config/snakemake"
mkdir -p "$profile_dir"

python3 -m cookiecutter $profile_dir https://github.com/Snakemake-Profiles/slurm.git
```

When prompted, set the following parameters, according to the requirements of your HPC system e.g., for <a href="https://wiki.bwhpc.de/e/Development/Python#Workflow_Management_Systems" target="_blank" rel="noopener">Helix</a>.

```text
[1/17] profile_name (slurm): slurm
[2/17] Select use_singularity 1
[3/17] Select use_conda 1
[4/17] jobs (500): 400 
[5/17] restart_times (0): 2
[6/17] max_status_checks_per_second (10): 1 
[7/17] max_jobs_per_second (10): 1 
[8/17] latency_wait (5): 30
[9/17] Select print_shell_commands 2
[10/17] sbatch_defaults (): 
[11/17] cluster_sidecar_help (Use cluster sidecar. NB! Requires snakemake >= 7.0! Enter 
to continue...): 
[12/17] Select cluster_sidecar (1): 1 
[13/17] cluster_name (): 
[14/17] cluster_jobname (%r_%w): 
[15/17] cluster_logpath (logs/slurm/%r/%j): 
[16/17] cluster_config_help (The use of cluster-config is discouraged. Rather, set 
snakemake CLI options in the profile configuration file (see snakemake documentation on 
best practices). Enter to continue...): 
[17/17] cluster_config (): 

```
