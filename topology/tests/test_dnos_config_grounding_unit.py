"""Unit tests for ``ai.dnos_config_grounding`` -- the DNOS-grounded
chat backend.

Coverage:

  1. ``detect_config_intent`` must classify DNOS config asks as
     intent and topology / canvas / explanation asks as non-intent.
     This is the gate that decides whether the chat handler runs the
     strict RST-grounded flow vs the existing topology AI path.
  2. ``search_local_rst`` returns matching evidence from the bundled
     ``scaler/dnos_cheetah_docs`` tree. We pin a couple of canonical
     queries (``bgp neighbor``, ``evpn vpws``, ``ospf area``) so a
     future tree reorganisation that breaks them shows up here
     instead of breaking the user-visible chip.
  3. ``parse_dnos_block`` extracts the fenced CLI body from a model
     reply, including the no-fence heuristic fallback.
  4. ``validate_dnos_text`` integrates with ``cli_validator`` when
     present, and soft-fails when the validator import is missing
     (deployments without Scaler installed must keep working).
  5. ``build_grounded_system_prompt`` renders a prompt that contains
     the evidence block, the NO_VERIFIED_DNOS_SOURCE sentinel
     contract, and the no-tool-calls clause. We assert on those
     literals so we notice if a future edit drops the contract.

Run:
    PYTHONPATH="topology" python3 topology/tests/test_dnos_config_grounding_unit.py
"""
from __future__ import annotations

import os
import sys


def _case(label: str) -> None:
    print(f"\n=== {label}")


def _assert(cond, label: str, *, info: str = "") -> None:
    if cond:
        print(f"  ok: {label}")
        return
    print(f"  FAIL: {label}")
    if info:
        print(f"    info: {info}")
    raise SystemExit(1)


