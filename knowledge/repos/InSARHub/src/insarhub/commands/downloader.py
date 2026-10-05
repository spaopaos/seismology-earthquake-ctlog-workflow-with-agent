# -*- coding: utf-8 -*-
from insarhub.core.base import BaseDownloader
from .base import BaseCommand, CommandResult, safe_command


class SearchCommand(BaseCommand):
    """Wraps downloader.search() — works with any registered BaseDownloader."""

    def __init__(self, downloader: BaseDownloader, progress_callback=None):
        super().__init__(progress_callback)
        self.downloader = downloader

    @safe_command
    def run(self) -> CommandResult:
        self.progress("Starting search...", 0)
        results = self.downloader.search()
        total = sum(len(v) for v in results.values())
        stacks = len(results)
        self.progress(f"Found {total} scenes in {stacks} stacks", 100)
        return CommandResult(
            success=True,
            message=f"Found {total} scenes in {stacks} stacks",
            data=results,
        )


class FilterCommand(BaseCommand):
    """Wraps downloader.filter(**filter_kwargs) on existing search results."""

    def __init__(self, downloader: BaseDownloader, filter_kwargs: dict, progress_callback=None):
        super().__init__(progress_callback)
        self.downloader = downloader
        self.filter_kwargs = filter_kwargs

    @safe_command
    def run(self) -> CommandResult:
        self.progress("Applying filters...", 0)
        results = self.downloader.filter(**self.filter_kwargs)
        total = sum(len(v) for v in results.values())
        stacks = len(results)
        self.progress(f"Filter applied: {total} scenes in {stacks} stacks", 100)
        return CommandResult(
            success=True,
            message=f"Filter applied: {total} scenes in {stacks} stacks",
            data=results,
        )


class DownloadScenesCommand(BaseCommand):
    """Wraps downloader.download() with forwarded keyword arguments."""

    def __init__(self, downloader: BaseDownloader, progress_callback=None, **download_kwargs):
        super().__init__(progress_callback)
        self.downloader = downloader
        self.download_kwargs = download_kwargs

    @safe_command
    def run(self) -> CommandResult:
        self.progress("Starting scene download...", 0)
        self.downloader.download(**self.download_kwargs)
        download_dir = getattr(self.downloader, "download_dir", None)
        self.progress("Download complete", 100)
        return CommandResult(
            success=True,
            message="Download complete",
            data=download_dir,
            output_files=[download_dir] if download_dir else [],
        )


class SummaryCommand(BaseCommand):
    """Wraps downloader.summary() — prints a text summary of active results."""

    def __init__(self, downloader: BaseDownloader, ls: bool = False, progress_callback=None):
        super().__init__(progress_callback)
        self.downloader = downloader
        self.ls = ls

    @safe_command
    def run(self) -> CommandResult:
        self.progress("Building summary...", 0)
        self.downloader.summary(ls=self.ls)
        self.progress("Done", 100)
        return CommandResult(success=True, message="Summary printed")


class FootprintCommand(BaseCommand):
    """Wraps downloader.footprint() — renders or saves the scene footprint map."""

    def __init__(self, downloader: BaseDownloader, save_path: str | None = None, progress_callback=None):
        super().__init__(progress_callback)
        self.downloader = downloader
        self.save_path = save_path

    @safe_command
    def run(self) -> CommandResult:
        self.progress("Rendering footprint map...", 0)
        self.downloader.footprint(save_path=self.save_path)
        self.progress("Done", 100)
        msg = f"Footprint saved to {self.save_path}" if self.save_path else "Footprint displayed"
        return CommandResult(
            success=True,
            message=msg,
            output_files=[self.save_path] if self.save_path else [],
        )
