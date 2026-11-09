# Kafka exactly-once

- Idempotent producer (`enable.idempotence=true`) removes duplicates from retries.
- Transactions write to several partitions and commit consumer offsets atomically.
- Consumers must use `isolation.level=read_committed` to skip aborted records.
- Exactly-once stops at Kafka: side effects in other systems still need idempotent handlers.
