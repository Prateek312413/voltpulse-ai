"""
Pydantic Data Schemas for NeuroAccess API
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class RestoreSpeechRequest(BaseModel):
    raw_text_hint: Optional[str] = Field(None, description="Degraded or slurred word hint (e.g., 'wtr', 'hlp')")
    phonemes: Optional[List[str]] = Field(None, description="List of detected phoneme tokens")
    audio_base64: Optional[str] = Field(None, description="Base64 encoded WAV/PCM audio for edge decoding")

class CandidateWord(BaseModel):
    word: str
    confidence: float

class RestoreSpeechResponse(BaseModel):
    restored_word: str
    confidence_score: float
    phoneme_sequence: List[str]
    alternative_candidates: List[CandidateWord]
    clarity_boost_db: float

class PredictIntentRequest(BaseModel):
    tokens: List[str] = Field(..., min_length=1, description="Selected AAC tokens or restored keywords")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Environmental and temporal metadata")

class IntentPhrase(BaseModel):
    phrase: str
    confidence: float
    urgency: str
    category: str
    speech_rate: float
    speech_pitch: float

class PredictIntentResponse(BaseModel):
    selected_tokens: List[str]
    predictions: List[IntentPhrase]

class SOSTriggerRequest(BaseModel):
    trigger_source: str = Field("MANUAL_AAC_SWITCH", description="Origin of emergency trigger")
    message: Optional[str] = Field("EMERGENCY: Immediate caregiver assistance required!")
    patient_id: Optional[str] = Field("PT-8042-NEURO")
    location: Optional[Dict[str, Any]] = None

class SOSTriggerResponse(BaseModel):
    alert_id: str
    patient_id: str
    timestamp: str
    trigger_source: str
    message: str
    urgency: str
    dispatched_channels: List[str]
    acknowledgment_status: str
    response_time_ms: int

class SystemHealthResponse(BaseModel):
    status: str
    service: str
    version: str
    sample_rate: int
    dsp_pipeline_ready: bool
    total_sos_incidents: int
    active_contacts: int
