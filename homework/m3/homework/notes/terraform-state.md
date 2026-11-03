# Terraform state

- Keep state remote (S3 + DynamoDB lock, or the cloud backend), never in git.
- One state per environment and per component keeps the blast radius small.
- Use `terraform state mv` / `moved` blocks for renames instead of destroy and recreate.
