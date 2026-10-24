TheBitLab technical documentation
=================================

This Sphinx entry point exposes the main Python modules through autodoc.
The authoritative Italian guides remain Markdown documents in the repository:

* `Cornice didattica <https://github.com/TheBitPoets/2cornot2c/blob/main/doc/CORNICE_DIDATTICA.md>`_
* `Guida MVP 2026/2027 <https://github.com/TheBitPoets/2cornot2c/blob/main/doc/MVP_2026_2027.md>`_
* `Architettura MVP <https://github.com/TheBitPoets/2cornot2c/blob/main/doc/ARCHITETTURA_MVP.md>`_
* `Architettura frontend <https://github.com/TheBitPoets/2cornot2c/blob/main/doc/FRONTEND_ARCHITECTURE.md>`_
* `Catalogo delle fonti <https://github.com/TheBitPoets/2cornot2c/blob/main/doc/COURSE_SOURCE_CATALOG.md>`_
* `Contratto dei runtime plugin <https://github.com/TheBitPoets/2cornot2c/blob/main/doc/architecture/runtime-plugin-contract.md>`_

Runtime implementations
-----------------------

TheBitLab keeps runtime implementations outside the platform core. Their own
repositories are the authoritative source for domain-specific installation,
teaching and API documentation.

* `Romeo · Python e robotica <https://github.com/TheBitPoets/romeo/blob/main/docs/index.md>`_
  — reference implementation of a ``runtime_plugin.v1`` adapter with
  ``sandbox-plan.v1``, deterministic simulation and an external Course Bundle.

.. toctree::
   :maxdepth: 2
   :caption: Python API

   modules
