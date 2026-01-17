import threading
import time
from typing import Callable, Optional


class WakeWordListener:
    def __init__(
        self,
        on_detected: Callable[[], None],
        wake_word: str = "jarvis",
        threshold: float = 0.5,
        cooldown_seconds: float = 3.0,
        sample_rate: int = 16000,
        chunk_size: int = 1280,
        device: Optional[int] = None,
    ) -> None:
        self._on_detected = on_detected
        self._wake_word = wake_word
        self._threshold = threshold
        self._cooldown_seconds = cooldown_seconds
        self._sample_rate = sample_rate
        self._chunk_size = chunk_size
        self._device = device
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_trigger = 0.0

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        try:
            import numpy as np
            import sounddevice as sd
            from openwakeword.model import Model
        except Exception:
            return

        # TODO: Replace with a real model path or keyword model for "jarvis".
        model = Model(
            wakeword_models=["jarvis"],
        )

        with sd.InputStream(
            samplerate=self._sample_rate,
            channels=1,
            dtype="int16",
            blocksize=self._chunk_size,
            device=self._device,
        ) as stream:
            while not self._stop_event.is_set():
                data, _overflowed = stream.read(self._chunk_size)
                audio = np.frombuffer(data, dtype=np.int16)

                # TODO: Validate prediction output format for openwakeword.
                predictions = model.predict(audio)
                confidence = float(predictions.get(self._wake_word, 0.0))
                now = time.time()
                if confidence >= self._threshold and (now - self._last_trigger) >= self._cooldown_seconds:
                    self._last_trigger = now
                    try:
                        self._on_detected()
                    except Exception:
                        pass
