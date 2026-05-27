export type CaptureMode = 'worklet' | 'script-processor' | 'unavailable';

export interface AudioState {
  isRecording: boolean;
  level: number;
  captureMode: CaptureMode;
  error: string | null;
}
