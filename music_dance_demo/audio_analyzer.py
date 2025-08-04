import numpy as np
import threading
import queue
import librosa
import pygame
from scipy import signal


class AudioAnalyzer:
    def __init__(self):
        self.sample_rate = 22050
        self.frame_size = 2048
        self.hop_length = 512
        self.tempo = 120
        self.beat_times = []
        self.onset_times = []
        self.energy_history = []
        self.is_playing = False
        self.current_time = 0
        self.audio_queue = queue.Queue()
        
        pygame.mixer.init()
    
    def load_music(self, file_path):
        try:
            self.y, self.sr = librosa.load(file_path, sr=self.sample_rate)
            self.analyze_audio()
            pygame.mixer.music.load(file_path)
            return True
        except Exception as e:
            print(f"Error loading music: {e}")
            return False
    
    def analyze_audio(self):
        self.tempo, self.beat_frames = librosa.beat.beat_track(
            y=self.y, 
            sr=self.sr, 
            hop_length=self.hop_length
        )
        
        self.beat_times = librosa.frames_to_time(
            self.beat_frames, 
            sr=self.sr, 
            hop_length=self.hop_length
        )
        
        onset_envelope = librosa.onset.onset_strength(
            y=self.y, 
            sr=self.sr, 
            hop_length=self.hop_length
        )
        self.onset_times = librosa.onset.onset_detect(
            onset_envelope=onset_envelope,
            sr=self.sr,
            hop_length=self.hop_length,
            units='time'
        )
        
        self.rms_energy = librosa.feature.rms(
            y=self.y, 
            frame_length=self.frame_size, 
            hop_length=self.hop_length
        )[0]
        
        self.spectral_centroids = librosa.feature.spectral_centroid(
            y=self.y, 
            sr=self.sr, 
            hop_length=self.hop_length
        )[0]
    
    def get_current_beat_strength(self):
        if not self.is_playing:
            return 0.0
        
        current_time = pygame.mixer.music.get_pos() / 1000.0
        
        frame_idx = int(current_time * self.sr / self.hop_length)
        if frame_idx >= len(self.rms_energy):
            return 0.0
        
        current_energy = self.rms_energy[frame_idx]
        
        is_beat = any(abs(current_time - beat_time) < 0.05 for beat_time in self.beat_times)
        
        beat_strength = current_energy
        if is_beat:
            beat_strength *= 1.5
        
        return float(np.clip(beat_strength, 0, 1))
    
    def get_current_frequency_profile(self):
        if not self.is_playing:
            return "low"
        
        current_time = pygame.mixer.music.get_pos() / 1000.0
        frame_idx = int(current_time * self.sr / self.hop_length)
        
        if frame_idx >= len(self.spectral_centroids):
            return "low"
        
        centroid = self.spectral_centroids[frame_idx]
        
        if centroid < 2000:
            return "low"
        elif centroid < 4000:
            return "mid"
        else:
            return "high"
    
    def play(self):
        pygame.mixer.music.play()
        self.is_playing = True
    
    def pause(self):
        pygame.mixer.music.pause()
        self.is_playing = False
    
    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False
    
    def set_volume(self, volume):
        pygame.mixer.music.set_volume(volume)
    
    def get_tempo(self):
        return self.tempo
    
    def is_on_beat(self):
        if not self.is_playing:
            return False
        
        current_time = pygame.mixer.music.get_pos() / 1000.0
        return any(abs(current_time - beat_time) < 0.05 for beat_time in self.beat_times)