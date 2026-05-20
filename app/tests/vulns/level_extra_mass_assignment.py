import json

from db.models import User, UserRole


def test_mass_assignment_via_patch_profile(test_db, customer_client):
    """
    Note:
        After gaining Chef-level access through the previous vulnerabilities,
        I started reviewing the remaining endpoints more carefully.

        I found that the PATCH "/profile" endpoint uses a Pydantic model
        configured with `extra=Extra.allow`. This means that any extra fields
        sent in the HTTP request body are accepted and stored without validation.

        Since the endpoint iterates over ALL fields in the request body
        (including the undocumented ones) and calls `setattr(db_user, var, value)`
        for each one, an attacker can simply send a `role` field in the request
        to escalate their own privileges directly — no second endpoint needed!

        This is a classic Mass Assignment vulnerability (also known as
        Auto-binding or Object Injection). The application blindly trusts
        user-supplied field names and maps them to internal model attributes.

        Difference from Level 3 (Privilege Escalation via /users/update_role):
        That level exploited a missing authorisation check on a dedicated
        role-update endpoint. THIS vulnerability is subtler: the endpoint is
        not *supposed* to allow role changes at all, but the permissive
        Pydantic model and the generic setattr loop make it possible anyway.

        OWASP API Security Top 10: API6:2023 - Unrestricted Access to
        Sensitive Business Flows / Mass Assignment.

    Possible fix:
        Two complementary fixes are recommended:

        1. Remove `extra=Extra.allow` from the `UserUpdate` model in
           "app/apis/auth/services/patch_profile_service.py" and replace it
           with `extra=Extra.forbid` (or just remove the extra config entirely).
           This rejects any unrecognised fields at the validation layer.

        2. Replace the generic `setattr` loop with an explicit allowlist of
           fields that may be updated (e.g. first_name, last_name, phone_number),
           so that even if an unexpected field somehow passes validation it
           cannot be written to the database model.

        Example safe loop:
            ALLOWED_FIELDS = {"first_name", "last_name", "phone_number"}
            for var, value in user.dict().items():
                if value and var in ALLOWED_FIELDS:
                    setattr(db_user, var, value)
    """

    # Confirm the user starts as a CUSTOMER
    db_user = test_db.query(User).filter(User.username == "customer").first()
    assert db_user.role == UserRole.CUSTOMER

    # Send a PATCH /profile request with an extra `role` field that should
    # never be accepted by this endpoint.
    malicious_payload = {
        "first_name": "Hacker",
        "last_name": "Chef",
        "phone_number": "0000000000",
        "role": "Chef",          # <-- Mass Assignment payload
    }

    response = customer_client.patch(
        "/profile", content=json.dumps(malicious_payload)
    )

    # The endpoint returns 200 because it processes all fields without filtering
    assert response.status_code == 200

    # Refresh the object from the DB and verify the role was overwritten
    test_db.refresh(db_user)
    assert db_user.role == UserRole.CHEF  # Privilege escalated to Chef!
