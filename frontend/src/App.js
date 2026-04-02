import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Sparkles } from "lucide-react";
import axios from "axios";
import "@/App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const translations = {
  en: {
    mainQuestion: "How do you feel today?",
    beginButton: "Begin",
    chatPlaceholder: "Share what's on your mind...",
  },
  fr: {
    mainQuestion: "Comment vous sentez-vous aujourd'hui ?",
    beginButton: "Commencer",
    chatPlaceholder: "Exprimez vos pensées...",
  }
};

function App() {
  const [started, setStarted] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [dailyReflection, setDailyReflection] = useState({ en: "", fr: "" });
  const [language, setLanguage] = useState("en");
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    // Detect browser language
    const browserLang = navigator.language || navigator.userLanguage;
    if (browserLang.toLowerCase().startsWith('fr')) {
      setLanguage('fr');
    }
    fetchDailyReflection();
  }, []);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  useEffect(() => {
    if (started && inputRef.current) {
      inputRef.current.focus();
    }
  }, [started]);

  const fetchDailyReflection = async () => {
    try {
      const response = await axios.get(`${API}/daily-reflection`);
      setDailyReflection(response.data);
    } catch (error) {
      console.error("Failed to fetch daily reflection:", error);
    }
  };

  const handleStart = () => {
    setStarted(true);
  };

  const toggleLanguage = () => {
    setLanguage(prev => prev === "en" ? "fr" : "en");
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue("");
    
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        message: userMessage
      });
      
      setMessages(prev => [...prev, { 
        role: "ai", 
        content: response.data.response 
      }]);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMsg = language === "fr" 
        ? "Désolé, une erreur s'est produite. Veuillez réessayer."
        : "Sorry, something went wrong. Please try again.";
      setMessages(prev => [...prev, { role: "ai", content: errorMsg }]);
    } finally {
      setIsLoading(false);
    }
  };

  const t = translations[language];

  if (!started) {
    return (
      <div className="min-h-screen w-full bg-black flex items-center justify-center relative overflow-hidden">
        <div 
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `url('https://static.prod-images.emergentagent.com/jobs/a2025be9-9ee4-476a-919c-46e92129890e/images/8c4de83f72de4547628e25d933e1017da74d6a64a5ca964c42c0ab288e67e7c1.png')`,
            backgroundSize: 'cover',
            backgroundPosition: 'center'
          }}
        />
        
        {/* Language Switcher */}
        <motion.div 
          className="absolute top-6 right-6 sm:top-8 sm:right-8 z-20"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <div className="flex items-center gap-2 text-sm font-light">
            <button
              onClick={() => setLanguage('en')}
              className={`transition-colors duration-300 ${
                language === 'en' 
                  ? 'text-[#D4AF37] font-medium' 
                  : 'text-white/50 hover:text-white/80'
              }`}
              data-testid="lang-switch-en"
            >
              EN
            </button>
            <span className="text-white/30">|</span>
            <button
              onClick={() => setLanguage('fr')}
              className={`transition-colors duration-300 ${
                language === 'fr' 
                  ? 'text-[#D4AF37] font-medium' 
                  : 'text-white/50 hover:text-white/80'
              }`}
              data-testid="lang-switch-fr"
            >
              FR
            </button>
          </div>
        </motion.div>
        
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.2, ease: "easeOut" }}
          className="relative z-10 flex flex-col items-center justify-center px-6 sm:px-12 max-w-4xl mx-auto text-center"
        >
          <motion.img
            src="https://static.prod-images.emergentagent.com/jobs/a2025be9-9ee4-476a-919c-46e92129890e/images/5919e22cd369047abe23906169ab5aea282959e86819b16d96cee17d758446ad.png"
            alt="AUREN"
            className="w-24 h-24 sm:w-32 sm:h-32 mb-8 sm:mb-12 opacity-90"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 0.9 }}
            transition={{ delay: 0.3, duration: 0.8 }}
            data-testid="auren-logo"
          />
          
          <motion.h1 
            className="font-serif text-4xl sm:text-5xl lg:text-6xl text-white mb-6 sm:mb-8 tracking-tight leading-none text-shadow-gold"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.8 }}
            data-testid="main-question"
            key={`question-${language}`}
          >
            {t.mainQuestion}
          </motion.h1>
          
          <motion.p 
            className="font-sans font-light text-base md:text-lg text-white/70 mb-12 sm:mb-16 max-w-md leading-relaxed"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7, duration: 0.8 }}
            data-testid="daily-reflection"
            key={`reflection-${language}`}
          >
            {dailyReflection[language] || dailyReflection.en}
          </motion.p>
          
          <motion.button
            onClick={handleStart}
            className="bg-[#D4AF37] text-black hover:bg-[#C29B2E] rounded-full px-10 py-4 sm:px-12 sm:py-5 text-sm sm:text-base font-semibold tracking-wide flex items-center gap-3 transition-all duration-500 hover:-translate-y-1"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.9, duration: 0.6 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.98 }}
            data-testid="begin-button"
            key={`button-${language}`}
          >
            <Sparkles size={18} />
            {t.beginButton}
          </motion.button>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-black overflow-hidden" data-testid="chat-container">
      {/* Language Switcher in Chat */}
      <motion.div 
        className="absolute top-4 right-4 sm:top-6 sm:right-6 z-20"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className="flex items-center gap-2 text-xs font-light">
          <button
            onClick={() => setLanguage('en')}
            className={`transition-colors duration-300 ${
              language === 'en' 
                ? 'text-[#D4AF37] font-medium' 
                : 'text-white/50 hover:text-white/80'
            }`}
            data-testid="chat-lang-switch-en"
          >
            EN
          </button>
          <span className="text-white/30">|</span>
          <button
            onClick={() => setLanguage('fr')}
            className={`transition-colors duration-300 ${
              language === 'fr' 
                ? 'text-[#D4AF37] font-medium' 
                : 'text-white/50 hover:text-white/80'
            }`}
            data-testid="chat-lang-switch-fr"
          >
            FR
          </button>
        </div>
      </motion.div>

      <motion.div 
        className="flex-1 overflow-y-auto px-4 sm:px-8 py-8 sm:py-12 space-y-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        <div className="max-w-3xl mx-auto space-y-8">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-center gap-3 mb-12"
          >
            <img
              src="https://static.prod-images.emergentagent.com/jobs/a2025be9-9ee4-476a-919c-46e92129890e/images/5919e22cd369047abe23906169ab5aea282959e86819b16d96cee17d758446ad.png"
              alt="AUREN"
              className="w-10 h-10 opacity-80"
              data-testid="chat-logo"
            />
            <span className="font-serif text-xl text-[#D4AF37] tracking-wider">AUREN</span>
          </motion.div>

          <AnimatePresence mode="popLayout">
            {messages.map((msg, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                data-testid={msg.role === 'user' ? 'user-message' : 'ai-message'}
              >
                <div className={`
                  ${msg.role === 'ai' 
                    ? 'bg-transparent border border-[#D4AF37]/20 rounded-2xl p-6 md:p-8 text-white text-lg font-light leading-relaxed max-w-[85%] md:max-w-[70%] border-glow' 
                    : 'bg-[#111111] text-white border border-white/10 rounded-2xl p-6 md:p-8 max-w-[85%] md:max-w-[70%]'
                  }
                `}>
                  {msg.content}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
              data-testid="loading-indicator"
            >
              <div className="bg-transparent border border-[#D4AF37]/20 rounded-2xl p-6 md:p-8 max-w-[85%] md:max-w-[70%]">
                <div className="flex gap-2">
                  <motion.div
                    className="w-2 h-2 bg-[#D4AF37] rounded-full"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1.5, repeat: Infinity, delay: 0 }}
                  />
                  <motion.div
                    className="w-2 h-2 bg-[#D4AF37] rounded-full"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
                  />
                  <motion.div
                    className="w-2 h-2 bg-[#D4AF37] rounded-full"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
                  />
                </div>
              </div>
            </motion.div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </motion.div>

      <motion.div 
        className="glass-effect border-t border-[#D4AF37]/20 p-4 md:p-8"
        initial={{ y: 100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <form onSubmit={handleSendMessage} className="max-w-3xl mx-auto">
          <div className="flex gap-3 sm:gap-4 items-center">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={t.chatPlaceholder}
              className="flex-1 bg-transparent border-none text-white placeholder-white/30 focus:outline-none focus:ring-0 text-lg md:text-xl font-light"
              disabled={isLoading}
              data-testid="chat-input"
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              className="bg-[#D4AF37] text-black hover:bg-[#C29B2E] disabled:opacity-30 disabled:cursor-not-allowed rounded-full p-3 sm:p-4 transition-all duration-300 hover:-translate-y-1 flex items-center justify-center"
              data-testid="send-button"
            >
              <Send size={20} />
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

export default App;