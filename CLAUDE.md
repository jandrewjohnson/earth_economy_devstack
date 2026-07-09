# earth_economy_devstack

Umbrella repo for the earth-economy modeling stack: install tooling, docs, specs,
and scenario definitions that coordinate the other repos (hazelbean, seals,
global_invest, gtap_invest, etc.).

This repo mostly holds documentation and specifications rather than a single
importable package. Code utilities belong in the appropriate library (hazelbean
for anything general).

Shared devstack guidance (reuse rule + ownership map + conventions pointer):

@devstack_guidance.md

## Notes

- Scenario definitions / specs live here; the hazelbean-side parser implementation
  consumes them.
- Conda-based stack. Activate the relevant project environment before running code.
