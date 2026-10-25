"""Background Worker Thread for Batch FBX Processing."""
from typing import List, Optional
from PyQt6.QtCore import QThread, pyqtSignal

from src.core.rescaler_pipeline import process_fbx_file


class BatchWorkerThread(QThread):
    """
    Worker thread that executes FBX rescaling tasks asynchronously,
    preventing UI lockups on large meshes or batch workloads.
    """
    log_message = pyqtSignal(str, str)            # level, message
    progress_updated = pyqtSignal(int, int, str)   # current_index, total, current_filename
    file_completed = pyqtSignal(str, bool, str)    # file_path, success, error_message
    batch_finished = pyqtSignal(int, int)          # total, success_count

    def __init__(
        self,
        files: List[str],
        auto_normalize: bool,
        manual_multiplier: float,
        target_height_cm: float = 180.0,
        output_dir: Optional[str] = None,
        parent=None
    ):
        super().__init__(parent)
        self.files = files
        self.auto_normalize = auto_normalize
        self.manual_multiplier = manual_multiplier
        self.target_height_cm = target_height_cm
        self.output_dir = output_dir
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        total = len(self.files)
        success_count = 0

        self.log_message.emit("INFO", f"Starting batch processing for {total} FBX file(s)...")
        if self.output_dir:
            self.log_message.emit("INFO", f"Custom output directory: {self.output_dir}")

        for idx, file_path in enumerate(self.files, start=1):
            if self._is_cancelled:
                self.log_message.emit("WARNING", "Operation cancelled by user.")
                break

            self.progress_updated.emit(idx, total, file_path)

            try:
                result = process_fbx_file(
                    input_path=file_path,
                    auto_normalize=self.auto_normalize,
                    manual_multiplier=self.manual_multiplier,
                    target_height_cm=self.target_height_cm,
                    output_dir=self.output_dir,
                    log_callback=lambda lvl, msg: self.log_message.emit(lvl, msg)
                )
                success_count += 1
                self.file_completed.emit(file_path, True, "")
            except Exception as e:
                err_msg = str(e)
                self.log_message.emit("ERROR", f"Failed processing {file_path}: {err_msg}")
                self.file_completed.emit(file_path, False, err_msg)

        self.batch_finished.emit(total, success_count)
