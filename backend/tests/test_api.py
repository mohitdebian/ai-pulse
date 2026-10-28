from tests.conftest import login


def test_login_lists_organizations(client):
    _, data = login(client, "ravi@consult.test")
    names = {o["org_name"] for o in data["organizations"]}
    assert names == {"Northwind Logistics", "Bluepeak Retail"}


def test_employee_sees_questions(client):
    headers, _ = login(client, "priya@northwind.test", "Northwind Logistics")
    r = client.get("/diagnostic/questions", headers=headers)
    assert r.status_code == 200
    assert any(q["id"] == "sup-drafts" for q in r.json())


def test_admin_dashboard(client):
    headers, data = login(client, "asha@northwind.test", "Northwind Logistics")
    org_id = data["organizations"][0]["org_id"]
    r = client.get(f"/dashboard?org_id={org_id}", headers=headers)
    assert r.status_code == 200
    assert len(r.json()["departments"]) == 4


def test_admin_cannot_see_other_org(client):
    headers, _ = login(client, "asha@northwind.test", "Northwind Logistics")
    r = client.get("/dashboard?org_id=2", headers=headers)
    assert r.status_code == 403


def test_report_includes_score_breakdown(client):
    headers, _ = login(client, "priya@northwind.test", "Northwind Logistics")
    r = client.get("/reports/me", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "breakdown" in data
    assert len(data["breakdown"]) == 2
    assert data["breakdown"][0]["question_id"] == "common-freq"
    assert data["breakdown"][0]["score"] == 2.0
    assert data["breakdown"][1]["reason"] == "Useful summary but shared customer data."


def test_delete_my_report(client):
    headers, _ = login(client, "priya@northwind.test", "Northwind Logistics")
    del_res = client.delete("/reports/me", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json() == {"status": "deleted"}

    rep_res = client.get("/reports/me", headers=headers)
    assert rep_res.status_code == 200
    assert rep_res.json()["answered"] == 0
    assert rep_res.json()["average_score"] is None


