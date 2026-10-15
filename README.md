# R3LA

## Description

R3LA is a repository for reproducing and evaluating reinforcement learning algorithms for robotic systems.

Different algorithms are maintained in separate branches to keep implementations isolated and easy to compare.

## Repository Structure

A typical project structure is:

```text
r3-la/
├── config/         # Isaac Sim Extension config
├── docs/           # Documentation and design notes
├── scripts/        # Training, evaluation, and utility scripts
├── src/            # Source code
    ├── r3la/
        ├── tasks/  # Motion task definition
├── test/           # Unit and integration tests
└── benchmark/      # Performance and algorithm benchmarks
```

## Dependicies
Current Use Isaaclab 3.0.0EA version, which can be installed following [IsaacLab Installation](https://isaac-sim.github.io/IsaacLab/v3.0.0-EA/source/setup/installation/index.html#installation-method-uv)

Adding custom learning library with [Adding your own learning library](https://isaac-sim.github.io/IsaacLab/v3.0.0-EA/source/how-to/add_own_library.html)


## Branch Organization

Each branch contains the implementation of a specific reinforcement learning algorithm or experiment.

Please switch to the corresponding branch before building, training, or evaluating an algorithm.