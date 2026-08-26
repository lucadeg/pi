import sys, time

sys.path.insert(0, r'C:\Users\Deglu\.hermes\tools\tuios')
import hermes_data_bridge

fns = [
    'query_state_db', 'query_projects_deep_analytics', 'query_github_catalog',
    'query_ports', 'query_git_velocity', 'query_storage_subsystem',
    'query_swarm_workload', 'query_catalog', 'query_auth_providers',
    'query_system_hardware', 'extract_all_130_agents', 'query_traceability_compliance',
    'query_kanban_burndown_and_tasks', 'query_technical_debt_metrics',
    'query_atomic_goals_telemetry', 'query_immutable_ledger_telemetry',
    'query_sovereign_requirements_telemetry', 'query_live_swarm_job_telemetry',
    'query_swarm_jobs_telemetry'
]

for name in fns:
    print(f"Profiling {name} ...", flush=True)
    t0 = time.time()
    try:
        fn = getattr(hermes_data_bridge, name)
        res = fn()
        dur = time.time() - t0
        print(f"DONE {name}: {dur:.4f}s", flush=True)
    except Exception as e:
        print(f"ERROR {name}: {e}", flush=True)
