# Kafka summary

- Order is guaranteed only within a partition; the record key picks the partition.
- Replication factor 3 + `min.insync.replicas=2` + `acks=all` survives one broker loss.
- In a group each partition has one consumer; offsets live in `__consumer_offsets`.
- Alert on consumer lag that keeps growing; prefer cooperative sticky rebalancing.
- Exactly-once = idempotent producer + transactions + `read_committed`, and it ends at Kafka.

Sources: kafka-basics.md, kafka-consumer-groups.md, kafka-exactly-once.md
