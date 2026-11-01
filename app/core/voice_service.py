import io
import wave
import logging
import threading
from typing import Optional, Callable
import numpy as np
import sounddevice as sd
import speech_recognition as sr
import pyttsx3

from app.config import config

logger = logging.getLogger("AURA.Voice")


class VoiceService:
    """Voice service providing offline TTS and microphone STT capture."""

    SAMPLE_RATE = 16000
    CHANNELS = 1

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.is_recording = False
        self.recorded_frames = []
        self._record_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Audio level callback for AURA Core waveform reactivity
        self.audio_level_callback: Optional[Callable[[float], None]] = None
        
        # TTS Engine
        self._tts_lock = threading.Lock()
        self.tts_engine = None
        self._init_tts()

    def _init_tts(self):
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty("rate", config.speech_rate)
            self.tts_engine.setProperty("volume", config.speech_volume)
        except Exception as e:
            logger.warning("TTS engine initialization notice: %s. TTS will operate in fallback mode.", e)
            self.tts_engine = None

    def set_speech_rate(self, rate: int):
        config.speech_rate = rate
        if self.tts_engine:
            try:
                self.tts_engine.setProperty("rate", rate)
            except Exception:
                pass

    def set_speech_volume(self, volume: float):
        config.speech_volume = max(0.0, min(1.0, volume))
        if self.tts_engine:
            try:
                self.tts_engine.setProperty("volume", config.speech_volume)
            except Exception:
                pass

    def check_microphone_available(self) -> bool:
        """Check if any audio input device is present on system."""
        try:
            devices = sd.query_devices()
            for dev in devices:
                if dev.get("max_input_channels", 0) > 0:
                    return True
            return False
        except Exception:
            return False

    def start_recording(self, level_callback: Optional[Callable[[float], None]] = None):
        """Start capturing audio stream from microphone."""
        if self.is_recording:
            return

        if not self.check_microphone_available():
            raise RuntimeError("No microphone hardware detected on this system.")

        self.audio_level_callback = level_callback
        self.recorded_frames = []
        self._stop_event.clear()
        self.is_recording = True

        self._record_thread = threading.Thread(target=self._record_worker, daemon=True)
        self._record_thread.start()

    def _record_worker(self):
        """Worker thread continuously reading audio buffer via sounddevice."""
        try:
            def audio_callback(indata, frames, time_info, status):
                if status:
                    logger.debug("Audio callback status: %s", status)
                if self.is_recording:
                    self.recorded_frames.append(indata.copy())
                    # Compute RMS for reactive waveform
                    rms = np.sqrt(np.mean(indata**2))
                    norm_level = min(1.0, float(rms * 10))
                    if self.audio_level_callback:
                        self.audio_level_callback(norm_level)

            with sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype="int16",
                callback=audio_callback,
                blocksize=1024
            ):
                while not self._stop_event.is_set():
                    self._stop_event.wait(timeout=0.05)
        except Exception as e:
            logger.error("Audio recording error: %s", e)
            self.is_recording = False

    def stop_recording(self) -> str:
        """Stop microphone recording and transcribe captured audio to text."""
        if not self.is_recording:
            return ""

        self.is_recording = False
        self._stop_event.set()
        if self._record_thread and self._record_thread.is_alive():
            self._record_thread.join(timeout=1.0)

        if self.audio_level_callback:
            self.audio_level_callback(0.0)

        if not self.recorded_frames:
            return ""

        # Concatenate audio frames
        audio_data = np.concatenate(self.recorded_frames, axis=0)

        # Write to in-memory WAV buffer
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.SAMPLE_RATE)
            wf.writeframes(audio_data.tobytes())
        wav_buffer.seek(0)

        # Recognize with SpeechRecognition
        try:
            with sr.AudioFile(wav_buffer) as source:
                sr_audio = self.recognizer.record(source)
            text = self.recognizer.recognize_google(sr_audio)
            return text.strip()
        except sr.UnknownValueError:
            logger.info("Speech recognition could not decipher audio (silent or unclear).")
            return ""
        except sr.RequestError as e:
            logger.warning("Online speech recognition network error: %s", e)
            raise RuntimeError(f"Speech recognition service unreachable: {e}")
        except Exception as e:
            logger.error("Transcription error: %s", e)
            raise RuntimeError(f"Transcription error: {str(e)}")

    def speak_text(self, text: str, interrupt_check: Optional[Callable[[], bool]] = None):
        """Speak response aloud using pyttsx3."""
        if not config.voice_enabled or not text.strip():
            return

        with self._tts_lock:
            try:
                # Re-initialize clean engine for each utterance to prevent pyttsx3 loop lockup on Windows
                engine = pyttsx3.init()
                engine.setProperty("rate", config.speech_rate)
                engine.setProperty("volume", config.speech_volume)
                
                # Strip markdown asterisks and backticks before speaking
                clean_text = text.replace("*", "").replace("`", "").replace("#", "")
                engine.say(clean_text)
                engine.runAndWait()
                engine.stop()
            except Exception as e:
                logger.warning("TTS speech failed: %s", e)


voice_service = VoiceService()
