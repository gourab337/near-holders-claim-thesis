"""Who can move the three revenue wallets: read from the contracts themselves through a public NEAR RPC endpoint (no key).

The two DAO wallets are Sputnik DAOs: get_policy returns their member groups and vote thresholds. The buybacks wallet is
a multisig contract: get_num_confirmations is how many approvals a request needs, and its access keys are its signers.
Also saves the text of HSP-029, the House of Stake proposal that lowers NEAR's maximum issuance, from NEAR's governance forum.
Writes data/raw/rpc_wallet_control.json and data/raw/gov_hsp029.json, and their manifest entries.
"""
import base64, hashlib, html, json, os, re, time, urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(ROOT, "data", "raw")
RPC = "https://rpc.mainnet.fastnear.com"
DAOS = ["fefundsadmin.sputnik-dao.near", "1csfundsadmin.sputnik-dao.near"]
MULTISIG = "buybacks.multisignature.near"
HSP = "https://gov.near.org/t/42644.json"


def rpc(params):
    req = urllib.request.Request(RPC, json.dumps({"jsonrpc": "2.0", "id": 1, "method": "query", "params": params}).encode(),
                                 {"content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)["result"]
    assert "error" not in out, out
    return out


def view(account, method):
    out = rpc({"request_type": "call_function", "finality": "final", "account_id": account, "method_name": method,
               "args_base64": base64.b64encode(b"{}").decode()})
    return json.loads(bytes(out["result"]))


def main():
    keys = rpc({"request_type": "view_access_key_list", "finality": "final", "account_id": MULTISIG})
    data = {"daos": {a: view(a, "get_policy") for a in DAOS},
            "multisig": {"account": MULTISIG, "num_confirmations": view(MULTISIG, "get_num_confirmations"),
                         "access_keys": sorted(k["public_key"] for k in keys["keys"]), "block_height": keys["block_height"]}}
    with urllib.request.urlopen(urllib.request.Request(HSP, headers={"User-Agent": "near-thesis-fetch"}), timeout=60) as r:
        topic = json.load(r)
    first = topic["post_stream"]["posts"][0]
    hsp = {"title": topic["title"], "created_at": topic["created_at"], "post_updated_at": first["updated_at"],
           "text": html.unescape(re.sub(r"<[^>]+>", "", first["cooked"]))}
    path = os.path.join(RAW, "MANIFEST.json")
    with open(path) as f:
        manifest = json.load(f)
    for name, obj, url in [("rpc_wallet_control.json", data, RPC + " (get_policy, get_num_confirmations, view_access_key_list)"),
                           ("gov_hsp029.json", hsp, HSP + " (first post, tags removed)")]:
        body = json.dumps(obj, indent=1, sort_keys=True).encode()
        with open(os.path.join(RAW, name), "wb") as f:
            f.write(body)
        manifest[name.rsplit(".", 1)[0]] = {"file": name, "url": url, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                            "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
        print(f"{name:40s} {len(body):>10,d} bytes")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=1)


if __name__ == "__main__":
    main()