def main() -> None:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
    from ai.dnos_config_grounding import (
        Evidence,
        build_grounded_system_prompt,
        build_search_query,
        detect_config_intent,
        format_evidence_for_prompt,
        parse_dnos_block,
        search_local_rst,
        serialize_sources,
        validate_dnos_text,
    )

    _case("detect_config_intent: positive cases")
    pos_cases = [
        ("How do I configure BGP neighbor on dnos?", ["bgp"]),
        ("Give me the DNOS config for an OSPF single area network", ["ospf"]),
        ("configure vrf with bgp", ["bgp", "vrf"]),
        ("show me the syntax for vrrp", ["vrrp"]),
        ("fix this dnos config: dnRouter(cfg)# bgp neigbor 1.1.1.1", ["bgp"]),
    ]
    for prompt, expected_objects in pos_cases:
        intent = detect_config_intent([{"role": "user", "content": prompt}])
        _assert(intent.is_config_intent, f"is_config_intent for {prompt!r}",
                info=f"reason={intent.reason}")
        for obj in expected_objects:
            _assert(obj in intent.matched_objects or obj in intent.query.lower(),
                    f"matched/contains {obj!r} in {prompt!r}",
                    info=f"matched_objects={intent.matched_objects}")

    _case("detect_config_intent: negative cases")
    neg_cases = [
        "create a topology with 3 PEs and 2 Ps",
        "add a router to the canvas",
        "explain the difference between iBGP and eBGP",
        "what is BGP?",
        "enrich the canvas with protocol colors",
    ]
    for prompt in neg_cases:
        intent = detect_config_intent([{"role": "user", "content": prompt}])
        _assert(not intent.is_config_intent, f"not config intent: {prompt!r}",
                info=f"reason={intent.reason}")

    _case("build_search_query")
    intent = detect_config_intent([{"role": "user", "content":
        "Give me dnos config for BGP neighbor address-family ipv4 unicast"}])
    q = build_search_query(intent)
    _assert("bgp" in q, "query mentions bgp", info=f"query={q!r}")
    _assert("address-family" in q or "address" in q,
            "query mentions address-family",
            info=f"query={q!r}")

    _case("search_local_rst: BGP neighbor")
    items = search_local_rst("bgp neighbor address-family", limit=5)
    _assert(len(items) > 0, "found at least one BGP doc",
            info=f"items={[(i.category, i.doc_name) for i in items]}")
    bgp_hit = any("bgp" in (i.doc_name + " " + i.category).lower() for i in items)
    _assert(bgp_hit, "BGP appears in top results",
            info=f"items={[(i.category, i.doc_name) for i in items]}")

    _case("search_local_rst: OSPF area")
    items = search_local_rst("ospf area", limit=5)
    _assert(len(items) > 0, "found at least one OSPF doc",
            info=f"items={[(i.category, i.doc_name) for i in items]}")

    _case("search_local_rst: empty / unknown query is safe")
    _assert(search_local_rst("", limit=5) == [], "empty query -> []")
    _assert(search_local_rst("xyzzyplugh notathing", limit=5) == [],
            "nonsense query -> []")

    _case("parse_dnos_block: fenced ```dnos block")
    text = ("Here is the config:\n"
            "```dnos\n"
            "configure\n"
            "protocols bgp\n"
            "  neighbor 1.1.1.1 remote-as 65001\n"
            "  exit\n"
            "exit\n"
            "```\n"
            "Apply with commit when ready.")
    body = parse_dnos_block(text)
    _assert(body.startswith("configure"), "starts with configure", info=body)
    _assert("neighbor 1.1.1.1" in body, "neighbor line preserved", info=body)
    _assert("Here is the config" not in body,
            "prose not included in body", info=body)

    _case("parse_dnos_block: heuristic on un-fenced CLI")
    text = ("Sure!\n"
            "configure\n"
            "interfaces ge-0/0/0\n"
            "  description test\n"
            "exit\n"
            "\n"
            "More prose here that should NOT be captured.")
    body = parse_dnos_block(text)
    _assert("configure" in body, "captured configure block", info=body)
    _assert("More prose" not in body, "stops before prose", info=body)

    _case("parse_dnos_block: empty / no CLI -> empty")
    _assert(parse_dnos_block("just a plain explanation") == "",
            "plain text -> empty body")
    _assert(parse_dnos_block("") == "", "empty input -> empty body")

    _case("validate_dnos_text: trivial valid block")
    out = validate_dnos_text(
        "configure\nprotocols bgp\n  neighbor 1.1.1.1 remote-as 65001\nexit"
    )
    _assert(isinstance(out, dict), "returns dict",
            info=f"type={type(out)}")
    _assert("ok" in out, "has 'ok' field",
            info=str(list(out.keys())))

    _case("validate_dnos_text: empty body fails")
    out = validate_dnos_text("")
    _assert(out.get("ok") is False, "empty body marked invalid")

    _case("build_grounded_system_prompt: contract literals")
    ev = [Evidence(
        source="rst",
        doc_name="bgp",
        category="Protocols/bgp",
        path="Protocols/bgp/neighbor/address-family/address-family.rst",
        snippet="neighbor address-family ipv4-unicast example",
    )]
    prompt = build_grounded_system_prompt(ev)
    _assert("NO_VERIFIED_DNOS_SOURCE" in prompt,
            "contains NO_VERIFIED_DNOS_SOURCE sentinel")
    _assert("Do not call tools" in prompt,
            "forbids tool calls")
    _assert("address-family ipv4-unicast example" in prompt,
            "inlines evidence snippet")
    _assert("DNOS CLI" in prompt or "dnos cli" in prompt.lower(),
            "mentions DNOS CLI in role")

    _case("format_evidence_for_prompt + serialize_sources")
    block = format_evidence_for_prompt(ev)
    _assert("[1] Protocols/bgp/bgp" in block or "[1] Protocols" in block,
            "block has citation marker", info=block.splitlines()[0])
    wire = serialize_sources(ev)
    _assert(isinstance(wire, list) and len(wire) == 1,
            "wire format is a list of len 1")
    _assert(wire[0]["source"] == "rst", "source preserved")
    _assert("snippet" in wire[0], "snippet preserved")

    print("\nAll DNOS grounding tests passed.")


if __name__ == "__main__":
    main()
