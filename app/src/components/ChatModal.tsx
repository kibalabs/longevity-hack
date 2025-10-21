import React from 'react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatModalProps {
  isOpen: boolean;
  onClose: () => void;
  categoryName: string;
  categoryDescription: string;
  onSendMessage: (message: string) => Promise<string>;
}

export function ChatModal(props: ChatModalProps): React.ReactElement | null {
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = (): void => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (): Promise<void> => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    // Add user message to chat
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    try {
      // Get response from API
      const response = await props.onSendMessage(userMessage);
      
      // Add assistant response
      setMessages(prev => [...prev, { role: 'assistant', content: response }]);
    } catch (error) {
      console.error('Failed to get response:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent): void => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSendMessage();
    }
  };

  if (!props.isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '24px',
    }}
    onClick={props.onClose}>
      <div 
        style={{
          width: '100%',
          maxWidth: '800px',
          height: '600px',
          maxHeight: '90vh',
          background: 'linear-gradient(145deg, rgba(255, 255, 255, 0.98) 0%, rgba(252, 248, 255, 0.98) 100%)',
          borderRadius: '24px',
          border: '2px solid rgba(102, 126, 234, 0.2)',
          boxShadow: '0 20px 60px rgba(102, 126, 234, 0.25)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}>
        
        {/* Header */}
        <div style={{
          padding: '24px 32px',
          borderBottom: '2px solid rgba(102, 126, 234, 0.15)',
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <div>
              <h2 style={{
                fontSize: '24px',
                fontWeight: 700,
                color: 'white',
                margin: '0 0 8px 0',
              }}>Ask Your AI Agent</h2>
              <p style={{
                fontSize: '15px',
                color: 'rgba(255, 255, 255, 0.9)',
                margin: 0,
              }}>{props.categoryName}</p>
            </div>
            <button
              onClick={props.onClose}
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                border: 'none',
                background: 'rgba(255, 255, 255, 0.2)',
                color: 'white',
                fontSize: '20px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.3)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)';
              }}>
              ×
            </button>
          </div>
        </div>

        {/* Messages */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '24px 32px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}>
          {messages.length === 0 && (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              gap: '16px',
              color: '#888',
            }}>
              <div style={{ fontSize: '48px' }}>🤖</div>
              <p style={{ 
                fontSize: '16px',
                textAlign: 'center',
                maxWidth: '400px',
                lineHeight: '1.6',
                margin: 0,
              }}>
                Ask me anything about {props.categoryName}. I'll help you understand your genetic results and what they mean for your health.
              </p>
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
              }}>
              <div
                style={{
                  maxWidth: '70%',
                  padding: '12px 18px',
                  borderRadius: message.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                  background: message.role === 'user' 
                    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                    : 'rgba(102, 126, 234, 0.08)',
                  color: message.role === 'user' ? 'white' : '#1a1a1a',
                  fontSize: '15px',
                  lineHeight: '1.6',
                  wordWrap: 'break-word',
                  whiteSpace: 'pre-wrap',
                }}>
                {message.content}
              </div>
            </div>
          ))}

          {isLoading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
              <div style={{
                padding: '12px 18px',
                borderRadius: '18px 18px 18px 4px',
                background: 'rgba(102, 126, 234, 0.08)',
                fontSize: '15px',
                color: '#666',
              }}>
                <span style={{ animation: 'pulse 1.5s ease-in-out infinite' }}>Thinking...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div style={{
          padding: '20px 32px 24px 32px',
          borderTop: '2px solid rgba(102, 126, 234, 0.15)',
        }}>
          <div style={{
            display: 'flex',
            gap: '12px',
            alignItems: 'flex-end',
          }}>
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question..."
              disabled={isLoading}
              style={{
                flex: 1,
                padding: '14px 18px',
                borderRadius: '14px',
                border: '2px solid rgba(102, 126, 234, 0.2)',
                fontSize: '15px',
                resize: 'none',
                fontFamily: 'inherit',
                minHeight: '52px',
                maxHeight: '120px',
                background: 'white',
                color: '#1a1a1a',
                transition: 'border-color 0.2s ease',
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.5)';
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = 'rgba(102, 126, 234, 0.2)';
              }}
            />
            <button
              onClick={() => void handleSendMessage()}
              disabled={!inputMessage.trim() || isLoading}
              style={{
                padding: '14px 24px',
                background: (!inputMessage.trim() || isLoading)
                  ? 'rgba(0, 0, 0, 0.15)'
                  : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '14px',
                fontSize: '15px',
                fontWeight: 700,
                cursor: (!inputMessage.trim() || isLoading) ? 'not-allowed' : 'pointer',
                transition: 'all 0.3s ease',
                boxShadow: (!inputMessage.trim() || isLoading) 
                  ? 'none' 
                  : '0 4px 16px rgba(102, 126, 234, 0.3)',
                minHeight: '52px',
              }}
              onMouseEnter={(e) => {
                if (inputMessage.trim() && !isLoading) {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.4)';
                }
              }}
              onMouseLeave={(e) => {
                if (inputMessage.trim() && !isLoading) {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '0 4px 16px rgba(102, 126, 234, 0.3)';
                }
              }}>
              Send
            </button>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}
