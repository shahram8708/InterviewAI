document.addEventListener('DOMContentLoaded', () => {
  const interviewDataElem = document.getElementById('interview-data');
  if (!interviewDataElem) return;

  const sessionData = JSON.parse(interviewDataElem.textContent);
  const interviewId = sessionData.id;
  const persona = sessionData.persona || 'friendly';

  let recognition;
  let isListening = false;
  let finalTranscript = '';
  let silenceTimer;
  const SILENCE_TIMEOUT = 3000;
  
  let timerInterval;
  let secondsElapsed = 0;
  
  let currentTurn = 1;
  const totalTurns = sessionData.total_questions || 5;

  const micBtn = document.getElementById('micBtn');
  const transcriptArea = document.getElementById('transcriptArea');
  const subtitlesElem = document.getElementById('micStatus');
  const confidenceFill = document.getElementById('confidenceMeter');
  const timerDisplay = document.getElementById('timer');
  const textInputArea = document.getElementById('textControls');
  const textInput = document.getElementById('textInput');
  const textSubmitBtn = document.getElementById('sendTextBtn');
  const stopAnsweringBtn = document.getElementById('stopAnsweringBtn');
  const switchToVoiceBtn = document.getElementById('switchToVoiceBtn');
  const confirmEndBtn = document.getElementById('confirmEndBtn');

  if (stopAnsweringBtn) {
    stopAnsweringBtn.onclick = stopListeningAndSubmit;
  }
  if (confirmEndBtn) {
    confirmEndBtn.onclick = () => endInterview();
  }
  if (switchToVoiceBtn) {
    switchToVoiceBtn.onclick = () => {
      if (textInputArea) textInputArea.classList.add('d-none');
      if (micBtn) micBtn.style.display = 'flex';
      showMicState('idle');
    };
  }

  // Initialize Speech Recognition
  if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      isListening = true;
      showMicState('listening');
      finalTranscript = '';
      resetSilenceTimer();
    };

    recognition.onresult = (event) => {
      if (!isListening) {
         isListening = true;
         showMicState('listening');
      }
      resetSilenceTimer();
      let interimTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }
      showSubtitles(finalTranscript + interimTranscript);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error', event.error);
      isListening = false;
      showMicState('idle');
    };

    recognition.onend = () => {
      if (isListening) {
        try { recognition.start(); } catch(e) {}
      } else {
        showMicState('idle');
      }
    };
  } else {
    fallbackToText();
  }

  function resetSilenceTimer() {
    clearTimeout(silenceTimer);
    if (isListening) {
      silenceTimer = setTimeout(() => {
        stopListeningAndSubmit();
      }, SILENCE_TIMEOUT);
    }
  }

  // Setup Voice Synthesis with Failsafe for Chrome bug
  let globalUtterance = null;
  function speakText(text) {
    return new Promise((resolve) => {
      if (!('speechSynthesis' in window)) {
        resolve();
        return;
      }
      
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      globalUtterance = utterance; // Prevent garbage collection
      
      if (persona === 'friendly') {
        utterance.rate = 0.9;
        utterance.pitch = 1.1;
      } else if (persona === 'strict') {
        utterance.rate = 1.0;
        utterance.pitch = 0.9;
      } else {
        utterance.rate = 1.1;
      }
      
      utterance.onend = () => {
        globalUtterance = null;
        resolve();
      };
      
      utterance.onerror = () => {
        globalUtterance = null;
        resolve();
      };
      
      window.speechSynthesis.speak(utterance);
      
      // Failsafe in case onend never fires (common Chrome bug for long text)
      setTimeout(() => {
        if (globalUtterance === utterance) {
          globalUtterance = null;
          resolve();
        }
      }, Math.max(text.length * 100, 3000));
    });
  }

  // Interview Flow
  async function startInterview() {
    startTimer();
    updateStage('Introduction');
    try {
      const response = await apiFetch(`/api/interview/${interviewId}/next-question`, { method: 'POST' });
      updateTranscript('interviewer', response.question);
      await speakText(response.question);
      enableMic();
    } catch (e) {
      updateTranscript('interviewer', 'Error starting interview. Please refresh.');
    }
  }

  function toggleListening() {
    if (isListening) {
      stopListeningAndSubmit();
    } else {
      startListening();
    }
  }

  function startListening() {
    if (!recognition) return;
    try {
      recognition.start();
    } catch(e) {} 
  }

  async function stopListeningAndSubmit() {
    if (!isListening && !finalTranscript && !subtitlesElem?.textContent) return;
    
    isListening = false;
    clearTimeout(silenceTimer);
    try { if (recognition) recognition.stop(); } catch(e) {}
    
    let answer = finalTranscript;
    if (!answer) {
       answer = subtitlesElem ? subtitlesElem.textContent : '';
    }
    
    // Clean up fallback text
    if (answer.includes('Click mic when ready') || answer.includes('Listening...') || answer.includes('Processing...')) {
        answer = '';
    }
    
    if (!answer.trim()) {
      showMicState('idle');
      return;
    }

    showMicState('processing');
    showSubtitles('');
    updateTranscript('candidate', answer);
    finalTranscript = '';
    
    await submitAnswer(answer);
  }

  async function submitAnswer(answer) {
    try {
      const data = await apiFetch(`/api/interview/${interviewId}/submit-answer`, {
        method: 'POST',
        body: JSON.stringify({ answer })
      });
      handleResponse(data);
    } catch (e) {
      updateTranscript('interviewer', 'Sorry, I missed that. Could you repeat?');
      showMicState('idle');
    }
  }

  async function handleResponse(data) {
    const aiText = data.ai_response || data.response || 'Acknowledged.';
    updateTranscript('interviewer', aiText);
    updateConfidenceMeter(data.confidence || 50);
    
    await speakText(aiText);
    
    if (data.should_continue === false) {
      endInterview();
    } else {
      currentTurn++;
      updateTurnCounter();
      showMicState('processing');
      try {
        const response = await apiFetch(`/api/interview/${interviewId}/next-question`, { method: 'POST' });
        updateTranscript('interviewer', response.question);
        updateStage(response.stage || 'Questioning');
        await speakText(response.question);
        showMicState('idle');
      } catch (e) {
        updateTranscript('interviewer', 'Error fetching next question. Please try again.');
        showMicState('idle');
      }
    }
  }

  async function endInterview() {
    clearInterval(timerInterval);
    updateTranscript('interviewer', 'The interview is now complete. Generating report...');
    try {
      const result = await apiFetch(`/api/interview/${interviewId}/end`, { method: 'POST' });
      if (result.report_url) {
        window.location.href = result.report_url;
      }
    } catch (e) {
      updateTranscript('interviewer', 'Error generating report. Please refresh.');
    }
  }

  // UI Updates
  function updateTimer() {
    secondsElapsed++;
    const m = Math.floor(secondsElapsed / 60).toString().padStart(2, '0');
    const s = (secondsElapsed % 60).toString().padStart(2, '0');
    if (timerDisplay) timerDisplay.textContent = `${m}:${s}`;
  }

  function startTimer() {
    timerInterval = setInterval(updateTimer, 1000);
  }

  function updateTranscript(role, text) {
    if (!transcriptArea) return;
    const bubble = document.createElement('div');
    // FIXED: Use text-body instead of text-light so the text is visible regardless of the theme background
    bubble.className = `transcript-bubble ${role} fade-in mb-3 p-3 rounded text-body ${role === 'interviewer' ? 'bg-secondary bg-opacity-25 ms-2 me-5 border border-secondary' : 'bg-primary bg-opacity-25 text-end ms-5 me-2 border border-primary'}`;
    bubble.textContent = text;
    transcriptArea.appendChild(bubble);
    transcriptArea.scrollTop = transcriptArea.scrollHeight;
  }

  function updateConfidenceMeter(val) {
    if (confidenceFill) confidenceFill.style.width = `${val}%`;
  }

  function updateStage(stageName) {
    const stageEl = document.getElementById('stageLabel');
    if (stageEl) stageEl.textContent = stageName;
  }

  function updateTurnCounter() {
    const turnEl = document.getElementById('progressText');
    if (turnEl) turnEl.textContent = `Question ${currentTurn} of ~${totalTurns}`;
    const progressBar = document.getElementById('progressBar');
    if (progressBar) progressBar.style.width = `${(currentTurn / totalTurns) * 100}%`;
  }

  function showMicState(state) {
    if (stopAnsweringBtn) stopAnsweringBtn.disabled = (state !== 'listening');
    
    if (!micBtn) return;
    micBtn.className = `btn btn-lg rounded-circle shadow-lg position-relative d-flex align-items-center justify-content-center border border-secondary transition-all ${state === 'listening' ? 'bg-danger text-white pulse-red' : 'bg-card-bg text-body'}`;
    
    const icon = document.getElementById('micIcon');
    if (!icon) return;
    
    if (state === 'idle') {
      icon.className = 'bi bi-mic-fill fs-3';
      micBtn.disabled = false;
      showSubtitles('Click mic when ready to speak');
    } else if (state === 'listening') {
      icon.className = 'bi bi-mic-fill fs-3';
      micBtn.disabled = false;
      showSubtitles('Listening...');
    } else {
      icon.className = 'bi bi-hourglass-split fs-3';
      micBtn.disabled = true;
      showSubtitles('Processing...');
    }
  }

  function showSubtitles(text) {
    if (subtitlesElem) subtitlesElem.textContent = text;
  }

  function enableMic() {
    showMicState('idle');
    if (micBtn) {
      micBtn.onclick = toggleListening;
    }
  }

  function fallbackToText() {
    if (micBtn) micBtn.style.display = 'none';
    if (textInputArea) textInputArea.classList.remove('d-none');
    
    if (textSubmitBtn && textInput) {
      textSubmitBtn.onclick = async () => {
        const val = textInput.value;
        if (val.trim()) {
          textInput.value = '';
          updateTranscript('candidate', val);
          if (textInputArea) textInputArea.classList.add('d-none');
          showSubtitles('Processing text...');
          await submitAnswer(val);
          if (textInputArea) textInputArea.classList.remove('d-none');
          showSubtitles('Type your next answer.');
        }
      };
      
      textInput.onkeypress = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            textSubmitBtn.click();
        }
      };
    }
  }

  // Start initialization
  startInterview();
});
