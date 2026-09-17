import React, { useState, useRef, useEffect } from "react";
import { useAppDispatch, useAppSelector } from "../../app/hooks";
import { addUserMessage, sendMessage } from "../../features/chat/chatSlice";

export const CopilotChat: React.FC = () => {
  const dispatch = useAppDispatch();
  const { messages, loading, error } = useAppSelector((state) => state.chat);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSend = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (loading) return;

    if (!input.trim()) {
      setValidationError("Message cannot be empty.");
      return;
    }

    setValidationError(null);
    dispatch(addUserMessage(input));
    dispatch(sendMessage(input));
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="copilot-chat-container">
      <div className="chat-header">
        <h2>Copilot</h2>
      </div>

      <div className="chat-messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-message ${msg.role}`}>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}
        {loading && (
          <div className="chat-message assistant loading">
            <div className="message-content">Processing...</div>
          </div>
        )}
        {error && (
          <div className="chat-error">
            <p>Error: {error}</p>
          </div>
        )}
        {validationError && (
          <div className="chat-error">
            <p>Validation Error: {validationError}</p>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-container">
        <form onSubmit={handleSend}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type complaint or correction..."
            disabled={loading}
            rows={3}
          />
          <button type="submit" disabled={!input.trim() || loading}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
};
