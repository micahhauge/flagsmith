import json
import typing
import uuid
from datetime import datetime

from django.db import models
from django.utils import timezone

from task_processor.exceptions import TaskProcessingError
from task_processor.task_registry import registered_tasks


class AbstractBaseTask(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    task_identifier = models.CharField(max_length=200)
    serialized_args = models.TextField(blank=True, null=True)
    serialized_kwargs = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

    @property
    def args(self) -> typing.List[typing.Any]:
        if self.serialized_args:
            return self.deserialize_data(self.serialized_args)
        return []

    @property
    def kwargs(self) -> typing.Dict[str, typing.Any]:
        if self.serialized_kwargs:
            return self.deserialize_data(self.serialized_kwargs)
        return {}

    @staticmethod
    def serialize_data(data: typing.Any):
        # TODO: add datetime support if needed
        return json.dumps(data)

    @staticmethod
    def deserialize_data(data: typing.Any):
        return json.loads(data)

    def mark_failure(self):
        pass

    def mark_success(self):
        pass

    def run(self):
        return self.callable(*self.args, **self.kwargs)

    @property
    def callable(self) -> typing.Callable:
        try:
            return registered_tasks[self.task_identifier]
        except KeyError as e:
            raise TaskProcessingError(
                "No task registered with identifier '%s'. Ensure your task is "
                "decorated with @register_task_handler.",
                self.task_identifier,
            ) from e


class Task(AbstractBaseTask):
    scheduled_for = models.DateTimeField(blank=True, null=True, default=timezone.now)

    # denormalise failures and completion so that we can use select_for_update
    num_failures = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)

    class Meta:
        # We have customised the migration in 0004 to only apply this change to postgres databases
        # TODO: work out how to index the taskprocessor_task table for Oracle and MySQL
        indexes = [
            models.Index(
                name="incomplete_tasks_idx",
                fields=["scheduled_for"],
                condition=models.Q(completed=False, num_failures__lt=3),
            )
        ]

    @classmethod
    def create(
        cls,
        task_identifier: str,
        *,
        args: typing.Tuple[typing.Any] = None,
        kwargs: typing.Dict[str, typing.Any] = None,
    ) -> "Task":
        return Task(
            task_identifier=task_identifier,
            serialized_args=cls.serialize_data(args or tuple()),
            serialized_kwargs=cls.serialize_data(kwargs or dict()),
        )

    @classmethod
    def schedule_task(
        cls,
        schedule_for: datetime,
        task_identifier: str,
        *,
        args: typing.Tuple[typing.Any] = None,
        kwargs: typing.Dict[str, typing.Any] = None,
    ) -> "Task":
        task = cls.create(
            task_identifier=task_identifier,
            args=args,
            kwargs=kwargs,
        )
        task.scheduled_for = schedule_for
        return task

    def mark_failure(self):
        self.num_failures += 1

    def mark_success(self):
        self.completed = True


class RecurringTask(AbstractBaseTask):
    run_every = models.DurationField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["task_identifier", "run_every"],
                name="unique_run_every_tasks",
            ),
        ]

    @property
    def should_execute(self) -> bool:
        last_task_run = self.task_runs.order_by("-started_at").first()
        # if we have never run this task, then we should execute it
        if not last_task_run:
            return True
        # if the last run was at t- run_every, then we should execute it
        if (timezone.now() - last_task_run.started_at) >= self.run_every:
            return True

        # if the last run was not a success and we do not have
        # more than 3 failures in t- run_every, then we should execute it
        if (
            last_task_run.result != TaskResult.SUCCESS.name
            and self.task_runs.filter(
                started_at__gte=(timezone.now() - self.run_every)
            ).count()
            <= 3
        ):
            return True
        # otherwise, we should not execute it
        return False

    @property
    def is_task_registered(self) -> bool:
        return self.task_identifier in registered_tasks


class TaskResult(models.Choices):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class AbstractTaskRun(models.Model):
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(blank=True, null=True)
    result = models.CharField(
        max_length=50, choices=TaskResult.choices, blank=True, null=True, db_index=True
    )
    error_details = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True


class TaskRun(AbstractTaskRun):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="task_runs")


class RecurringTaskRun(AbstractTaskRun):
    task = models.ForeignKey(
        RecurringTask, on_delete=models.CASCADE, related_name="task_runs"
    )


class HealthCheckModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(unique=True, blank=False, null=False)
