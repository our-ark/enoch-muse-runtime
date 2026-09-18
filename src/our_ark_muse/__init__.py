"""our_ark_muse: Muse runtime provider for Enoch (MuseEnoch PoC).

Route B registration (no install needed): Enoch's provider registry
discovers the ``OUR_ARK_PROVIDERS`` descriptor when this module is listed
as a ``[[runtime_dependencies]]`` entry (``import_name = "our_ark_muse"``)
in ``genesis.toml``.

Route A registration (installed package): the ``our_ark.providers``
entry point ``runtime.muse = our_ark_muse:create_provider`` in
``pyproject.toml``.
"""

from our_ark_muse.core import MuseRuntime, create_provider, mailbox_configured

OUR_ARK_PROVIDERS = (
    {
        "kind": "runtime",
        "name": "muse",
        "factory": create_provider,
        "supports": mailbox_configured,
    },
)

__all__ = [
    "MuseRuntime",
    "create_provider",
    "mailbox_configured",
    "OUR_ARK_PROVIDERS",
]
