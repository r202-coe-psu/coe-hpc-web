Title: Scheduled Maintenance Window — GPU Partition
Date: 2026-02-03 10:00
Category: Maintenance
Slug: scheduled-maintenance-gpu-partition

The `gpu` partition will be offline for firmware updates and rack cooling
maintenance. During this window:

- New jobs submitted to `gpu` will stay `PENDING` until maintenance ends.
- Running jobs on `compute` and `bigmem` are **not** affected.
- Please checkpoint long-running GPU jobs beforehand where possible.

We'll post an update here once the partition is back online — track real-time
status any time on the [homepage](/).
