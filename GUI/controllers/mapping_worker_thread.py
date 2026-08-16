# mapping_worker_thread.py
from PyQt6 import QtCore, QtGui, QtWidgets 
import threading

from thread_queue_calculation_stream import QueueCalcStream

from PyQt6 import QtCore


class MappingWorker(QtCore.QObject):

    progress = QtCore.pyqtSignal(object)
    status = QtCore.pyqtSignal(str)

    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(object)
    stopped = QtCore.pyqtSignal()

    def __init__(self, function, *args, **kwargs):
        super().__init__()

        self.function = function
        self.args = args
        self.kwargs = kwargs

        self.kill_ev = threading.Event()

        self.result = None
        self.exception = None

    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.result = self.function(
                *self.args,
                **self.kwargs,
                kill_ev=self.kill_ev,
            )

            if self.stop_requested:
                self.stopped.emit()
            else:
                self.finished.emit(self.result)

        except Exception as exc:
            self.exception = exc
            self.error.emit(exc)

    def stop(self):
        self.kill_ev.set()

    @property
    def stop_requested(self) -> bool:
        return self.kill_ev.is_set()

    def should_stop(self) -> bool:
        return self.kill_ev.is_set()

class WorkerManager(QtCore.QObject):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._workers = set()
        self._threads = set()

    def start(self, function, *args, **kwargs):
        thread = QtCore.QThread()

        worker = MappingWorker(
            function,
            *args,
            **kwargs,
        )

        worker.moveToThread(thread)

        thread.started.connect(worker.run)

        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.stopped.connect(thread.quit)

        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        self._workers.add(worker)
        self._threads.add(thread)

        thread.finished.connect(
            lambda: self._cleanup(worker, thread)
        )

        thread.start()

        return worker

    def _cleanup(self, worker, thread):
        self._workers.discard(worker)
        self._threads.discard(thread)


class RemapWorker(QtCore.QObject):

    progress = QtCore.pyqtSignal(object)
    status = QtCore.pyqtSignal(str)

    finished = QtCore.pyqtSignal(str)
    cancelled = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self, mapper, table_name):
        super().__init__()

        self.mapper = mapper
        self.table_name = table_name

        self.kill_ev = threading.Event()
        self.qstream = None

    @QtCore.pyqtSlot()
    def run(self):

        try:
            db_info = {
                "name": self.mapper.db_path_file,
                "key": self.mapper.key_filepath,
                "pwd": self.mapper.password,
                "encrypt": self.mapper.is_db_encrypted,
            }

            mount, mount_active, mappath_exists = (
                self.mapper.check_if_map_device_active(
                    self.mapper.db,
                    self.table_name,
                    False,
                )
            )

            if not (mount_active and mappath_exists):
                self.error.emit("Mount not available!")
                return

            self.kill_ev.clear()

            self.qstream = QueueCalcStream(
                db_info,
                self.table_name,
                mount,
                0.1,
                self.kill_ev,
                self.progress,
            )

            self.qstream.start()

            # IMPORTANT:
            # This is now running inside the QThread,
            # not the GUI thread.
            self.qstream.join()

            if self.kill_ev.is_set():
                self.cancelled.emit()
            else:
                self.finished.emit(
                    "Thread Mapping finished"
                )

        except Exception as exc:
            self.error.emit(str(exc))

    def stop(self):
        self.kill_ev.set()

class FunctionWorker(QtCore.QObject):

    finished = QtCore.pyqtSignal(object)
    error = QtCore.pyqtSignal(object)
    progress = QtCore.pyqtSignal(object)
    status = QtCore.pyqtSignal(str)
    cancelled = QtCore.pyqtSignal()

    def __init__(self, function, *args, **kwargs):
        super().__init__()

        self.function = function
        self.args = args
        self.kwargs = kwargs

        self._stop_event = threading.Event()

    @QtCore.pyqtSlot()
    def run(self):
        try:
            result = self.function(
                *self.args,
                worker=self,
                **self.kwargs
            )

            if self.stop_requested:
                self.cancelled.emit()
            else:
                self.finished.emit(result)

        except Exception as exc:
            self.error.emit(exc)

    def stop(self):
        self._stop_event.set()

    @property
    def stop_requested(self):
        return self._stop_event.is_set()

    def should_stop(self):
        return self._stop_event.is_set()

class WorkerMapProgress:

    def __init__(self, worker:MappingWorker):
        self.worker = worker

    def start(self, total, description):
        self.worker.progress.emit(
            ("start", total, description)
        )

    def update(
        self,
        current=None,
        advance=None,
        description=None,
    ):
        self.worker.progress.emit(
            (
                "update",
                current,
                advance,
                description,
            )
        )

    def stop(self):
        self.worker.progress.emit(
            ("stop",)
        )