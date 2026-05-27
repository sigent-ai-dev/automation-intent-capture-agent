# Research: Browser Frontend

## 1. AudioWorklet Implementation

**Decision**: Use AudioWorklet as primary capture API, detect support at init, fall back to ScriptProcessorNode.

**Rationale**: AudioWorklet runs on a dedicated audio rendering thread — eliminates audio glitches caused by main-thread UI work. ScriptProcessorNode is deprecated (Chrome 105+ shows console warnings) but still functional in all browsers.

**Implementation pattern**:
```typescript
// Detection
const supportsWorklet = 'audioWorklet' in AudioContext.prototype;

// AudioWorklet path
await audioContext.audioWorklet.addModule('/audio-processor.js');
const workletNode = new AudioWorkletNode(audioContext, 'pcm-capture-processor');
workletNode.port.onmessage = (e) => sendAudio(e.data.buffer);

// Fallback path
const scriptNode = audioContext.createScriptProcessor(4096, 1, 1);
scriptNode.onaudioprocess = (e) => {
  const float32 = e.inputBuffer.getChannelData(0);
  const int16 = float32ToInt16(float32);
  sendAudio(int16.buffer);
};
```

**AudioWorklet processor** (`public/audio-processor.js`):
```javascript
class PCMCaptureProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0][0]; // mono channel
    if (input) {
      const int16 = new Int16Array(input.length);
      for (let i = 0; i < input.length; i++) {
        int16[i] = Math.max(-32768, Math.min(32767, input[i] * 32768));
      }
      this.port.postMessage({ buffer: int16.buffer }, [int16.buffer]);
    }
    return true;
  }
}
registerProcessor('pcm-capture-processor', PCMCaptureProcessor);
```

**Alternatives considered**:
- MediaRecorder API: produces Opus/WebM, not raw PCM — would require server-side decoding
- Web Codecs API: too new, poor Safari support

---

## 2. PCM Player Integration

**Decision**: Use `pcm-player` library (npm) with destroy/recreate pattern for barge-in.

**Rationale**: Same proven pattern as trainline-voice-poc. The library is small (~2KB) and handles Web Audio API buffer scheduling.

**Implementation pattern**:
```typescript
import PCMPlayer from 'pcm-player';

// Create player
const player = new PCMPlayer({
  inputCodec: 'Int16',
  channels: 1,
  sampleRate: 24000,
  flushTime: 100,
});

// Feed from WebSocket binary messages
ws.onmessage = (e) => {
  if (e.data instanceof ArrayBuffer) {
    player.feed(new Uint8Array(e.data));
  }
};

// Barge-in: destroy and recreate
function handleBargeIn() {
  player.destroy();
  // recreate fresh instance
}
```

**Alternatives considered**:
- Custom AudioBuffer queue: more control but 10x more code for same result
- Howler.js: designed for pre-loaded audio, not streaming PCM

---

## 3. react-window Dynamic Sizing

**Decision**: Use `VariableSizeList` with a ref-based height cache and `resetAfterIndex` on new messages.

**Rationale**: Messages vary in height (short utterances vs long agent paragraphs). Fixed-size lists waste space or clip content.

**Implementation pattern**:
```typescript
const listRef = useRef<VariableSizeList>(null);
const heightCache = useRef<Map<number, number>>(new Map());

const getItemSize = (index: number) => heightCache.current.get(index) || 80;

// After render, measure actual height and update cache
const setRowHeight = (index: number, height: number) => {
  if (heightCache.current.get(index) !== height) {
    heightCache.current.set(index, height);
    listRef.current?.resetAfterIndex(index);
  }
};

// Auto-scroll on new message
useEffect(() => {
  listRef.current?.scrollToItem(messages.length - 1, 'end');
}, [messages.length]);
```

**Alternatives considered**:
- `react-virtuoso`: better auto-sizing but larger bundle (15KB vs 6KB)
- No virtualization: fine for <100 messages, but sessions could run 500+ in long captures

---

## 4. Vite Proxy Configuration

**Decision**: Use Vite's built-in proxy with WebSocket support for local development.

**Rationale**: Avoids CORS issues during development. Single `npm run dev` command proxies both REST and WebSocket to the Python backend.

**Implementation** (`vite.config.ts`):
```typescript
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/sessions': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
      '/ws/audio': {
        target: 'ws://localhost:8080',
        ws: true,
      },
    },
  },
});
```

**Alternatives considered**:
- Separate CORS configuration on backend: works but leaks dev concerns into production code
- nginx reverse proxy: overkill for local dev
