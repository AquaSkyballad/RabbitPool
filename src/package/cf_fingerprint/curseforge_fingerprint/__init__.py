"""CurseForge Fingerprint - Python binding for the CurseForge fingerprinting algorithm.

This module provides functionality to compute file fingerprints compatible with
the CurseForge platform. The algorithm uses a MurmurHash3 variant that filters
whitespace characters (Tab, LF, CR, Space) before computing the hash, producing
results identical to the CurseForge platform's fingerprinting system.

Functions:
    fingerprint: Compute the fingerprint of a file by path.
    fingerprint_bytes: Compute the fingerprint of in-memory bytes data.

Example:
    >>> from curseforge_fingerprint import fingerprint
    >>> result = fingerprint("/path/to/mod.jar")
    >>> print(result)
    3608199863

    >>> from curseforge_fingerprint import fingerprint_bytes
    >>> result = fingerprint_bytes(b"some data")
    >>> print(result)
    3493718775
"""

from curseforge_fingerprint._core import fingerprint, fingerprint_bytes

__all__ = ['fingerprint', 'fingerprint_bytes']
__version__ = '1.0.0'
