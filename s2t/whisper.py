import numpy as np
import threading
import time
import queue
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import subprocess
import tempfile
import os
import wave

from logs.logger import logger

class WhisperRecorderNoAudioLib:
    def __init__(self, model_name="openai/whisper-base.en", chunk_duration=3.0, 
                 on_keyword_detected=None, on_sentence_transcribed=None):
        """
        Initialize the Whisper recorder using system commands for audio
        
        Args:
            model_name: Whisper model to use
            chunk_duration: Duration of audio chunks to process (seconds)
            on_keyword_detected: Callback function called when keyword is detected
                                Function signature: on_keyword_detected(transcription)
            on_sentence_transcribed: Callback function called when single recording is transcribed
                                   Function signature: on_sentence_transcribed(transcription)
        """
        self.model_name = model_name
        self.chunk_duration = int(chunk_duration)  # Convert to integer for arecord
        self.sample_rate = 16000  # Whisper expects 16kHz
        self.chunk_size = int(self.sample_rate * chunk_duration)
        
        # Initialize Whisper model
        logger.info(f"Loading Whisper model: {model_name}")
        self.processor = WhisperProcessor.from_pretrained(model_name, local_files_only=False)
        self.model = WhisperForConditionalGeneration.from_pretrained(model_name, local_files_only=False)
        
        
        # Move model to GPU if available
        if torch.cuda.is_available():
            self.model = self.model.to("cuda")
            logger.info("Using CUDA for inference")
        else:
            logger.info("Using CPU for inference")
        
        self.is_listening = True

        self.keyword_variations = ["jumbo", "jambo", "jumber", "jumba", "jambo", "jumbu", "dumbo"]
        
        # Store callback functions
        self.on_keyword_detected = on_keyword_detected
        self.on_sentence_transcribed = on_sentence_transcribed
    
    def is_silence(self, audio_data, threshold=0.01):
        """Check if audio is mostly silence"""
        rms = np.sqrt(np.mean(audio_data**2))
        return rms < threshold
    
    def record_audio_chunk(self, duration=3):
        """Record audio using arecord command and return numpy array"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            cmd = [
                'arecord',
                '-f', 'S16_LE',
                '-r', str(self.sample_rate),
                '-c', '1',
                '-d', str(int(duration)),
                temp_filename
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 5)
                if result.returncode != 0:
                    logger.error(f"arecord failed: {result.stderr}")
                    return None
            except subprocess.TimeoutExpired:
                logger.error("arecord command timed out")
                return None
            
            if not os.path.exists(temp_filename) or os.path.getsize(temp_filename) == 0:
                logger.error("No audio file created or file is empty")
                return None
            
            try:
                with wave.open(temp_filename, 'rb') as wav_file:
                    frames = wav_file.readframes(wav_file.getnframes())
                    audio_data = np.frombuffer(frames, dtype=np.int16)
                    audio_data = audio_data.astype(np.float32) / 32768.0
            except Exception as e:
                logger.error(f"Error reading WAV file: {e}")
                return None
            
            try:
                os.unlink(temp_filename)
            except:
                pass
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            return None

    def record_until_silence(self, silence_duration=2.0, chunk_size=1.0):
        """
        Record audio until there's silence for the specified duration
        """
        try:
            audio_chunks = []
            silence_start = None
            start_time = time.time()
            chunk_count = 0
            
            while True:
                chunk_count += 1
                audio_data = self.record_audio_chunk(chunk_size)
                if audio_data is None:
                    logger.error("Failed to record audio chunk, stopping")
                    break
                audio_chunks.append(audio_data)
                rms = np.sqrt(np.mean(audio_data**2))
                if self.is_silence(audio_data, threshold=0.005):
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start >= silence_duration:
                        break
                else:
                    silence_start = None
                elapsed_time = time.time() - start_time
                if elapsed_time > 30:
                    logger.warning(f"Recording timeout ({elapsed_time:.1f}s)")
                    break
            if audio_chunks:
                combined_audio = np.concatenate(audio_chunks)
                return combined_audio
            else:
                return None
        except Exception as e:
            logger.error(f"Error in record_until_silence: {e}")
            return None
    
    def process_audio_chunk(self, audio_chunk):
        """Process a single audio chunk and return transcription"""
        try:
            if self.is_silence(audio_chunk):
                return None
            if len(audio_chunk.shape) > 1:
                audio_chunk = audio_chunk.flatten()
            input_features = self.processor(
                audio_chunk, 
                sampling_rate=self.sample_rate, 
                return_tensors="pt"
            ).input_features
            if torch.cuda.is_available():
                input_features = input_features.to("cuda")
            with torch.no_grad():
                predicted_ids = self.model.generate(input_features)
            transcription = self.processor.batch_decode(
                predicted_ids, 
                skip_special_tokens=True
            )[0]
            transcription = transcription.strip()
            if len(transcription) < 3:
                return None
            false_positives = ['you', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
            if transcription.lower() in false_positives:
                return None
            return transcription
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return None
    
    def check_for_keyword(self, transcription):
        """Check if transcription contains the keyword (case insensitive)"""
        if transcription:
            for keyword in self.keyword_variations:
                if keyword.lower() in transcription.lower():
                    return True
        return False
    
    def single_recording_mode(self):
        """Run a single recording session when keyword is detected"""
        logger.info(f"Keyword 'Jumbo' detected! Starting single recording...")
        audio_data = self.record_until_silence(silence_duration=1.0)
        if audio_data is not None:
            transcription = self.process_audio_chunk(audio_data)
            if transcription:
                logger.success(f"Single Recording: {transcription}")
                if self.on_sentence_transcribed:
                    try:
                        self.on_sentence_transcribed(transcription)
                    except Exception as e:
                        logger.error(f"Error in on_sentence_transcribed callback: {e}")
            else:
                logger.info("Silence detected in single recording")
        else:
            logger.error("Failed to record audio")
        logger.info("Returning to continuous monitoring...")
    
    def run_continuous_with_keyword_detection(self):
        """Run continuous recording with keyword detection"""
        try:
            logger.info(f"Starting continuous Whisper transcription with keyword detection. Say 'Jumbo' to trigger single recording mode.")
            while True:
                # Check if listening is paused
                if not self.is_listening:
                    logger.info("Listening paused - waiting for resume...")
                    while not self.is_listening:
                        time.sleep(1)
                    logger.info("Listening resumed...")
                    continue
                
                audio_data = self.record_audio_chunk(self.chunk_duration)
                if audio_data is not None:
                    transcription = self.process_audio_chunk(audio_data)
                    if transcription:
                        if self.check_for_keyword(transcription):
                            if self.on_keyword_detected:
                                try:
                                    self.on_keyword_detected(transcription)
                                except Exception as e:
                                    logger.error(f"Error in on_keyword_detected callback: {e}")
                            else:
                                self.single_recording_mode()
                        else:
                            logger.info(f"Transcription: {transcription}")
                else:
                    logger.error("Recording failed")
        except KeyboardInterrupt:
            logger.info("Stopping transcription...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
    
    def run_continuous(self):
        """Run continuous recording and transcription (original mode)"""
        try:
            logger.info("Starting continuous Whisper transcription...")
            while True:
                audio_data = self.record_audio_chunk(self.chunk_duration)
                if audio_data is not None:
                    transcription = self.process_audio_chunk(audio_data)
                    if transcription:
                        logger.info(f"Transcription: {transcription}")
                else:
                    logger.error("Recording failed")
        except KeyboardInterrupt:
            logger.info("Stopping transcription...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
    
    def run_single_recording(self):
        """Run a single recording session"""
        try:
            input("Press Enter to start recording (or Ctrl+C to exit): ")
            audio_data = self.record_until_silence(silence_duration=2.0)
            if audio_data is not None:
                transcription = self.process_audio_chunk(audio_data)
                if transcription:
                    logger.success(f"Transcription: {transcription}")
                else:
                    logger.info("Silence detected")
            else:
                logger.error("Failed to record audio")
        except KeyboardInterrupt:
            logger.info("Exiting...")
        except Exception as e:
            logger.error(f"Error: {e}")

def main():
    """Main function to run the transcriber"""
    try:
        subprocess.run(['arecord', '--version'], capture_output=True, check=True)
        logger.success("arecord is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("arecord not found. Please install ALSA utilities: sudo apt-get install alsa-utils")
        return
    
    transcriber = WhisperRecorderNoAudioLib(
        model_name="openai/whisper-tiny.en",
        chunk_duration=3.0
    )
    
    print("\nChoose mode:")
    print("1. Single recording (press Enter to record)")
    print("2. Continuous recording (press Ctrl+C to stop)")
    print("3. Continuous with keyword detection (say 'jumbo' to trigger single recording)")
    
    choice = input("Enter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        transcriber.run_single_recording()
    elif choice == "2":
        transcriber.run_continuous()
    elif choice == "3":
        transcriber.run_continuous_with_keyword_detection()
    else:
        logger.warning("Invalid choice. Using continuous with keyword detection mode.")
        transcriber.run_continuous_with_keyword_detection()

# if __name__ == "__main__":
#     main()
