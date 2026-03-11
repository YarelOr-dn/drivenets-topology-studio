show system revert-stack pre-check
-------------------------------------

**Minimum user role:** viewer

To display the result of the last revert-stack pre-check command.

**Command syntax: show system revert-stack pre-check**

**Command mode:** operational

**Note**

- If no revert-stack pre-check command was conducted prior to the show command, it will display an empty output.

**Example**
::

    Task ID:		    1688992839666
    Task status:		DONE
    Task start time:	2023-07-10 12:40:39
    Task finish time:	2023-07-10 12:40:39
    Pre-check result:	Failed
    Tests info:

    | Test Name            | Test Result   | Message                                                                                            |
    |----------------------+---------------+----------------------------------------------------------------------------------------------------|
    | Versioning Readiness | Passed        | Verified cluster readiness:                                                                        |
    |                      |               |    Secondary NCC, if present, is ready and operational.                                            |
    |                      |               |    The cluster is not currently performing any other versioning operation.                         |
    | Download In-Progress | Passed        | Verified packages download status:                                                                 |
    |                      |               |    There are no packages that are being downloaded to the cluster.                                 |
    | DNOS Target Version  | Passed        | Verified DNOS target version validity:                                                             |
    |                      |               |    DNOS target version is higher than current installed version                                    |
    | Stack Validity       | Failed        | Revert stack is empty                                                                              |
    | Disk Partition       | Passed        | Verified disk space and mount:                                                                     |
    |                      |               |    Cluster's nodes have enough space to perform versioning operations and all of them are mounted. |
    | Repo Replication     | Passed        | Verified repository synchronization:                                                               |
    |                      |               |    The standby NCC, if present, is synchronized over stack configurations and packages.            |
    | Packages Validity    | Passed        | Verified packages validity:                                                                        |
    |                      |               |    Stack packages' integrity checksum was verified.                                                |
    | Packages Signature   | Passed        | Verified packages signature:                                                                       |
    |                      |               |    DN-signed stack packages' have been verified to be sourced from DN.                             | 

.. **Help line:** Displays the result of the last revert stack pre-check command.

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2.1  | Command introduced                  |
+---------+-------------------------------------+
