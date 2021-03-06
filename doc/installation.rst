.. _`installation`:

Installation
============

lemoncheesecake can be installed through pip:

.. code-block:: none

    $ pip install lemoncheesecake

The following reporting backends are supported:

- ``console``: available by default

- ``json``: available by default

- ``html``: available by default

- ``xml``: available through the extra of the same name

- ``junit``: available through the extra of the same name

- ``reportportal``: available through the extra of the same name

- ``slack``: available through the extra of the same name

lemoncheesecake can be installed with an extra like this:

.. code-block:: shell

    $ pip install lemoncheesecake[xml]

Multiple extras can be specified:

.. code-block:: shell

    $ pip install lemoncheesecake[junit,reportportal]
