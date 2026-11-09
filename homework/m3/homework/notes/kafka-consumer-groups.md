# Kafka consumer groups

- Each partition is read by at most one consumer in a group; extra consumers stay idle.
- Offsets are committed per group and partition in `__consumer_offsets`.
- A rebalance happens when a consumer joins, leaves or misses `max.poll.interval.ms`.
- Cooperative sticky assignment avoids stop-the-world rebalances.
- Consumer lag = log end offset − committed offset; alert on lag that keeps growing.
