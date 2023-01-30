from datetime import datetime

from django.db.models import Count, Q, Sum
from django.utils import timezone

from environments.models import Environment
from task_processor.decorators import register_task_handler

from .models import (
    APIUsageBucket,
    APIUsageRaw,
    FeatureEvaluationBucket,
    FeatureEvaluationRaw,
)


@register_task_handler()
def track_feature_evaluation(environment_id, feature_evaluations):
    feature_evaluation_objects = []
    for feature_name, evaluation_count in feature_evaluations.items():
        feature_evaluation_objects.append(
            FeatureEvaluationRaw(
                feature_name=feature_name,
                environment_id=environment_id,
                evaluation_count=evaluation_count,
            )
        )
    FeatureEvaluationRaw.objects.bulk_create(feature_evaluation_objects)


@register_task_handler()
def track_request(resource: int, host: str, environment_key: str):
    environment = Environment.get_from_cache(environment_key)
    if environment is None:
        return
    APIUsageRaw.objects.create(
        environment_id=environment.id,
        resource=resource,
        host=host,
    )


def _get_api_usage_source_data(
    process_from: datetime, process_till: datetime, source_bucket_size: int = None
) -> dict:
    filters = Q(
        created_at__lte=process_till,
        created_at__gt=process_from,
    )
    if source_bucket_size:
        return (
            APIUsageBucket.objects.filter(filters, bucket_size=source_bucket_size)
            .values("environment_id", "resource")
            .annotate(count=Sum("total_count"))
        )
    return (
        APIUsageRaw.objects.filter(filters)
        .values("environment_id", "resource")
        .annotate(count=Count("id"))
    )


def _get_feature_evaluation_source_data(
    process_from: datetime, process_till: datetime, source_bucket_size: int = None
) -> dict:
    filters = Q(
        created_at__lte=process_till,
        created_at__gt=process_from,
    )
    if source_bucket_size:
        return (
            FeatureEvaluationBucket.objects.filter(
                filters, bucket_size=source_bucket_size
            )
            .values("environment_id", "feature_name")
            .annotate(count=Sum("total_count"))
        )
    return (
        FeatureEvaluationRaw.objects.filter(filters, bucket_size=source_bucket_size)
        .values("environment_id", "feature_name")
        .annotate(count=Sum("evaluation_count"))
    )


def get_start_of_current_bucket(bucket_size: int) -> datetime:
    current_time = timezone.now().replace(second=0, microsecond=0)
    start_of_current_bucket = current_time - timezone.timedelta(
        minutes=current_time.minute % bucket_size
    )
    return start_of_current_bucket


@register_task_handler()
def populate_api_usage_bucket(
    bucket_size: int, run_every: int, source_bucket_size: int = None
):
    start_of_current_bucket = get_start_of_current_bucket(
        bucket_size,
    )

    for i in range(1, (run_every // bucket_size) + 1):
        process_from = start_of_current_bucket - timezone.timedelta(
            minutes=bucket_size * i
        )
        process_to = process_from + timezone.timedelta(minutes=bucket_size)
        data = _get_api_usage_source_data(process_from, process_to, source_bucket_size)
        for row in data:
            APIUsageBucket.objects.create(
                environment_id=row["environment_id"],
                resource=row["resource"],
                total_count=row["count"],
                bucket_size=bucket_size,
                created_at=process_from,
            )


@register_task_handler()
def populate_feature_evaluation_bucket(
    bucket_size: int, run_every: int, source_bucket_size: int = None
):
    start_of_current_bucket = get_start_of_current_bucket(
        bucket_size,
    )

    for i in range(1, (run_every // bucket_size) + 1):
        process_from = start_of_current_bucket - timezone.timedelta(
            minutes=bucket_size * i
        )
        process_to = process_from + timezone.timedelta(minutes=bucket_size)
        data = _get_feature_evaluation_source_data(
            process_from, process_to, source_bucket_size
        )
        for row in data:
            FeatureEvaluationBucket.objects.create(
                environment_id=row["environment_id"],
                feature_name=row["feature_name"],
                total_count=row["count"],
                bucket_size=bucket_size,
                created_at=process_from,
            )
