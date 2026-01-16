from dataclasses import dataclass, field
from threading import Lock


@dataclass
class JarvisState:
    audio_enabled: bool = True
    mic_enabled: bool = True
    vision_enabled: bool = True
    lock: Lock = field(default_factory=Lock, repr=False)

    def toggle_audio(self) -> bool:
        with self.lock:
            self.audio_enabled = not self.audio_enabled
            return self.audio_enabled

    def toggle_mic(self) -> bool:
        with self.lock:
            self.mic_enabled = not self.mic_enabled
            return self.mic_enabled

    def toggle_vision(self) -> bool:
        with self.lock:
            self.vision_enabled = not self.vision_enabled
            return self.vision_enabled

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "audio_enabled": self.audio_enabled,
                "mic_enabled": self.mic_enabled,
                "vision_enabled": self.vision_enabled,
            }


state = JarvisState()
