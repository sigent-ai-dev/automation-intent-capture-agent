import { useCallback, useRef, useState } from 'react';
import { CONFIG } from '../config/constants';
import { supportsAudioWorklet, float32ToInt16, computeLevel } from '../utils/audioUtils';
import type { CaptureMode } from '../types/audio';

interface UseAudioCaptureOptions {
  onAudioData: (buffer: ArrayBuffer) => void;
  onLevelChange: (level: number) => void;
}

export function useAudioCapture({ onAudioData, onLevelChange }: UseAudioCaptureOptions) {
  const [isRecording, setIsRecording] = useState(false);
  const [captureMode, setCaptureMode] = useState<CaptureMode>('worklet');
  const [error, setError] = useState<string | null>(null);

  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const scriptNodeRef = useRef<ScriptProcessorNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: CONFIG.INPUT_SAMPLE_RATE, channelCount: 1, echoCancellation: true },
      });
      streamRef.current = stream;

      const ctx = new AudioContext({ sampleRate: CONFIG.INPUT_SAMPLE_RATE });
      audioContextRef.current = ctx;
      const source = ctx.createMediaStreamSource(stream);
      sourceRef.current = source;

      if (supportsAudioWorklet()) {
        await ctx.audioWorklet.addModule('/audio-processor.js');
        const worklet = new AudioWorkletNode(ctx, 'pcm-capture-processor');
        workletNodeRef.current = worklet;
        worklet.port.onmessage = (e) => {
          onAudioData(e.data.buffer);
          onLevelChange(e.data.level);
        };
        source.connect(worklet);
        worklet.connect(ctx.destination);
        setCaptureMode('worklet');
      } else {
        const scriptNode = ctx.createScriptProcessor(4096, 1, 1);
        scriptNodeRef.current = scriptNode;
        scriptNode.onaudioprocess = (e) => {
          const float32 = e.inputBuffer.getChannelData(0);
          const int16 = float32ToInt16(float32);
          onAudioData(int16.buffer);
          onLevelChange(computeLevel(float32));
        };
        source.connect(scriptNode);
        scriptNode.connect(ctx.destination);
        setCaptureMode('script-processor');
      }

      setIsRecording(true);
      setError(null);
    } catch (err) {
      if (err instanceof DOMException && err.name === 'NotAllowedError') {
        setCaptureMode('unavailable');
        setError('Microphone permission denied. Use text input instead.');
      } else {
        setError(`Audio capture error: ${err}`);
      }
    }
  }, [onAudioData, onLevelChange]);

  const stopRecording = useCallback(() => {
    workletNodeRef.current?.disconnect();
    scriptNodeRef.current?.disconnect();
    sourceRef.current?.disconnect();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    audioContextRef.current?.close();

    workletNodeRef.current = null;
    scriptNodeRef.current = null;
    sourceRef.current = null;
    streamRef.current = null;
    audioContextRef.current = null;

    setIsRecording(false);
    onLevelChange(0);
  }, [onLevelChange]);

  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  return { isRecording, captureMode, error, toggleRecording, startRecording, stopRecording };
}
