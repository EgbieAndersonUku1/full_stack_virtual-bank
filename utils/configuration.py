def parse_old_fernet_keys(raw_keys: str) -> list[str]:
    """
    Parse a comma-separated string of previous Fernet keys.

    Remove surrounding whitespace from individual keys.
    Return an empty list when no keys are configured.

    Preserve malformed empty entries so that cryptographic
    validation can detect and reject invalid configurations.
    """
    return (
        [key.strip() for key in raw_keys.split(",")]
        if raw_keys else []
    )
