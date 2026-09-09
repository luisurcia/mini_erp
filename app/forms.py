"""Shared WTForms helpers used across more than one blueprint's forms."""


def optional_int(value):
    """Coerce a select value to int, or None for the empty placeholder
    option — so an Optional() field accepts "no choice" instead of
    blowing up on int("")."""
    return int(value) if value not in ("", None) else None
