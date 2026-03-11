request system integrity-report
--------------------------------

**Minimum user role:** admin

Generates a system integrity report. The integrity report contains metadata about files in the system that should not be modified as part of normal operation. The metadata includes: path, type, permission, ownership, sha256 hash of the file content and last modified time.

This command runs in the background.


**Command syntax: request system integrity report**

**Command mode:** operational

**Note**

- Start a background job to collect the integrity report.
- Immediately after using this command the prompt returns to enable the user to continue using the CLI while the report is being generated.


**Example**
::

	dnRouter# request system integrity-report


.. **Help line:** Generate system integrity-report file

**Command History**

+-------------+-----------------------+
|             |                       |
| Release     | Modification          |
+=============+=======================+
| 19.1        | Command introduced    |
+-------------+-----------------------+
