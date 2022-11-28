import json

import pytest
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from rest_framework import status

from audit.models import (
    SEGMENT_FEATURE_STATE_DELETED_MESSAGE,
    AuditLog,
    RelatedObjectType,
)
from environments.models import Environment
from features.models import Feature, FeatureSegment
from segments.models import Segment


@pytest.mark.parametrize(
    "client, num_queries",
    [
        (lazy_fixture("admin_client"), 2),  # 1 for paging, 1 for result
        (lazy_fixture("master_api_key_client"), 3),  # an extra one for master_api_key
    ],
)
def test_list_feature_segments(
    segment,
    feature,
    environment,
    project,
    django_assert_num_queries,
    client,
    feature_segment,
    num_queries,
):
    # Given
    base_url = reverse("api-v1:features:feature-segment-list")
    url = f"{base_url}?environment={environment.id}&feature={feature.id}"
    environment_2 = Environment.objects.create(
        project=project, name="Test environment 2"
    )
    segment_2 = Segment.objects.create(project=project, name="Segment 2")
    segment_3 = Segment.objects.create(project=project, name="Segment 3")

    FeatureSegment.objects.create(
        feature=feature, segment=segment_2, environment=environment
    )
    FeatureSegment.objects.create(
        feature=feature, segment=segment_3, environment=environment
    )
    FeatureSegment.objects.create(
        feature=feature, segment=segment, environment=environment_2
    )

    # When
    with django_assert_num_queries(num_queries):
        response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["count"] == 3
    for result in response_json["results"]:
        assert result["environment"] == environment.id
        assert "uuid" in result
        assert "segment_name" in result


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_create_feature_segment(segment, feature, environment, client):
    # Given
    data = {
        "feature": feature.id,
        "segment": segment.id,
        "environment": environment.id,
    }
    url = reverse("api-v1:features:feature-segment-list")

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()
    assert response_json["id"]


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_delete_feature_segment(segment, feature, environment, client):
    # Given
    feature_segment = FeatureSegment.objects.create(
        feature=feature, environment=environment, segment=segment
    )
    url = reverse("api-v1:features:feature-segment-detail", args=[feature_segment.id])

    # When
    response = client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FeatureSegment.objects.filter(id=feature_segment.id).exists()


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_audit_log_created_when_feature_segment_created(
    segment, feature, environment, client
):
    # Given
    url = reverse("api-v1:features:feature-segment-list")
    data = {
        "segment": segment.id,
        "feature": feature.id,
        "environment": environment.id,
    }

    # When
    response = client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.FEATURE.name
        ).count()
        == 1
    )


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_priority_of_multiple_feature_segments(
    feature_segment, project, client, environment, feature
):
    # Given
    url = reverse("api-v1:features:feature-segment-update-priorities")

    # another segment and feature segments for the same feature
    another_segment = Segment.objects.create(name="Another segment", project=project)

    another_feature_segment = FeatureSegment.objects.create(
        segment=another_segment, environment=environment, feature=feature
    )

    # reorder the feature segments
    assert feature_segment.priority == 0
    assert another_feature_segment.priority == 1
    data = [
        {"id": feature_segment.id, "priority": 1},
        {"id": another_feature_segment.id, "priority": 0},
    ]

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then the segments are reordered
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response[0]["id"] == feature_segment.id
    assert json_response[1]["id"] == another_feature_segment.id


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_get_feature_segment_by_uuid(
    feature_segment, project, client, environment, feature
):
    # Given
    url = reverse(
        "api-v1:features:feature-segment-get-by-uuid", args=[feature_segment.uuid]
    )

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    json_response = response.json()
    assert json_response["id"] == feature_segment.id
    assert json_response["uuid"] == str(feature_segment.uuid)


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_delete_feature_segment_creates_audit_log(
    feature_segment,
    segment_featurestate,
    feature,
    segment,
    client,
    project,
    environment,
):
    expected_audit_log_message = SEGMENT_FEATURE_STATE_DELETED_MESSAGE % (
        feature.name,
        segment.name,
    )

    url = reverse("api-v1:features:feature-segment-detail", args=(feature_segment.id,))

    # When
    response = client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert AuditLog.objects.filter(
        project=project,
        related_object_id=segment_featurestate.id,
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
        environment=environment,
        log=expected_audit_log_message,
    ).exists()


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_creating_segment_override_for_feature_based_segment_returns_400_for_wrong_feature(
    client, feature_based_segment, project, environment
):
    # Given - A different feature
    feature = Feature.objects.create(name="Feature 2", project=project)
    data = {
        "feature": feature.id,
        "segment": feature_based_segment.id,
        "environment": environment.id,
    }
    url = reverse("api-v1:features:feature-segment-list")

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["feature"][0]
        == "Can only create segment override(using this segment) for feature %d"
        % feature_based_segment.feature.id
    )


@pytest.mark.parametrize(
    "client", [lazy_fixture("master_api_key_client"), lazy_fixture("admin_client")]
)
def test_creating_segment_override_for_feature_based_segment_returns_201_for_correct_feature(
    client, feature_based_segment, project, environment, feature
):
    # Given
    data = {
        "feature": feature.id,
        "segment": feature_based_segment.id,
        "environment": environment.id,
    }
    url = reverse("api-v1:features:feature-segment-list")

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")
    # Then
    assert response.status_code == status.HTTP_201_CREATED
