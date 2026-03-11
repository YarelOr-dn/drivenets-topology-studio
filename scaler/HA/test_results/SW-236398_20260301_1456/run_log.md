[14:56:57] Starting FlowSpec HA tests on YOR_CL_PE-4
[14:56:57] VLAN=212 Spirent=10.99.212.1 DUT=10.99.212.2
[14:56:57] Results: /home/dn/SCALER/HA/test_results/SW-236398_20260301_1456
[14:56:57] Setting up Spirent: connect + reserve
[14:56:58] Port already reserved (reusing existing session)
[14:56:58] Creating Spirent BGP device
[14:56:59] Starting BGP peer
[14:57:42] Injecting 200 FlowSpec rules
[14:57:42] FlowSpec injection failed: FlowSpec not supported in this STC version: 500 Internal Server Error: STC exception: in create: unable to create unknown class "BgpFlowSpecRouteConfig": similar classes include BfdPortConfig, BfdRouterConfig, BgpEvpnAdRouteConfig, BgpEvpnMacAdvRouteConfig, BgpFlowSpecConfig, BgpIpv4RouteConfig, BgpIpv6FlowSpecConfig, BgpIpv6RouteConfig, BgpLsNodeConfig, BgpMvpnType1RouteConfig, BgpPortConfig, BgpRouterConfig, BgpTableRouteConfig, BgpVpnRouteConfig, BridgePortConfig, FcHostConfig, FcoeHostConfig, IgmpHostConfig, IgmpPortConfig, IgmpRouterConfig, IsisRouterConfig, L1PortConfig, LdpRouterConfig, LispRouterConfig, LispSiteConfig, MldRouterConfig, MplsTpConfig, OpenflowMeterConfig, OpflexPortConfig, OsePortConfig, Ospfv2RouterConfig, Ospfv3RouterConfig, PccLspConfig, PceLspConfig, PimRouterConfig, RipRouterConfig, and RsvpRouterConfig
Use ExaBGP or /BGP for FlowSpec injection.
Traceback (most recent call last):
  File "/home/dn/SCALER/SPIRENT/spirent_tool.py", line 1372, in <module>
    main()
  File "/home/dn/SCALER/SPIRENT/spirent_tool.py", line 1368, in main
    cmds[args.command](args)
  File "/home/dn/SCALER/SPIRENT/spirent_tool.py", line 736, in cmd_add_routes
    flowspec = stc.create(
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 383, in create
    data = self.createx(object_type, under, attributes, **kwattrs)
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/stchttp.py", line 408, in createx
    status, data = self._rest.post_request('objects', None, params)
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/resthttp.py", line 231, in post_request
    return self._handle_response(rsp)
  File "/home/dn/.local/lib/python3.10/site-packages/stcrestclient/resthttp.py", line 450, in _handle_response
    raise RestHttpError(rsp.status_code, rsp.reason, detail, code)
stcrestclient.resthttp.RestHttpError: 500 Internal Server Error: STC exception: in create: unable to create unknown class "BgpFlowSpecRouteConfig": similar classes include BfdPortConfig, BfdRouterConfig, BgpEvpnAdRouteConfig, BgpEvpnMacAdvRouteConfig, BgpFlowSpecConfig, BgpIpv4RouteConfig, BgpIpv6FlowSpecConfig, BgpIpv6RouteConfig, BgpLsNodeConfig, BgpMvpnType1RouteConfig, BgpPortConfig, BgpRouterConfig, BgpTableRouteConfig, BgpVpnRouteConfig, BridgePortConfig, FcHostConfig, FcoeHostConfig, IgmpHostConfig, IgmpPortConfig, IgmpRouterConfig, IsisRouterConfig, L1PortConfig, LdpRouterConfig, LispRouterConfig, LispSiteConfig, MldRouterConfig, MplsTpConfig, OpenflowMeterConfig, OpflexPortConfig, OsePortConfig, Ospfv2RouterConfig, Ospfv3RouterConfig, PccLspConfig, PceLspConfig, PimRouterConfig, RipRouterConfig, and RsvpRouterConfig

[14:57:42] Falling back to ExaBGP
[14:57:42] Using ExaBGP session: gobgp_test
[14:57:42] ExaBGP FlowSpec batch inject not yet implemented in orchestrator.
[14:57:42] ERROR: Setup failed. Exiting.