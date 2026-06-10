
import sys
import os
import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.ai_service import ai_service
from app.services.anomaly_service import anomaly_service
from app.services.nn_fusion_engine import nn_fusion_engine

class MockTicket:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = 999
        self.ref = "T-MOCK-999"
        self.employee_id = 1
        self.team_name = "MOE"
        self.role = "DEVELOPPEUR"
        self.requested_environments = ["PRD"]
        self.requested_access_details = {
            "application": "CRM_SIEBEL",
            "environment": "PRD",
            "access_type": "READ",
            "resource": "OTHER",
            "request_reason": "maintenance_preventive",
            "manager_approval_status": "none",
            "justification": "Routine maintenance check."
        }

def test_anomaly_fusion():
    print("Loading models...")
    ai_service.load_models()
    
    # 1. Normal Ticket (Monday 10am)
    print("\n--- TEST: NORMAL TICKET (Mon 10am) ---")
    mon_10am = datetime.datetime(2026, 5, 11, 10, 0) # 2026-05-11 is a Monday
    t_normal = MockTicket(employee_submitted_at=mon_10am, source="ITOP")
    
    m1_res = ai_service.classify_ticket_data(t_normal.requested_access_details)
    m1_res["risk_score_rules"] = 50 # Force a base score
    m1_res["level"] = "SENSITIVE"
    
    # Mock DB for counts
    class MockDB:
        def query(self, *args): return self
        def filter(self, *args): return self
        def count(self): return 1
        def add(self, *args): pass
        def flush(self): pass
    
    m2_res = anomaly_service.analyze_ticket(t_normal, MockDB())
    fusion = nn_fusion_engine.predict(m1_res, m2_res)
    
    print(f"M1 Level: {m1_res['level']}")
    print(f"M2 Anomalous: {m2_res['is_anomalous']} (Score: {m2_res['anomaly_score']})")
    print(f"Final Level: {fusion['final_level']} (Mode: {fusion['fusion_mode']})")

    # 2. Anomaly Ticket (Sunday 2am)
    print("\n--- TEST: ANOMALY TICKET (Sun 2am) ---")
    sun_2am = datetime.datetime(2026, 5, 10, 2, 0) # 2026-05-10 is a Sunday
    t_anom = MockTicket(employee_submitted_at=sun_2am, source="ITOP")
    
    m2_res_anom = anomaly_service.analyze_ticket(t_anom, MockDB())
    fusion_anom = nn_fusion_engine.predict(m1_res, m2_res_anom)
    
    print(f"M1 Level: {m1_res['level']}")
    print(f"M2 Anomalous: {m2_res_anom['is_anomalous']} (Score: {m2_res_anom['anomaly_score']})")
    print(f"Flags: {m2_res_anom['flags']}")
    print(f"Final Level: {fusion_anom['final_level']} (Mode: {fusion_anom['fusion_mode']})")

if __name__ == "__main__":
    test_anomaly_fusion()
