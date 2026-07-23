"""Built-in check catalog.

Importing this package imports every check module, which runs the ``@check``
decorators and populates the registry in :mod:`gcphelpit.catalog`.
"""

from . import cost, iam, reliability, security  # noqa: F401
