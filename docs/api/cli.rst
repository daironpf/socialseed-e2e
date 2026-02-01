API Reference - CLI Module
==========================

This section documents the command-line interface components.

Main CLI
--------

.. automodule:: socialseed_e2e.cli
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Commands
--------

The CLI provides the following commands:

init
~~~~

Initialize a new E2E testing project.

.. autofunction:: socialseed_e2e.cli.init

new-service
~~~~~~~~~~~

Create a new service with scaffolding.

.. autofunction:: socialseed_e2e.cli.new_service

new-test
~~~~~~~~

Create a new test module.

.. autofunction:: socialseed_e2e.cli.new_test

run
~~~

Execute E2E tests.

.. autofunction:: socialseed_e2e.cli.run

doctor
~~~~~~

Verify installation and dependencies.

.. autofunction:: socialseed_e2e.cli.doctor

config
~~~~~~

Show and validate configuration.

.. autofunction:: socialseed_e2e.cli.config
