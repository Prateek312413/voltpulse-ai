/**
 * Audio Capture & Real-time Waveform Visualizer
 * High-performance Web Audio API integration with fallback dysarthric speech simulators.
 */
class AudioController {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.canvasCtx = this.canvas ? this.canvas.getContext('2d') : null;
    this.audioCtx = null;
    this.analyser = null;
    this.microphone = null;
    this.isRecording = false;
    this.recordedChunks = [];
    this.mediaRecorder = null;
    this.animationId = null;

    this.initCanvas();
  }

  initCanvas() {
    if (!this.canvas) return;
    this.canvas.width = this.canvas.offsetWidth * window.devicePixelRatio || 600;
    this.canvas.height = this.canvas.offsetHeight * window.devicePixelRatio || 120;
    this.drawIdleWaveform();
  }

  drawIdleWaveform() {
    if (!this.canvasCtx) return;
    const ctx = this.canvasCtx;
    const width = this.canvas.width;
    const height = this.canvas.height;

    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, width, height);

    ctx.lineWidth = 2;
    ctx.strokeStyle = '#3b82f6';
    ctx.beginPath();

    const sliceWidth = width / 100;
    let x = 0;
    for (let i = 0; i < 100; i++) {
      const y = (height / 2) + Math.sin(i * 0.2) * 4;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
      x += sliceWidth;
    }
    ctx.stroke();
  }

  async startRecording() {
    try {
      this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      this.analyser = this.audioCtx.createAnalyser();
      this.analyser.fftSize = 512;
      this.microphone = this.audioCtx.createMediaStreamSource(stream);
      this.microphone.connect(this.analyser);

      this.mediaRecorder = new MediaRecorder(stream);
      this.recordedChunks = [];
      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) this.recordedChunks.push(e.data);
      };

      this.mediaRecorder.start();
      this.isRecording = true;
      this.visualize();
      return true;
    } catch (err) {
      console.warn("Microphone access unavailable or denied. Using synthetic simulation mode.", err);
      this.simulateRecording();
      return false;
    }
  }

  visualize() {
    if (!this.analyser || !this.isRecording) return;
    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    const ctx = this.canvasCtx;
    const width = this.canvas.width;
    const height = this.canvas.height;

    const render = () => {
      if (!this.isRecording) return;
      this.animationId = requestAnimationFrame(render);
      this.analyser.getByteTimeDomainData(dataArray);

      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, width, height);

      ctx.lineWidth = 2.5;
      ctx.strokeStyle = '#00e5ff';
      ctx.beginPath();

      const sliceWidth = width / bufferLength;
      let x = 0;
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = v * (height / 2);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        x += sliceWidth;
      }
      ctx.lineTo(width, height / 2);
      ctx.stroke();
    };
    render();
  }

  simulateRecording() {
    this.isRecording = true;
    const ctx = this.canvasCtx;
    const width = this.canvas.width;
    const height = this.canvas.height;
    let phase = 0;

    const renderSim = () => {
      if (!this.isRecording) return;
      this.animationId = requestAnimationFrame(renderSim);
      phase += 0.1;

      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, width, height);

      ctx.lineWidth = 2.5;
      ctx.strokeStyle = '#38bdf8';
      ctx.beginPath();

      const sliceWidth = width / 80;
      let x = 0;
      for (let i = 0; i < 80; i++) {
        const amp = Math.sin(i * 0.15 + phase) * Math.sin(phase * 0.5) * (height / 3);
        const y = (height / 2) + amp;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        x += sliceWidth;
      }
      ctx.stroke();
    };
    renderSim();
  }

  async stopRecording() {
    this.isRecording = false;
    if (this.animationId) cancelAnimationFrame(this.animationId);
    
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      return new Promise((resolve) => {
        this.mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(this.recordedChunks, { type: 'audio/wav' });
          this.drawIdleWaveform();
          resolve(audioBlob);
        };
        this.mediaRecorder.stop();
      });
    }

    this.drawIdleWaveform();
    return null;
  }

  generateSyntheticDysarthricAudio(wordHint = "HELP") {
    // Generates a mock 16-bit PCM byte stream for simulated offline testing
    const sampleRate = 16000;
    const durationSec = 0.6;
    const totalSamples = Math.floor(sampleRate * durationSec);
    const buffer = new Int16Array(totalSamples);

    for (let i = 0; i < totalSamples; i++) {
      const t = i / sampleRate;
      // Synthesize vowel formant fundamental + slight slurred harmonic noise
      const f0 = 120;
      const f1 = wordHint === "WATER" ? 350 : 700;
      const signal = Math.sin(2 * Math.PI * f0 * t) * 0.6 + Math.sin(2 * Math.PI * f1 * t) * 0.4;
      const noise = (Math.random() - 0.5) * 0.15;
      buffer[i] = Math.floor((signal + noise) * 20000);
    }

    let binary = '';
    const bytes = new Uint8Array(buffer.buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }
}
