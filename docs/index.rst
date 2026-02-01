socialseed-e2e Documentation
============================

**socialseed-e2e** is a comprehensive End-to-End (E2E) testing framework for REST APIs built with Python and Playwright.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   configuration
   writing-tests
   cli-reference

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/core
   api/cli
   api/models
   api/utils

.. toctree::
   :maxdepth: 1
   :caption: Development

   testing-guide
   mock-api

.. toctree::
   :maxdepth: 1
   :caption: Additional Resources

   changelog
   license


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Features
--------

- **Hexagonal Architecture**: Clean separation between core framework and service-specific code
- **Playwright Integration**: Modern HTTP client with automatic retries and rate limiting
- **YAML Configuration**: Centralized configuration management
- **Dynamic Test Discovery**: Automatic test module loading and execution
- **Rich CLI**: Beautiful command-line interface with helpful feedback
- **Type Safety**: Full type hints support with Pydantic models

Quick Links
-----------

- **Source Code**: https://github.com/daironpf/socialseed-e2e
- **Issue Tracker**: https://github.com/daironpf/socialseed-e2e/issues
- **PyPI**: https://pypi.org/project/socialseed-e2e/

License
-------

This project is licensed under the MIT License - see the :doc:`license` page for details.
