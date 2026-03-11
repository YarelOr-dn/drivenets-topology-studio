show system target-stack pre-check
-------------------------------------

**Minimum user role:** viewer

To display the result of the last target-stack pre-check command.

**Command syntax: show system target-stack pre-check**

**Command mode:** operational

**Note**

- If no target-stack pre-check command was conducted prior to the show command, it will display an empty output.

**Example**
::

    Task ID:		    1688987412517
    Task status:		DONE
    Task start time:	2023-07-10 11:10:12
    Task finish time:	2023-07-10 11:10:12
    Pre-check result:	Failed
    Tests info:

    | Test Name            | Test Result   | Message                                                                                 |
    |----------------------+---------------+-----------------------------------------------------------------------------------------|
    | Disk Partition       | Failed        | ncc0: Partition 'docker' is lacking space: required: 500.00MB, available: 9B            |
    |                      |               | ncc1: Partition 'docker' is lacking space: required: 500.00MB, available: 9B            |
    | Packages Signature   | Failed        | Package: dnos_mock_package_1, authenticity: integrity-failed                            |
    | Versioning Readiness | Passed        | Verified cluster readiness:                                                             |
    |                      |               |    Secondary NCC, if present, is ready and operational.                                 |
    |                      |               |    The cluster is not currently performing any other versioning operation.              |
    | Download In-Progress | Passed        | Verified packages download status:                                                      |
    |                      |               |    There are no packages that are being downloaded to the cluster.                      |
    | DNOS Target Version  | Passed        | Verified DNOS target version validity:                                                  |
    |                      |               |    DNOS target version is higher than current installed version                         |
    | Stack Validity       | Passed        | Verified stack validity:                                                                |
    |                      |               |    Stack is not empty.                                                                  |
    |                      |               |    Target stack will not cause DNOS deletion.                                           |
    |                      |               |    All stack components' dependencies are met.                                          |
    | Repo Replication     | Passed        | Verified repository synchronization:                                                    |
    |                      |               |    The standby NCC, if present, is synchronized over stack configurations and packages. |
    | Packages Validity    | Passed        | Verified packages validity:                                                             |
    |                      |               |    Stack packages' integrity checksum was verified.                                     |

.. **Help line:** Displays the result of the last target stack pre-check command.

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2.1  | Command introduced                  |
+---------+-------------------------------------+
