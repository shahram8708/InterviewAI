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

  const micBtn = document.getElementById('mic-btn');
  const transcriptArea = document.getElementById('transcript-area');
  const subtitlesElem = document.getElementById('subtitles');
  const confidenceFill = document.getElementById('confidence-fill');
  const timerDisplay = document.getElementById('timer-display');
  const textInputArea = document.getElementById('text-input-area');
  const textInput = document.getElementById('text-input');
  const textSubmitBtn = document.getElementById('text-submit-btn');

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
      fallbackToText();
    };

    recognition.onend = () => {
      if (isListening) {
        recognition.start(); // Restart if unexpectedly ended
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

  // Setup Voice Synthesis
  function speakText(text) {
    return new Promise((resolve) => {
      if (!('speechSynthesis' in window)) {
        resolve();
        return;
      }
      const utterance = new SpeechSynthesisUtterance(text);
      
      // Voice configuration based on persona
      if (persona === 'friendly') {
        utterance.rate = 0.9;
        utterance.pitch = 1.1;
      } else if (persona === 'strict') {
        utterance.rate = 1.0;
        utterance.pitch = 0.9;
      } else {
        utterance.rate = 1.1;
      }
      
      utterance.onend = () => resolve();
      window.speechSynthesis.speak(utterance);
    });
  }

  // Interview Flow
  async function startInterview() {
    startTimer();
    updateStage('Introduction');
    try {
      const response = await apiFetch(`/api/interview/${interviewId}/next-question`);
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
    } catch(e) {} // Ignore if already started
  }

  async function stopListeningAndSubmit() {
    isListening = false;
    clearTimeout(silenceTimer);
    if (recognition) recognition.stop();
    
    let answer = finalTranscript;
    if (!answer) {
       answer = subtitlesElem.textContent;
    }
    
    if (!answer.trim()) {
      showMicState('idle');
      return;
    }

    showMicState('processing');
    showSubtitles('');
    updateTranscript('candidate', answer);
    
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
    updateTranscript('interviewer', data.response);
    updateConfidenceMeter(data.confidence || 50);
    
    await speakText(data.response);
    
    if (data.is_complete) {
      endInterview();
    } else {
      currentTurn++;
      updateTurnCounter();
      showMicState('idle');
    }
  }

  function endInterview() {
    clearInterval(timerInterval);
    updateTranscript('interviewer', 'The interview is now complete. Generating report...');
    setTimeout(() => {
      window.location.href = `/interview/${interviewId}/report`;
    }, 2000);
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
    bubble.className = `transcript-bubble ${role} fade-in`;
    bubble.textContent = text;
    transcriptArea.appendChild(bubble);
    transcriptArea.scrollTop = transcriptArea.scrollHeight;
  }

  function updateConfidenceMeter(val) {
    if (confidenceFill) confidenceFill.style.width = `${val}%`;
  }

  function updateStage(stageName) {
    const stageEl = document.getElementById('current-stage');
    if (stageEl) stageEl.textContent = stageName;
  }

  function updateTurnCounter() {
    const turnEl = document.getElementById('turn-counter');
    if (turnEl) turnEl.textContent = `${currentTurn}/${totalTurns}`;
  }

  function showMicState(state) {
    if (!micBtn) return;
    micBtn.className = `mic-button ${state}`;
    if (state === 'idle') {
      micBtn.innerHTML = '<i class="fas fa-microphone"></i>';
      micBtn.disabled = false;
    } else if (state === 'listening') {
      micBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
      micBtn.disabled = false;
    } else {
      micBtn.innerHTML = '<i class="fas fa-spinner"></i>';
      micBtn.disabled = true;
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
    if (textInputArea) textInputArea.style.display = 'block';
    
    if (textSubmitBtn && textInput) {
      textSubmitBtn.onclick = async () => {
        const val = textInput.value;
        if (val.trim()) {
          textInput.value = '';
          updateTranscript('candidate', val);
          if (textInputArea) textInputArea.style.display = 'none';
          await submitAnswer(val);
          if (textInputArea) textInputArea.style.display = 'block';
        }
      };
      
      textInput.onkeypress = (e) => {
        if (e.key === 'Enter') textSubmitBtn.click();
      };
    }
  }

  // Start initialization
  startInterview();
});
