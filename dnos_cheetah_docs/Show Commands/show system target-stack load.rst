show system target-stack load
-----------------------------

**Command syntax: show system target-stack load**

**Description:** Displays current target stack load progress.

**CLI example:**
::

    dnRouter# show system target-stack load

    url:                http://172.16.100.12/packages/ufi-wbx-fw-17-0.tar
    Task ID:            140
    Task status:        in-progress
    Progress:           56%
    Task start time:    11-Dec-2019 13:58:14 UTC
    Task elapsed time:  01:42:37

    url:                http://172.16.100.12/packages/drivenets_stratax_1.1.0.tar
    Task ID:            144
    Task status:        in-progress
    Progress:           48%
    Task start time:    11-Dec-2019 13:44:14 UTC
    Task elapsed time:  01:56:37


**Command mode:** operational

**TACACS role:** viewer

**Note:**


**Help line:** Displays system target stack load progress.

**Outputs table:**

+----------------------+-------------------------+----------+
| Parameter            | Values                  | Comments |
+======================+=========================+==========+
| Task status          | in-progress             |          |
|                      | completed               |          |
|                      | failed                  |          |
|                      | canceled                |          |
+----------------------+-------------------------+----------+