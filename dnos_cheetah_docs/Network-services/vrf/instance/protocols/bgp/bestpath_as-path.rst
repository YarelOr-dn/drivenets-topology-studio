network-services vrf instance protocols bgp bestpath as-path
------------------------------------------------------------

**Minimum user role:** operator

To configure how BGP treats the AS path in best path selection:

**Command syntax: bestpath as-path {confed, multipath-relax, ignore}**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp
- protocols bgp

**Note**

- These parameter options are not mutually exclusive. You may configure all options. These options are disabled by default.

**Parameter table**

+-----------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter       | Description                                                                      | Range   | Default |
+=================+==================================================================================+=========+=========+
| confed          | specifies that the length of confederation path sets and sequences should be     | Boolean | False   |
|                 | taken into account during the BGP best path decision process                     |         |         |
+-----------------+----------------------------------------------------------------------------------+---------+---------+
| multipath-relax | specifies that BGP decision process should consider paths of equal as-path       | Boolean | False   |
|                 | length candidates for multipath computation. Without the set, the entire as-path |         |         |
|                 | must match for multipath computation                                             |         |         |
+-----------------+----------------------------------------------------------------------------------+---------+---------+
| ignore          | Ignore the AS path length when selecting the best path. The default is to use    | Boolean | False   |
|                 | the AS path length and prefer paths with shorter length.                         |         |         |
+-----------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# bestpath as-path confed
    dnRouter(cfg-protocols-bgp)# bestpath as-path multipath-relax
    dnRouter(cfg-protocols-bgp)# bestpath as-path ignore


**Removing Configuration**

To revert the best path AS path instruction to default (disable):
::

    dnRouter(cfg-protocols-bgp)# no bestpath as-path confed

::

    dnRouter(cfg-protocols-bgp)# no bestpath as-path multipath-relax

::

    dnRouter(cfg-protocols-bgp)# no bestpath as-path ignore

::

    dnRouter(cfg-protocols-bgp)# no bestpath as-path

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
