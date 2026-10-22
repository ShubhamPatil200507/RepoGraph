import time
import httpx

client = httpx.Client(base_url="http://127.0.0.1:8000", timeout=30.0)

# Check health
health = client.get("/api/health").json()
print("Health:", health)

# Check AI status
ai_st = client.get("/api/ai/status").json()
print("AI Status:", ai_st)

# Start repository analysis
r = client.post("/api/repositories/analyze", json={"repository_url": "https://github.com/repograph-demo/ecommerce-platform"})
aid = r.json()["analysis_id"]
print("Started analysis:", aid)

for i in range(30):
    time.sleep(0.4)
    st = client.get(f"/api/analyses/{aid}").json()
    status = st.get("status")
    stage = st.get("stage")
    print(f"[{i*0.4:.1f}s] status={status}, stage={stage}")
    if status == "completed":
        break
    if status == "failed":
        print("Analysis failed:", st.get("error"))
        exit(1)

# Get Graph
g_res = client.get(f"/api/analyses/{aid}/graph")
assert g_res.status_code == 200, g_res.text
g = g_res.json()
nodes = g["nodes"]
edges = g["edges"]
print(f"Graph loaded successfully: {len(nodes)} nodes, {len(edges)} edges.")

# Pick two connected or interesting nodes
node1 = nodes[0]["id"]
node2 = nodes[1]["id"]
print(f"Selected Node 1: {node1}")
print(f"Selected Node 2: {node2}")

# 1. Test Explain
print("\n>>> Testing Explain Endpoint...")
t0 = time.time()
exp_res = client.post(
    f"/api/analyses/{aid}/explain",
    json={"node_id": node1, "question": "Explain this component architecture role."}
)
print(f"Explain responded in {time.time()-t0:.2f}s with status {exp_res.status_code}")
assert exp_res.status_code == 200, exp_res.text
exp_data = exp_res.json()
print(f"  Model Used: {exp_data.get('model_used')}")
print(f"  Confidence: {exp_data.get('confidence')}")
print(f"  Findings count: {len(exp_data.get('verified_findings', []))}")
print(f"  Explanation preview: {exp_data.get('explanation', '')[:160]}...")

# 2. Test Trace
print("\n>>> Testing Trace Endpoint...")
t0 = time.time()
trace_res = client.post(
    f"/api/analyses/{aid}/trace",
    json={"start_node_id": node1, "target_node_id": node2, "max_depth": 6}
)
print(f"Trace responded in {time.time()-t0:.2f}s with status {trace_res.status_code}")
assert trace_res.status_code == 200, trace_res.text
trace_data = trace_res.json()
print(f"  Path Found: {trace_data.get('path_found')}")
print(f"  Step Descriptions count: {len(trace_data.get('step_descriptions', []))}")
print(f"  Trace Explanation preview: {(trace_data.get('explanation') or '')[:140].encode('ascii', errors='replace').decode()}...")

# 3. Test Impact
print("\n>>> Testing Impact Endpoint...")
t0 = time.time()
impact_res = client.post(
    f"/api/analyses/{aid}/impact",
    json={"node_id": node1, "max_depth": 5}
)
print(f"Impact responded in {time.time()-t0:.2f}s with status {impact_res.status_code}")
assert impact_res.status_code == 200, impact_res.text
impact_data = impact_res.json()
print(f"  Direct Dependents: {len(impact_data.get('direct_dependents', []))}")
print(f"  Transitive Dependents: {len(impact_data.get('transitive_dependents', []))}")
print(f"  Risk Level: {impact_data.get('risk_level')}")
print(f"  Gemma Explanation preview: {(impact_data.get('gemma_explanation') or '')[:140].encode('ascii', errors='replace').decode()}...")

print("\nALL THREE ENDPOINTS RETURNED COMPLETE RESULTS SUCCESSFULLY!")
