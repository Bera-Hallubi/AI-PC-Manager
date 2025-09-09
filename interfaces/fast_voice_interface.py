"""
Fast Voice Interface for AI PC Manager
Handles local speech recognition and text-to-speech using local models
"""

import os
import time
import threading
import queue
import wave
import tempfile
from typing import Optional, Callable, Dict, Any
import numpy as np
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel
import speech_recognition as sr
import pyttsx3
try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    TTS = None

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class FastVoiceInterface:
    """Local voice interface with speech recognition and text-to-speech"""
    
    def __init__(self):
        # Merge base STT config with voice overrides (voice.stt takes precedence)
        try:
            base_stt = settings.get('stt', {})
            voice_stt = settings.get('voice.stt', {})
            merged_stt = {}
            merged_stt.update(base_stt if isinstance(base_stt, dict) else {})
            merged_stt.update(voice_stt if isinstance(voice_stt, dict) else {})
            self.stt_config = merged_stt
        except Exception:
            self.stt_config = settings.get_stt_config()
        self.tts_config = settings.get_tts_config()
        
        # Speech recognition components
        self.whisper_model = None
        self.recognizer = None
        self.microphone = None
        self.input_device_index = self.stt_config.get('input_device_index', None)
        
        # Text-to-speech components
        self.tts_engine = None
        self.coqui_tts = None
        
        # Audio settings
        self.sample_rate = self.stt_config.get('sample_rate', 16000)
        self.chunk_size = self.stt_config.get('chunk_size', 1024)
        self.channels = self.stt_config.get('channels', 1)
        
        # Voice activity detection (RMS on float32 0..1 → small thresholds)
        self.vad_enabled = self.stt_config.get('vad_enabled', True)
        self.silence_threshold = float(self.stt_config.get('silence_threshold', 0.02))
        self.silence_duration = float(self.stt_config.get('silence_duration', 1.0))
        
        # State management
        self.is_listening = False
        self.is_speaking = False
        self.audio_queue = queue.Queue()
        self.callback = None
        
        # Initialize components
        self._initialize_stt()
        self._initialize_tts()
    
    def _initialize_stt(self):
        """Initialize speech-to-text components"""
        try:
            # Initialize Whisper model
            whisper_model_name = self.stt_config.get('whisper_model', 'base')
            device = self.stt_config.get('device', 'cpu')
            language = self.stt_config.get('language', 'en')
            
            logger.info(f"Loading Whisper model: {whisper_model_name} on {device}")
            
            self.whisper_model = WhisperModel(
                whisper_model_name,
                device=device,
                compute_type="float16" if device == "cuda" else "int8"
            )
            
            # Initialize fallback recognizer
            self.recognizer = sr.Recognizer()

            # Configure recognizer thresholds from config (with sensible defaults)
            energy_threshold = int(self.stt_config.get('energy_threshold', 200))
            self.recognizer.energy_threshold = energy_threshold
            self.recognizer.dynamic_energy_threshold = bool(self.stt_config.get('dynamic_energy_threshold', True))
            self.recognizer.pause_threshold = float(self.stt_config.get('pause_threshold', 0.7))

            # Select input device automatically if not provided
            self._apply_input_device_selection()

            # Create Microphone with selected device index (if available)
            if self.input_device_index is not None:
                self.microphone = sr.Microphone(device_index=self.input_device_index)
            else:
                self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            logger.info("Speech recognition initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing STT: {e}")
            self.whisper_model = None
            self.recognizer = None
            self.microphone = None
    
    def _apply_input_device_selection(self) -> None:
        """Apply microphone input device selection (config or auto-detect)."""
        try:
            # If user provided an index, use it directly
            if self.input_device_index is not None:
                try:
                    d = sd.query_devices(self.input_device_index)
                    if d.get('max_input_channels', 0) > 0:
                        sd.default.device = (self.input_device_index, None)
                        logger.info(f"Using configured input device index: {self.input_device_index} - {d.get('name','unknown')}")
                        return
                    else:
                        logger.warning("Configured input_device_index has no input channels; falling back to auto-detect")
                except Exception as e:
                    logger.warning(f"Invalid configured input_device_index; falling back to auto-detect: {e}")

            # Try system default input device first
            try:
                default_in, _ = sd.default.device
            except Exception:
                default_in = None

            if default_in is not None:
                try:
                    d = sd.query_devices(default_in)
                    if d.get('max_input_channels', 0) > 0:
                        self.input_device_index = default_in
                        sd.default.device = (self.input_device_index, None)
                        logger.info(f"Using system default input device: {self.input_device_index} - {d.get('name','unknown')}")
                        return
                except Exception:
                    pass

            # Auto-pick best device: prefer WASAPI with highest input channels, else highest channels overall
            devices = sd.query_devices()
            hostapis = sd.query_hostapis()
            candidates = []
            for idx, dev in enumerate(devices):
                if dev.get('max_input_channels', 0) > 0:
                    api_name = hostapis[dev['hostapi']]['name'] if isinstance(hostapis, list) or isinstance(hostapis, tuple) else hostapis[dev['hostapi']].get('name','')
                    score = dev['max_input_channels']
                    if 'WASAPI' in str(api_name).upper():
                        score += 100  # prefer WASAPI
                    candidates.append((score, idx, dev.get('name',''), api_name))

            if candidates:
                candidates.sort(reverse=True)
                _, best_idx, best_name, best_api = candidates[0]
                self.input_device_index = best_idx
                sd.default.device = (self.input_device_index, None)
                logger.info(f"Auto-selected input device: {best_idx} - {best_name} [{best_api}]")
            else:
                logger.warning("No input-capable audio devices found. STT may not work.")
        except Exception as e:
            logger.warning(f"Could not auto-select input device: {e}")

    def _initialize_tts(self):
        """Initialize text-to-speech components"""
        try:
            tts_engine = self.tts_config.get('engine', 'pyttsx3')
            
            if tts_engine == 'pyttsx3':
                # Initialize pyttsx3
                self.tts_engine = pyttsx3.init()
                
                # Configure voice settings
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    # Try to find a good voice
                    for voice in voices:
                        if 'english' in voice.name.lower() or 'en' in voice.id.lower():
                            self.tts_engine.setProperty('voice', voice.id)
                            break
                
                self.tts_engine.setProperty('rate', self.tts_config.get('voice_rate', 200))
                self.tts_engine.setProperty('volume', self.tts_config.get('voice_volume', 0.8))
                
                logger.info("pyttsx3 TTS initialized successfully")
            
            elif tts_engine == 'coqui':
                if TTS_AVAILABLE:
                    # Initialize Coqui TTS
                    model_name = self.tts_config.get('coqui_model', 'tts_models/en/ljspeech/tacotron2-DDC')
                    device = self.tts_config.get('coqui_device', 'cpu')
                    
                    logger.info(f"Loading Coqui TTS model: {model_name}")
                    self.coqui_tts = TTS(model_name=model_name)
                    
                    logger.info("Coqui TTS initialized successfully")
                else:
                    logger.warning("Coqui TTS not available, falling back to pyttsx3")
                    # Fallback to pyttsx3
                    self.tts_engine = pyttsx3.init()
                    self.tts_engine.setProperty('rate', self.tts_config.get('voice_rate', 200))
                    self.tts_engine.setProperty('volume', self.tts_config.get('voice_volume', 0.8))
            
        except Exception as e:
            logger.error(f"Error initializing TTS: {e}")
            self.tts_engine = None
            self.coqui_tts = None
    
    def start_listening(self, callback: Callable[[str], None] = None):
        """
        Start continuous voice recognition
        
        Args:
            callback: Function to call when speech is recognized
        """
        if self.is_listening:
            logger.warning("Already listening")
            return
        
        self.callback = callback
        self.is_listening = True
        
        # Start listening thread
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        
        logger.info("Started voice recognition")
    
    def stop_listening(self):
        """Stop continuous voice recognition"""
        self.is_listening = False
        logger.info("Stopped voice recognition")
    
    def _listen_loop(self):
        """Main listening loop for continuous recognition"""
        try:
            while self.is_listening:
                # Record audio
                audio_data = self._record_audio()
                
                if audio_data is not None and len(audio_data) > 0:
                    # Process audio
                    text = self._process_audio(audio_data)
                    
                    if text and text.strip():
                        normalized_text = self._normalize_recognized_text(text)
                        if normalized_text != text:
                            logger.debug(f"Normalized speech: '{text}' -> '{normalized_text}'")
                        logger.info(f"Recognized speech: {normalized_text}")
                        if self.callback:
                            self.callback(normalized_text)
                    else:
                        logger.debug("No text recognized for this segment")
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in listen loop: {e}")
        finally:
            self.is_listening = False
    
    def _record_audio(self) -> Optional[np.ndarray]:
        """Record audio from microphone"""
        try:
            # Record audio (slightly longer window helps)
            duration = 2.0
            try:
                sd.default.samplerate = self.sample_rate
            except Exception:
                pass
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32
            )
            sd.wait()
            
            # Check if audio has sufficient volume
            if self.vad_enabled:
                volume = np.sqrt(np.mean(audio_data**2))
                logger.debug(f"Audio RMS volume: {volume:.4f} (threshold {self.silence_threshold})")
                if volume < self.silence_threshold:
                    return None
            
            return audio_data.flatten()
            
        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            return None
    
    def _process_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """Process audio data and return recognized text"""
        try:
            text = None
            # Try Whisper first (more accurate)
            if self.whisper_model:
                text = self._process_with_whisper(audio_data)
            # If Whisper did not produce text, try fallback recognizer
            if not text:
                text = self._process_with_speech_recognition(audio_data)
            return text
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return None
    
    def _process_with_whisper(self, audio_data: np.ndarray) -> Optional[str]:
        """Process audio using Whisper model (expects float32 PCM -1..1)."""
        try:
            # Ensure float32 in range [-1, 1]
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            # Normalize if data looks like int16 scaled
            if audio_data.max() > 1.01 or audio_data.min() < -1.01:
                audio_data = np.clip(audio_data / 32767.0, -1.0, 1.0)

            # Transcribe using Whisper
            segments, info = self.whisper_model.transcribe(
                audio_data,
                language=self.stt_config.get('language', 'en'),
                beam_size=int(self.stt_config.get('beam_size', 5)),
                best_of=int(self.stt_config.get('best_of', 5)),
                temperature=float(self.stt_config.get('temperature', 0.0)),
                condition_on_previous_text=bool(self.stt_config.get('condition_on_previous_text', False)),
                no_speech_threshold=float(self.stt_config.get('no_speech_threshold', 0.2)),
                log_prob_threshold=float(self.stt_config.get('logprob_threshold', -1.0)),
                compression_ratio_threshold=float(self.stt_config.get('compression_ratio_threshold', 2.4))
            )
            
            # Get the first segment
            for segment in segments:
                text = segment.text.strip()
                if text:
                    return text
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing with Whisper: {e}")
            return None

    def _normalize_recognized_text(self, text: str) -> str:
        """Heuristic normalization for common misrecognitions and synonyms.
        Keeps it simple to improve command intent mapping without heavy NLP.
        """
        t = text.strip().lower()
        # Common word fixes
        replacements = {
            'sitting': 'settings',
            'sitings': 'settings',
            'setting': 'settings',
            'test manager': 'task manager',
            'taste manager': 'task manager',
            'file, except blurr': 'file explorer',
            'except blurr': 'explorer',
            'file explorer': 'file explorer',
            'explorer': 'explorer',
        }
        for wrong, right in replacements.items():
            if wrong in t:
                t = t.replace(wrong, right)

        # Simple phrase intent normalization
        if t.startswith('open the '):
            t = 'open ' + t[len('open the '):]
        if t.startswith('close the '):
            t = 'close ' + t[len('close the '):]

        return t
    
    def _process_with_speech_recognition(self, audio_data: np.ndarray) -> Optional[str]:
        """Process audio using speech_recognition library"""
        try:
            # Convert numpy array to AudioData
            audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
            audio_data_sr = sr.AudioData(audio_bytes, self.sample_rate, 2)
            
            # Recognize speech
            text = self.recognizer.recognize_google(audio_data_sr)
            return text.strip() if text else None
            
        except sr.UnknownValueError:
            # No speech detected
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing with speech_recognition: {e}")
            return None
    
    def listen_once(self, timeout: float = 5.0) -> Optional[str]:
        """
        Listen for speech once with timeout
        
        Args:
            timeout: Maximum time to wait for speech
            
        Returns:
            Recognized text or None
        """
        try:
            if not self.microphone or not self.recognizer:
                logger.error("Speech recognition not initialized")
                return None
            
            with self.microphone as source:
                logger.info("Listening for speech...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
            
            # Process the audio
            return self._process_audio_from_sr(audio)
            
        except sr.WaitTimeoutError:
            logger.info("No speech detected within timeout")
            return None
        except Exception as e:
            logger.error(f"Error in listen_once: {e}")
            return None
    
    def _process_audio_from_sr(self, audio_data) -> Optional[str]:
        """Process AudioData from speech_recognition"""
        try:
            # Try Whisper first
            if self.whisper_model:
                # Convert AudioData to numpy array
                audio_bytes = audio_data.get_wav_data()
                audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
                audio_float = audio_np.astype(np.float32) / 32767.0
                
                return self._process_with_whisper(audio_float)
            
            # Fallback to Google recognition
            text = self.recognizer.recognize_google(audio_data)
            return text.strip() if text else None
            
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing audio from SR: {e}")
            return None
    
    def speak(self, text: str, blocking: bool = True) -> bool:
        """
        Convert text to speech and play it
        
        Args:
            text: Text to speak
            blocking: Whether to wait for speech to complete
            
        Returns:
            True if successful, False otherwise
        """
        if self.is_speaking:
            logger.warning("Already speaking")
            return False
        
        try:
            self.is_speaking = True
            logger.info(f"Speaking: {text}")
            
            if self.coqui_tts:
                return self._speak_with_coqui(text, blocking)
            elif self.tts_engine:
                return self._speak_with_pyttsx3(text, blocking)
            else:
                logger.error("No TTS engine available")
                return False
                
        except Exception as e:
            logger.error(f"Error speaking: {e}")
            return False
        finally:
            self.is_speaking = False
    
    def _speak_with_pyttsx3(self, text: str, blocking: bool) -> bool:
        """Speak using pyttsx3"""
        try:
            if blocking:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            else:
                # Run in separate thread for non-blocking
                def speak_thread():
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                    self.is_speaking = False
                
                threading.Thread(target=speak_thread, daemon=True).start()
            
            return True
            
        except Exception as e:
            logger.error(f"Error speaking with pyttsx3: {e}")
            return False
    
    def _speak_with_coqui(self, text: str, blocking: bool) -> bool:
        """Speak using Coqui TTS"""
        try:
            # Generate audio
            audio_data = self.coqui_tts.tts(text)
            
            # Play audio
            if blocking:
                sd.play(audio_data, samplerate=22050)
                sd.wait()
            else:
                # Play in separate thread for non-blocking
                def play_thread():
                    sd.play(audio_data, samplerate=22050)
                    sd.wait()
                    self.is_speaking = False
                
                threading.Thread(target=play_thread, daemon=True).start()
            
            return True
            
        except Exception as e:
            logger.error(f"Error speaking with Coqui: {e}")
            return False
    
    def set_voice_rate(self, rate: int):
        """Set voice speaking rate"""
        if self.tts_engine:
            self.tts_engine.setProperty('rate', rate)
            logger.info(f"Voice rate set to {rate}")
    
    def set_voice_volume(self, volume: float):
        """Set voice volume (0.0 to 1.0)"""
        if self.tts_engine:
            self.tts_engine.setProperty('volume', max(0.0, min(1.0, volume)))
            logger.info(f"Voice volume set to {volume}")
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        if self.tts_engine:
            voices = self.tts_engine.getProperty('voices')
            return [{'id': voice.id, 'name': voice.name} for voice in voices] if voices else []
        return []
    
    def set_voice(self, voice_id: str) -> bool:
        """Set specific voice by ID"""
        if self.tts_engine:
            try:
                self.tts_engine.setProperty('voice', voice_id)
                logger.info(f"Voice set to {voice_id}")
                return True
            except Exception as e:
                logger.error(f"Error setting voice: {e}")
                return False
        return False
    
    def is_available(self) -> bool:
        """Check if voice interface is available"""
        return (self.whisper_model is not None or self.recognizer is not None) and \
               (self.tts_engine is not None or self.coqui_tts is not None)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of voice interface"""
        return {
            'stt_available': self.whisper_model is not None or self.recognizer is not None,
            'tts_available': self.tts_engine is not None or self.coqui_tts is not None,
            'is_listening': self.is_listening,
            'is_speaking': self.is_speaking,
            'whisper_model': self.stt_config.get('whisper_model', 'base'),
            'tts_engine': self.tts_config.get('engine', 'pyttsx3'),
            'sample_rate': self.sample_rate,
            'vad_enabled': self.vad_enabled
        }
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.stop_listening()
            
            if getattr(self, 'tts_engine', None):
                self.tts_engine.stop()
            
            if getattr(self, 'coqui_tts', None):
                del self.coqui_tts
            
            if getattr(self, 'whisper_model', None):
                del self.whisper_model
            
            logger.info("Voice interface cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Global voice interface instance
voice_interface = FastVoiceInterface()
