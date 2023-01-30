import json

from django.urls import reverse


def test(environment, identity, project, admin_client):
    trait_key = "age"
    trait_value = 18

    create_trait_url = reverse(
        "api-v1:environments:identities-traits-list",
        args=[environment.api_key, identity.id],
    )
    create_trait_data = {
        "trait_key": trait_key,
        "value_type": "int",
        "integer_value": trait_value,
    }
    response = admin_client.post(
        create_trait_url,
        data=json.dumps(create_trait_data),
        content_type="application/json",
    )
    assert response.status_code == 201
    assert identity.identity_traits.first().trait_value == 18

    segments_url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    create_segment_data = {
        "description": "",
        "name": "segment",
        "project": project.id,
        "rules": [
            {
                "type": "ALL",
                "rules": [
                    {
                        "type": "ANY",
                        "conditions": [
                            {
                                "property": trait_key,
                                "operator": "EQUAL",
                                "value": str(trait_value),
                            }
                        ],
                    }
                ],
            }
        ],
    }
    create_segment_response = admin_client.post(
        segments_url,
        data=json.dumps(create_segment_data),
        content_type="application/json",
    )
    assert create_segment_response.status_code == 201

    get_identity_segments_response = admin_client.get(
        f"{segments_url}?identity={identity.id}"
    )
    assert get_identity_segments_response.status_code == 200
