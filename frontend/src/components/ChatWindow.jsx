import { useState, useRef, useEffect } from 'react';
import { Send, Mic, Paperclip, Sprout, Cloud, Loader, AlertTriangle, CheckCircle } from 'lucide-react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAuth } from '../context/AuthContext';

const API_BASE = "http://localhost:8000";

const WELCOME_CHIPS = [
  "🌾 What should I plant this season?",
  "🍃 My tomato leaves have spots, help!",
  "💧 How much to irrigate wheat today?",
  "📈 Best time to sell my crop?",
];

function ThinkingBubble({ steps }) {
  return (
    <div className="message ai" style={{ maxWidth: '90%' }}>
      <div className="message-avatar">
        <Sprout size={14} />
      </div>
      <div className="thinking-bubble">
        <div className="thinking-header">
          <div className="thinking-dots">
            <span /><span /><span />
          </div>
          Analyzing your query...
        </div>
        {steps.map((step, i) => (
          <div className="thinking-step" key={i}>
            <Loader size={12} style={{ animation: 'spin 1s linear infinite' }} />
            {step}
          </div>
        ))}
      </div>
    </div>
  );
}

function Message({ msg }) {
  return (
    <div className={`message ${msg.role}`}>
      <div className="message-avatar">
        {msg.role === 'user' ? 'RS' : <Sprout size={14} />}
      </div>
      <div>
        <div className="message-bubble">
          {msg.image && (
            <div className="disease-result-card" style={{ marginBottom: 8, marginTop: 0 }}>
              <img src={msg.image} alt="Uploaded crop" className="disease-result-img" />
            </div>
          )}
          {msg.disease && (
            <div className="disease-result-card" style={{ marginBottom: 10 }}>
              <div className="disease-result-body">
                <span className={`disease-badge ${msg.disease.healthy ? 'success' : 'warning'}`}>
                  {msg.disease.healthy
                    ? <><CheckCircle size={11} /> Healthy Plant</>
                    : <><AlertTriangle size={11} /> {msg.disease.name}</>
                  }
                </span>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  Confidence: {msg.disease.confidence}
                </div>
              </div>
            </div>
          )}
          {/* Render AI messages as markdown, user messages as plain text */}
          {msg.role === 'ai' ? (
            <div className={`markdown-body ${msg.isStreaming ? 'streaming' : ''}`}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content || (msg.isStreaming ? ' ' : '')}</ReactMarkdown>
            </div>
          ) : (
            <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>
          )}
        </div>
        <span className="message-time">{msg.time}</span>
      </div>
    </div>
  );
}

