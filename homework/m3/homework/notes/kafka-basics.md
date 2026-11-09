# Kafka basics

- A topic is split into partitions; order is guaranteed only inside one partition.
- The record key picks the partition (hash of the key), so all events for one key stay in order.
- Retention is by time or size, not by consumption: consumers can re-read old data.
- Replication factor 3 with `min.insync.replicas=2` and `acks=all` survives one broker loss without data loss.
