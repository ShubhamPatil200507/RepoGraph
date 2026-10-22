import time
import httpx

client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=30.0)

print("=" * 60)
print("REPOGRAPH — COMPLETE SEVEN-FEATURE INTEGRATION VERIFICATION")
print("=" * 60)

# Check health & AI status
health = client.get("/api/health").json()
print("1. Health Check:", health["status"], f"({health['app_name']} - {health['tagline']})")

ai_st = client.get("/api/ai/status").json()
print(f"2. AI Status: Available={ai_st['available']} | Model={ai_st['configured_model']}")

# Feature 7: Repository Ingestion
print("\n>>> Feature 7: Ingestion & Analysis Lifecycle...")
r = client.post("/api/repositories/analyze", json={"repository_url": "https://github.com/repograph-demo/ecommerce-platform"})
aid = r.json()["analysis_id"]
print(f"  Analysis started: {aid}")

for i in range(30):
    time.sleep(0.3)
    st = client.get(f"/api/analyses/{aid}").json()
    if st.get("status") == "completed":
        print(f"  Analysis successfully completed in {i*0.3:.1f}s!")
        break
    if st.get("status") == "failed":
        print("  Analysis failed:", st.get("error"))
        exit(1)

# Feature 1: Graph Model & 3D/2D Positions
print("\n>>> Feature 1: 3D Universe Graph Topology...")
g_res = client.get(f"/api/analyses/{aid}/graph")
assert g_res.status_code == 200, g_res.text
graph = g_res.json()
print(f"  Topology verified: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges across layers: {list(graph['summary']['layers'].keys())}")
first_node = graph["nodes"][0]
assert first_node["position_3d"] is not None
print(f"  3D Coordinates verified on sample node '{first_node['label']}': x={first_node['position_3d']['x']:.1f}, y={first_node['position_3d']['y']:.1f}, z={first_node['position_3d']['z']:.1f}")

# Graphify Integration
print("\n>>> Graphify Sponsor Integration...")
gf_res = client.get(f"/api/analyses/{aid}/graphify")
assert gf_res.status_code == 200, gf_res.text
gf = gf_res.json()
print(f"  Graphify v1 export verified: schema_version={gf['schema_version']}, graphify_version={gf['graphify_version']}, communities={gf['metadata']['total_communities']}")

# Feature 2: API & Application Data-Flow Explorer
print("\n>>> Feature 2: API & Application Data-Flow Explorer...")
routes_res = client.get(f"/api/analyses/{aid}/api-routes")
assert routes_res.status_code == 200, routes_res.text
routes = routes_res.json()
print(f"  Detected {len(routes)} API endpoints:")
for rt in routes:
    print(f"    - [{rt['http_method']}] {rt['route_path']} -> handler: {rt['label']}")

assert len(routes) > 0, "No routes detected!"
test_route = routes[0]
flow_res = client.get(f"/api/analyses/{aid}/api-flow/{test_route['id']}")
assert flow_res.status_code == 200, flow_res.text
flow = flow_res.json()
print(f"  API Flow for '{test_route['route_path']}' traced {flow['total_connected_components']} components:")
print(f"    - Route: {len(flow['stages']['route'])}")
print(f"    - Middleware/Auth: {len(flow['stages']['middleware_auth'])}")
print(f"    - Service Logic: {len(flow['stages']['service_logic'])}")
print(f"    - Database Entities: {len(flow['stages']['database_entities'])}")

# Feature 3: Git Branch & Commit Comparison
print("\n>>> Feature 3: Git Revision Comparison...")
comp_res = client.post(
    f"/api/analyses/{aid}/compare",
    json={
        "base_ref": "main",
        "target_ref": "v2",
        "target_repository_url": "https://github.com/repograph-demo/ecommerce-platform-v2"
    }
)
assert comp_res.status_code == 200, comp_res.text
comp = comp_res.json()
print(f"  Revision Comparison against v2 completed:")
print(f"    - Added Symbols: {comp['summary']['added_count']}")
print(f"    - Modified Symbols: {comp['summary']['modified_count']}")
print(f"    - Impacted Nodes: {comp['summary']['impacted_count']}")
print(f"    - Changed Routes: {len(comp['changes']['changed_routes'])}")
print(f"    - Changed Schemas: {len(comp['changes']['changed_schemas'])}")

# Feature 4: Gemma 4 Architecture Copilot
print("\n>>> Feature 4: Evidence-Grounded Gemma Architecture Copilot...")
t0 = time.time()
exp_res = client.post(
    f"/api/analyses/{aid}/explain",
    json={"node_id": test_route["id"], "question": "Explain this component architecture role."}
)
print(f"  Explain responded in {time.time()-t0:.2f}s with status {exp_res.status_code}")
assert exp_res.status_code == 200, exp_res.text
exp_data = exp_res.json()
print(f"    Model Used: {exp_data.get('model_used')}")
print(f"    Verified Findings: {len(exp_data.get('verified_findings', []))}")
print(f"    Inferred Hypotheses: {len(exp_data.get('inferred_hypotheses', []))}")

# Feature 5: Database & Application Data-Flow Integration
print("\n>>> Feature 5: Database & Application Data-Flow...")
er_res = client.get(f"/api/analyses/{aid}/er-diagram")
assert er_res.status_code == 200, er_res.text
er = er_res.json()
print(f"  ER Diagram verified: {len(er['entities'])} tables/models, {len(er['relationships'])} relationships:")
for ent in er["entities"][:3]:
    pk = [a["name"] for a in ent["attributes"] if a["is_primary_key"]]
    print(f"    - Entity: {ent['name']} (table: {ent.get('table_name')}) [PK: {pk}]")

# Feature 6: Change Impact Analysis
print("\n>>> Feature 6: Change Impact Analysis...")
t0 = time.time()
impact_res = client.post(
    f"/api/analyses/{aid}/impact",
    json={"node_id": test_route["id"], "max_depth": 5}
)
print(f"  Impact analysis completed in {time.time()-t0:.2f}s:")
assert impact_res.status_code == 200, impact_res.text
impact = impact_res.json()
print(f"    - Direct Dependents: {len(impact['direct_dependents'])}")
print(f"    - Transitive Dependents: {len(impact['transitive_dependents'])}")
print(f"    - Risk Level: {impact.get('risk_level')}")

# Feature 7 Deletion & Resource Cleanup
print("\n>>> Feature 7 Cleanup: Deletion Workflow...")
del_res = client.delete(f"/api/analyses/{aid}")
assert del_res.status_code == 200, del_res.text
print(f"  Cleanup confirmed: {del_res.json()['message']}")

print("\n" + "=" * 60)
print("SUCCESS: ALL SEVEN CAPABILITIES VERIFIED END-TO-END!")
print("=" * 60)