export default function ChatWindow({ onChipClick, activeThreadId, setActiveThreadId }) {
  const { authFetch } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [thinkingSteps, setThinkingSteps] = useState([]);
  const [pendingContext, setPendingContext] = useState('');
  const [stagedImage, setStagedImage] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => { scrollToBottom(); }, [messages, isLoading]);

  // Load chat history when activeThreadId changes
  useEffect(() => {
    if (activeThreadId) {
      setIsLoading(true);
      fetch(`${API_BASE}/api/v1/chat/sessions/${activeThreadId}/messages`)
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data)) {
            const history = data.map(m => ({
              role: m.role,
              content: m.content,
              time: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }));
            setMessages(history);
          }
        })
        .catch(err => console.error("Failed to fetch messages:", err))
        .finally(() => setIsLoading(false));
    } else {
      setMessages([]); // New chat
    }
  }, [activeThreadId]);

  const getTime = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const sendMessage = async (text) => {
    if ((!text.trim() && !stagedImage) || isLoading) return;

    let finalMessageText = text;
    let combinedContext = pendingContext;

    if (stagedImage) {
      const userMsg = {
        role: 'user',
        content: text || "Analyzing this crop image for diseases...",
        image: stagedImage.url,
        time: getTime()
      };
      setMessages(prev => [...prev, userMsg]);
      setInput('');
      setIsLoading(true);
      setThinkingSteps(["Uploading image...", "Running ONNX disease detection model..."]);

      const formData = new FormData();
      formData.append('file', stagedImage.file);
      setStagedImage(null); // clear staging

      try {
        const response = await axios.post(`${API_BASE}/api/v1/disease/analyze`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        const result = response.data;
        const topPred = result.predictions && result.predictions.length > 0 ? result.predictions[0] : null;
        
        const diseaseName = topPred ? topPred.disease_name : 'Unknown';
        const confidence = topPred ? topPred.confidence : 'N/A';
        const isHealthy = topPred ? topPred.is_healthy : false;
        const treatments = topPred && topPred.treatment_recommendations && topPred.treatment_recommendations.length > 0
          ? topPred.treatment_recommendations.join(", ") 
          : 'Please consult a local agricultural expert for treatment options.';

        const aiMsg = {
          role: 'ai',
          content: `Disease detection complete!\n\n**Diagnosis:** ${diseaseName}\n**Confidence:** ${confidence}%\n\n**Advice:** ${treatments}`,
          disease: {
            name: diseaseName,
            confidence: `${confidence}%`,
            healthy: isHealthy
          },
          time: getTime()
        };
        setMessages(prev => [...prev, aiMsg]);
        
        const contextMsg = `[SYSTEM CONTEXT: The user just uploaded an image of a crop. The ONNX Computer Vision model analyzed it and detected: ${diseaseName} (Confidence: ${confidence}%). The automated advice given was: ${treatments}. Please use this context if the user asks any follow up questions about the image.]`;
        
        combinedContext = combinedContext ? `${combinedContext}\n\n${contextMsg}` : contextMsg;
        finalMessageText = text.trim() ? text : "Can you give me more details about this disease and how to manage it?";

      } catch (error) {
        const aiMsg = {
          role: 'ai',
          content: "📸 Image received! The disease detection model uses an optimized ONNX runtime (converted from a 241MB PyTorch model to just 1.4MB) to identify plant diseases.\n\nConnect the backend to get real-time disease analysis.",
          disease: { name: "Early Blight (Demo)", confidence: "94%", healthy: false },
          time: getTime()
        };
        setMessages(prev => [...prev, aiMsg]);
        finalMessageText = text.trim() ? text : "What can you tell me about the disease in the image?";
      }
    } else {
      const userMsg = { role: 'user', content: text, time: getTime() };
      setMessages(prev => [...prev, userMsg]);
      setInput('');
      setIsLoading(true);
    }

    setThinkingSteps(["Searching knowledge base...", "Running crop intelligence..."]);

    // Use the streaming endpoint so tokens appear word-by-word.
    try {
      const fullMessage = combinedContext ? `${combinedContext}\n\nUser Question: ${finalMessageText}` : finalMessageText;
      setPendingContext(''); // Clear it so it's only sent once

      const res = await authFetch(`${API_BASE}/api/v1/chat/message`, {
        method: 'POST',
        body: JSON.stringify({
          message: fullMessage,
          thread_id: activeThreadId,
        }),
      });

      if (!res.ok) {
        throw new Error(`Backend error: ${res.status} ${res.statusText}`);
      }

      // We don't hide the thinking bubble immediately.
      // We will hide it and show the placeholder only when the first actual text token arrives.
      let placeholderCreated = false;
      const placeholderId = Date.now();

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let currentEventType = 'message'; // default SSE event type

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            // Track the event type; reset after each blank line
            currentEventType = line.slice(7).trim();
          } else if (line === '') {
            // Blank line = end of SSE event block, reset event type
            currentEventType = 'message';
          } else if (line.startsWith('data: ')) {
            const data = line.slice(6); // strip "data: " prefix
            
            // Capture thread_id from the backend so we have conversation memory
            if (currentEventType === 'thread_id' && data) {
              if (activeThreadId !== data) {
                setActiveThreadId(data);
              }
            }

            if (currentEventType === 'error' && data) {
               try {
                 const errData = JSON.parse(data);
                 throw new Error(errData.error || errData);
               } catch (e) {
                 throw new Error(data);
               }
            }
            
            // Only append to chat for default (unnamed) events — skip thread_id, done, tool_status, etc.
            if (currentEventType === 'message' && data && data !== '{}') {
              let parsedText = data;
              try {
                // We JSON encode the text on the backend to preserve newlines and markdown over SSE
                parsedText = JSON.parse(data);
              } catch (e) {
                // Fallback in case of plain text
              }

              if (!placeholderCreated) {
                // First actual token arrived! Hide thinking bubble and create the streaming message bubble
                setIsLoading(false);
                setThinkingSteps([]);
                setMessages(prev => [...prev, { role: 'ai', content: parsedText, time: getTime(), id: placeholderId, isStreaming: true }]);
                placeholderCreated = true;
              } else {
                setMessages(prev => {
                  const updated = [...prev];
                  const lastIdx = updated.length - 1;
                  if (updated[lastIdx]?.role === 'ai') {
                    updated[lastIdx] = {
                      ...updated[lastIdx],
                      content: updated[lastIdx].content + parsedText,
                    };
                  }
                  return updated;
                });
              }
            }
          }
        }
      }

      // Stream is finished
      setIsLoading(false);
      setThinkingSteps([]);
      if (placeholderCreated) {
        setMessages(prev => prev.map(m => m.id === placeholderId ? { ...m, isStreaming: false } : m));
      }
    } catch (error) {
      console.error('Chat streaming error:', error.message);
      setIsLoading(false);
      setThinkingSteps([]);
      const fallbackMsg = {
        role: 'ai',
        content: `⚠️ Backend is not responding (${API_BASE}).\n\nError: ${error.message}\n\nMake sure the backend is running:\n  cd farming-assistant/backend\n  ./venv/bin/uvicorn app.main:app --reload`,
        time: getTime()
      };
      setMessages(prev => [...prev, fallbackMsg]);
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const imageUrl = URL.createObjectURL(file);
    setStagedImage({ file, url: imageUrl });
    
    // Reset the input value so the same file can be selected again if needed
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => audioChunksRef.current.push(e.data);
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.webm');

        setIsLoading(true);
        setThinkingSteps(["Transcribing audio with Whisper STT..."]);
        try {
          const response = await axios.post(`${API_BASE}/api/v1/voice/transcribe`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
          const transcribed = response.data.text;
          setInput(transcribed);
        } catch {
          setInput("Voice transcription available when backend is connected.");
        } finally {
          setIsLoading(false);
          setThinkingSteps([]);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch {
      alert("Microphone access is required for voice input.");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="chat-container">
      <div className="messages-area">
        {isEmpty ? (
          <div className="welcome-screen">
            <div className="welcome-logo">
              <Sprout size={28} color="white" />
            </div>
            <div className="welcome-title">How can I help your farm today?</div>
            <div className="welcome-subtitle">
              Ask me anything about your crops, soil, weather, diseases, or market prices.
            </div>
            <div className="welcome-chips">
              {WELCOME_CHIPS.map((chip) => (
                <button
                  key={chip}
                  className="welcome-chip"
                  onClick={() => sendMessage(chip)}
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => <Message key={i} msg={msg} />)
        )}

        {isLoading && <ThinkingBubble steps={thinkingSteps} />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="input-bar-wrapper">
        {stagedImage && (
          <div className="staged-image-container">
            <div className="staged-image-wrapper">
               <img src={stagedImage.url} alt="Staged" className="staged-image" />
               <button className="remove-staged-btn" onClick={() => setStagedImage(null)}>✕</button>
            </div>
          </div>
        )}
        <div className="input-bar">
          <button
            className={`input-action-btn mic-btn ${isRecording ? 'recording' : ''}`}
            onClick={toggleRecording}
            title={isRecording ? "Stop recording" : "Record voice message"}
          >
            <Mic size={15} />
          </button>

          <button
            className="input-action-btn"
            onClick={() => fileInputRef.current?.click()}
            title="Upload crop image for disease detection"
          >
            <Paperclip size={15} />
          </button>

          <input
            type="file"
            ref={fileInputRef}
            accept="image/*"
            style={{ display: 'none' }}
            onChange={handleImageUpload}
          />

          <input
            type="text"
            placeholder="Ask about your crops, weather, market prices..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />

          <button
            className="send-btn"
            onClick={() => sendMessage(input)}
            disabled={(!input.trim() && !stagedImage) || isLoading}
          >
            <Send size={15} />
          </button>
        </div>
        <div className="input-hint">
          <span><Mic size={10} /> Voice</span>
          <span><Paperclip size={10} /> Image</span>
          <span><Cloud size={10} /> AI-powered</span>
        </div>
      </div>
    </div>
  );
}
