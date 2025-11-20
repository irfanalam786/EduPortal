# Password Snapshot Ledger (`backend/data/decrypt.json`)

This document summarizes how EduPortal captures password transitions for auditability without touching application code.

## Purpose
- Preserve a history of every password mutation (user provisioning, admin reset, self-service change, DOB reset).
- Store both the plaintext credential and its SHA256 hash exactly as produced during the flow.
- Provide source context (e.g., `user_created`, `forgot_password`) and a UTC timestamp for downstream review or reporting.

## Location & Lifecycle
- File path: `backend/data/decrypt.json`
- Automatically created on first password event; manual pre-seeding with `[]` is optional.
- Uses the same backup-on-write mechanism as other JSON stores (`decrypt.json.backup`).

## Schema
`decrypt.json` is an array of objects with the following shape:

```
[
  {
    "username": "ADMIN",
    "source": "initialize_admin",
    "encrypted_value": "<sha256-hex>",
    "decrypted_value": "admin123",
    "timestamp": "2025-11-20T12:34:56Z"
  }
]
```

- `username`: Case-preserving key used during the triggering workflow.
- `source`: Identifier describing the flow (`initialize_admin`, `user_created`, `student_created`, `forgot_password`, `change_password`, etc.).
- `encrypted_value`: Output of the SHA256 routine at the moment the password was persisted.
- `decrypted_value`: The plaintext password issued to the end user.
- `timestamp`: ISO-8601 UTC string produced via `utils.get_current_timestamp()`.

## Operational Notes
- The ledger appends entries; it does not mutate or prune prior records. Archive the file periodically if size becomes a concern.
- Handle the file securely. It contains plaintext credentials and should never be committed to version control or shared outside authorized circles.
- For compliance resets, delete `decrypt.json`, restart the backend, and the next password mutation will recreate the file automatically.

## Verification Checklist
1. Start the Flask server.
2. Trigger a password event (e.g., add a user or run the “Forgot Password” flow).
3. Inspect `backend/data/decrypt.json` to confirm a new entry appears with the correct `source` and timestamps.

Keep this document updated whenever password-related workflows are added or renamed so auditors know how to interpret the ledger.

