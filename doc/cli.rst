.. _cli:

The ``lcc`` command line tool
=============================

.. _cli_commands:

``lcc`` commands
----------------

In addition to the main sub command ``run``, the ``lcc`` command provides other sub commands that helps with the test
project and report:

- Show the tests hierarchy with metadata:

  .. code-block:: none

      $ lcc show
      * suite_1:
          - suite_1.test_1 (slow, priority:low)
          - suite_1.test_2 (priority:low)
          - suite_1.test_3 (priority:medium, #1235)
          - suite_1.test_4 (priority:low)
          - suite_1.test_5 (priority:high)
          - suite_1.test_6 (slow, priority:high)
          - suite_1.test_7 (priority:high)
          - suite_1.test_8 (priority:medium)
          - suite_1.test_9 (priority:medium)
      * suite_2:
          - suite_2.test_1 (priority:low)
          - suite_2.test_2 (priority:low)
          - suite_2.test_3 (priority:high)
          - suite_2.test_4 (priority:medium)
          - suite_2.test_5 (priority:low)
          - suite_2.test_6 (priority:low)
          - suite_2.test_7 (priority:medium)
          - suite_2.test_8 (slow, priority:low, #1234)
          - suite_2.test_9 (slow, priority:medium)

- Compare two reports:

  .. code-block:: none

      $ lcc diff reports/report-1/ report/
      Added tests (1):
      - suite_3.test_1 (passed)

      Removed tests (1):
      - suite_1.test_9 (failed)

      Status changed (2):
      - suite_2.test_3 (failed => passed)
      - suite_2.test_4 (passed => failed)

- Show available fixtures:

  .. code-block:: none

      $ lcc fixtures

      Fixture with scope session_prerun:
      +---------+--------------+------------------+---------------+
      | Fixture | Dependencies | Used by fixtures | Used by tests |
      +---------+--------------+------------------+---------------+
      | fixt_1  | -            | 1                | 1             |
      +---------+--------------+------------------+---------------+


      Fixture with scope session:
      +---------+--------------+------------------+---------------+
      | Fixture | Dependencies | Used by fixtures | Used by tests |
      +---------+--------------+------------------+---------------+
      | fixt_2  | fixt_1       | 1                | 2             |
      | fixt_3  | -            | 2                | 1             |
      +---------+--------------+------------------+---------------+


      Fixture with scope suite:
      +---------+--------------+------------------+---------------+
      | Fixture | Dependencies | Used by fixtures | Used by tests |
      +---------+--------------+------------------+---------------+
      | fixt_4  | fixt_3       | 0                | 2             |
      | fixt_6  | fixt_3       | 1                | 1             |
      | fixt_5  | -            | 0                | 0             |
      +---------+--------------+------------------+---------------+


      Fixture with scope test:
      +---------+----------------+------------------+---------------+
      | Fixture | Dependencies   | Used by fixtures | Used by tests |
      +---------+----------------+------------------+---------------+
      | fixt_7  | fixt_6, fixt_2 | 0                | 2             |
      | fixt_8  | -              | 0                | 1             |
      | fixt_9  | -              | 0                | 1             |
      +---------+----------------+------------------+---------------+

- Show statistics on tests based on metadata:

  .. code-block:: none

      $ lcc stats
      Tags:
      +------+-------+------+
      | Tag  | Tests | In % |
      +------+-------+------+
      | slow | 4     | 22%  |
      +------+-------+------+

      Properties:
      +----------+--------+-------+------+
      | Property | Value  | Tests | In % |
      +----------+--------+-------+------+
      | priority | low    | 8     | 44%  |
      | priority | medium | 6     | 33%  |
      | priority | high   | 4     | 22%  |
      +----------+--------+-------+------+

      Links:
      +-------+-------------------------+-------+------+
      | Name  | URL                     | Tests | In % |
      +-------+-------------------------+-------+------+
      | #1234 | http://example.com/1234 | 1     |  5%  |
      | #1235 | http://example.com/1235 | 1     |  5%  |
      +-------+-------------------------+-------+------+

      Total: 18 tests in 2 suites

- Show a generated report on the console:

  .. code-block:: none

      $ lcc.py report report/
      =================================== suite_1 ===================================
       OK  1 # test_1
       OK  2 # test_2
       OK  3 # test_3
       OK  4 # test_4
       OK  5 # test_5
       OK  6 # test_6
       OK  7 # test_7
       OK  8 # test_8
       OK  9 # test_9

      =================================== suite_2 ===================================
       OK  1 # test_1
       OK  2 # test_2
       OK  3 # test_3
       OK  4 # test_4
       OK  5 # test_5
       OK  6 # test_6
       OK  7 # test_7
       OK  8 # test_8
       OK  9 # test_9

      Statistics :
       * Duration: 0s
       * Tests: 18
       * Successes: 18 (100%)
       * Failures: 0

Also see the ``--help`` of these sub commands.

.. _cli_filters:

``lcc`` filtering arguments
---------------------------

``lcc`` sub commands ``run``, ``show``, ``stats``, ``report`` and ``diff`` take advantage of a powerful set of filtering
arguments:

.. code-block:: none

    Filtering:
      path                  Filter on test/suite path (wildcard character '*' can
                            be used)
      --desc DESC [DESC ...]
                            Filter on descriptions
      --tag TAG [TAG ...], -a TAG [TAG ...]
                            Filter on tags
      --property PROPERTY [PROPERTY ...], -m PROPERTY [PROPERTY ...]
                            Filter on properties
      --link LINK [LINK ...], -l LINK [LINK ...]
                            Filter on links (names and URLs)
      --disabled            Filter on disabled tests
      --passed              Filter on passed tests (only available with --from-
                            report)
      --failed              Filter on failed tests (only available with --from-
                            report)
      --skipped             Filter on skipped tests (only available with --from-
                            report)
      --enabled             Filter on enabled (non-disabled) tests
      --from-report FROM_REPORT
                            When enabled, the filtering is based on the given
                            report


The ``--from-report`` argument tells ``lcc`` to use tests from the report rather than from the project to build
the actual filter. The ``--passed``, ``--failed``, ``skipped`` can only be used in conjunction with ``--from-report``.
A typical application of this functionality is to re-run failed tests from a previous report:

.. code-block:: none

    $ lcc run --failed --from-report report/