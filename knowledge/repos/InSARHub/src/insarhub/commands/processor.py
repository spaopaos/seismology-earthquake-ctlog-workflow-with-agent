# -*- coding: utf-8 -*-
from pathlib import Path

from insarhub.core.base import CloudProcessor
from .base import BaseCommand, CommandResult, safe_command


class SubmitCommand(BaseCommand):
    """Wraps processor.submit() — submits jobs to HyP3."""

    def __init__(self, processor: CloudProcessor, progress_callback=None):
        super().__init__(progress_callback)
        self.processor = processor

    @safe_command
    def run(self) -> CommandResult:
        self.progress("Submitting jobs to HyP3...", 0)
        batchs = self.processor.submit()
        total = sum(len(b) for b in batchs.values())
        self.progress(f"Submitted {total} jobs", 100)
        return CommandResult(
            success=True,
            message=f"Submitted {total} jobs",
            data=batchs,
        )


class RefreshCommand(BaseCommand):
    """Wraps processor.refresh() — fetches latest job statuses from HyP3."""

    def __init__(self, processor: CloudProcessor, progress_callback=None):
        super().__init__(progress_callback)
        self.processor = processor

    @safe_command
    def run(self) -> CommandResult:
        self.progress("Refreshing job statuses...", 0)
        batchs = self.processor.refresh()
        total = sum(len(b) for b in batchs.values())
        failed = len(getattr(self.processor, "failed_jobs", []))
        self.progress(f"Refreshed {total} jobs", 100)
        msg = f"Refreshed {total} jobs"
        if failed:
            msg += f" ({failed} failed)"
        return CommandResult(success=True, message=msg, data=batchs)


class DownloadResultsCommand(BaseCommand):
    """Wraps processor.download() — downloads all succeeded HyP3 job outputs."""

    def __init__(self, processor: CloudProcessor, progress_callback=None):
        super().__init__(progress_callback)
        self.processor = processor

    @safe_command
    def run(self) -> CommandResult:
        self.progress("Downloading HyP3 results...", 0)
        output_dir, dl_stats = self.processor.download()
        self.progress("Download complete", 100)
        return CommandResult(
            success=True,
            message=f"Results saved to {output_dir}",
            data={"output_dir": str(output_dir), **dl_stats},
            output_files=[output_dir] if output_dir else [],
        )


class RetryCommand(BaseCommand):
    """Wraps processor.retry() — resubmits all failed jobs."""

    def __init__(self, processor: CloudProcessor, progress_callback=None):
        super().__init__(progress_callback)
        self.processor = processor

    @safe_command
    def run(self) -> CommandResult:
        self.progress("Retrying failed jobs...", 0)
        batchs = self.processor.retry()
        if batchs is None:
            return CommandResult(success=True, message="No failed jobs to retry")
        total = sum(len(b) for b in batchs.values())
        self.progress(f"Resubmitted {total} jobs", 100)
        return CommandResult(
            success=True,
            message=f"Resubmitted {total} failed jobs",
            data=batchs,
        )


class SaveJobsCommand(BaseCommand):
    """Wraps processor.save() — persists job IDs to JSON for later resumption."""

    def __init__(self, processor: CloudProcessor, save_path: Path | str | None = None, progress_callback=None):
        super().__init__(progress_callback)
        self.processor = processor
        self.save_path = save_path

    @safe_command
    def run(self) -> CommandResult:
        self.progress("Saving job IDs...", 0)
        path = self.processor.save(self.save_path)
        self.progress(f"Saved to {path}", 100)
        return CommandResult(
            success=True,
            message=f"Job IDs saved to {path}",
            data=path,
            output_files=[path],
        )


class CheckCreditsCommand(BaseCommand):
    """Wraps processor.check_credits() — prints remaining HyP3 credits for all users."""

    def __init__(self, processor: CloudProcessor, progress_callback=None):
        super().__init__(progress_callback)
        self.processor = processor

    @safe_command
    def run(self) -> CommandResult:
        self.progress("Checking HyP3 credits...", 0)
        self.processor.check_credits()
        self.progress("Done", 100)
        return CommandResult(success=True, message="Credits checked (see output above)")
