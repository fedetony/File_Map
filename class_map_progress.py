# class_map_progress.py

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)


class MapProgress:
    def start(self, total, description):
        pass

    def update(self, current=None, description=None):
        pass

    def SetStatus(self,value):
        pass

    def stop(self):
        pass

class RichMapProgress(MapProgress):

    def __init__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
        )
        self.task_id = None
        self.total = 0
        self.last_per = -1

    def start(self, total, description):
        self.total = total
        self.last_per = -1

        self.progress.start()

        self.task_id = self.progress.add_task(
            description,
            total=total,
        )

    def update(
        self,
        current=None,
        advance=None,
        description=None,
    ):
        if self.task_id is None:
            return
        kwargs = {}

        if current is not None:
            kwargs["completed"] = current

        if advance is not None:
            kwargs["advance"] = advance

        if description is not None:
            kwargs["description"] = description

        if kwargs:
            self.progress.update(
                self.task_id,
                **kwargs,
            )

    def SetStatus(self, value):
        """Set progress using a percentage from 0 to 100."""
        self.update_percent(value)

    def update_percent(self, value, total=100):
        """Convert percentage to the actual Rich task progress."""
        if self.task_id is None or self.total <= 0:
            return
        value = max(0, min(int(value), total))
        if self.last_per == value:
            return
        current = int(self.total * value / total)
        self.update(current=current)
        self.last_per = value

    def stop(self):
        if self.task_id is not None:
            self.progress.stop()
            self.task_id = None
            self.total = 0