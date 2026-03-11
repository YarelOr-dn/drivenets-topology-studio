show high-availability policy
-----------------------------

**Command syntax: show high-availability policy**  { ncc [ncc-id] | ncp [ncp-id] | ncf [ncf-id] } container [container-name] process [process-name] 

**Description:** show high-availability policy information

ncc [ncc-id] | ncp [ncp-id] | ncf [ncf-id] -  filter to display information only of specific node
container [container-name] - filter to display information only of specific container
process [process-name] - filter to display information only of specific process

**CLI example:**
::

	dnRouter# show high-availability policy process routing:bgpd
    
    | Type | Id | Container         | Process name      | State  | Up/Downtime        | Max failures | Mitigations | Failures period / Remaining | Violation action |
    |------+----+-------------------+-------------------+--------+--------------------+--------------+-------------+-----------------------------+------------------|
    | NCC  | 0  | Routing-Engine    | routing:bgpd      | up     | 7 days, 9:07:35    |            2 |           1 | 30min /  00:07:35           | hold-down        |
    


    dnRouter# show high-availability policy

    dnRouter# show high-availability policy ncc 0

    dnRouter# show high-availability policy contianer node-manager

    dnRouter# show high-availability policy ncf 1 contianer node-manager

    dnRouter# show high-availability policy ncc 1 contianer routing-engine process routing:bgpd

    dnRouter# show high-availability policy ncc 0 process routing:bgpd



**Command mode:** operational

**TACACS role:** viewer

**Note:**
- Filter combanation should only be allowed according for Cluster type. For example, in SA there shouldn't be ncf filter.

- If filter result in no processes, empty outout is expected

**Help line:** show system detailed information

**Parameter table:**

+----------------+--------------------------------------------------------------+---------------+
| Parameter      | Values                                                       | Default value |
+================+==============================================================+===============+
| Node-name      | ncp                                                          |               |
|                |                                                              |               |
|                | ncc                                                          |               |
|                |                                                              |               |
|                | ncf                                                          |               |
+----------------+--------------------------------------------------------------+---------------+
| ncc-id         | 0-1                                                          |               |
+----------------+--------------------------------------------------------------+---------------+
| ncp-id         | 0-(Cluster type max NCP number-1)                            |               |
+----------------+--------------------------------------------------------------+---------------+
| ncf-id         | 0-(Cluster type max NCF number-1)                            |               |
+----------------+--------------------------------------------------------------+---------------+
| container-name | Any container from process list relative to the node name    |               |
+----------------+--------------------------------------------------------------+---------------+
| process-name   | Any process from process list                                |               |
+----------------+--------------------------------------------------------------+---------------+
