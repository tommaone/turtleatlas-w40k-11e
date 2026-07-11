# Findings

Verified research results, per faction. Human-readable summaries with engine data backing.

Not part of the MCP server — these are static analysis docs.

## Structure

```
findings/
  <faction>/
    <topic>.md
```

## Standards

- Every finding must cite engine data or explicit reasoning
- No speculation marked as fact — use `🟢 FACTS`, `🟡 USE CASES`, `🟠 CONSTRAINTS`, `🔴 STRATEGY` tiers
- Include an assumption registry
- Pass Shredder review before committing
