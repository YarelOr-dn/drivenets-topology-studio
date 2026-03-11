show system target-stack load history
-------------------------------------

**Command syntax: show system target-stack load history**

**Description:** Displays target stack load progress history.

**CLI example:**
::

    dnRouter# show system target-stack load history

    url:                http://172.16.100.12/packages/ufi-wbx-fw-17-0.tar
    Task ID:            140
    Task status:        complete
    Task start time:    11-Dec-2019 13:58:14 UTC
    Task elapsed time:  02:10:00
    Finish time:        11-Dec-2019 16:08:14 UTC

    url:                http://172.16.100.12/packages/drivenets_stratax_1.1.0.tar
    Task ID:            144
    Task status:        complete
    Task start time:    11-Dec-2019 13:44:14 UTC
    Task elapsed time:  02:20:00
    Finish time:        11-Dec-2019 16:04:14 UTC


**Command mode:** operational

**TACACS role:** viewer

**Note:**


**Help line:** Displays system target stack load progress history.

**Outputs table:**

+----------------------+-------------------------+----------+
| Parameter            | Values                  | Comments |
+======================+=========================+==========+
| Task status          | in-progress             |          |
|                      | completed               |          |
|                      | failed                  |          |
|                      | canceled                |          |
+----------------------+-------------------------+----------+