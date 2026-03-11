segment-routing mpls policy binding-sid
---------------------------------------

**Command syntax: binding-sid { dynamic | [label-value] }**

**Description:** Configure a binding sid for the SR-TE policy
Binding sid represnt forwarding traffic into the SR-TE policy, and can be used in SR-TE policies to to steer traffic into a specific policy.
Binding sid has local significant only
Default system behavior is binding-sid dynamic. Binding sid is allocated by internal DNOS logic and remain constant throughout policy lifetime.
User may configure binding sid to a specific label value, label value must be within global SRLB label block range.


**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# protcols
	dnRouter(cfg-protocols)# segment-routing
	dnRouter(cfg-protocols-sr)# mpls
	dnRouter(cfg-protocols-sr-mpls)# policy POL_1
	dnRouter(cfg-sr-mpls-policy)# binding-sid dynamic

	dnRouter(cfg-protocols-sr-mpls)# policy POL_2
	dnRouter(cfg-sr-mpls-policy)# binding-sid 23442

	dnRouter(cfg-sr-mpls-policy)# no binding-sid


**Command mode:** config

**TACACS role:** operator

**Note:**

- [label-value] must be within global SRLB label block range.

- If user configured value match an already allocated label, policy will be down due to "invalid binding-sid - cannot allocate label"

- no command return binding-sid to default value

**Help line:** Configure binding sid for the SR-TE policy

**Parameter table:**

+-------------+------------------------+----------------+
| Parameter   | Values                 | default value  |
+=============+========================+================+
| label-value | 256..1048575           |                |
+-------------+------------------------+----------------+
