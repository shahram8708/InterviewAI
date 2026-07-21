document.addEventListener('DOMContentLoaded', () => {
  // PWA Install Prompt
  let deferredPrompt;
  const installBtn = document.getElementById('install-pwa-btn');

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    if (installBtn) {
      installBtn.style.display = 'block';
      installBtn.addEventListener('click', () => {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
          if (choiceResult.outcome === 'accepted') {
            console.log('User accepted the install prompt');
          }
          deferredPrompt = null;
          installBtn.style.display = 'none';
        });
      });
    }
  });

  // iOS Detection for PWA
  const isIos = () => {
    const userAgent = window.navigator.userAgent.toLowerCase();
    return /iphone|ipad|ipod/.test(userAgent);
  };
  const isInStandaloneMode = () => ('standalone' in window.navigator) && (window.navigator.standalone);
  if (isIos() && !isInStandaloneMode()) {
    const iosPrompt = document.getElementById('ios-pwa-prompt');
    if (iosPrompt) iosPrompt.style.display = 'block';
  }

  // Theme Toggle
  const themeToggle = document.getElementById('theme-toggle');
  const themeSelectors = document.querySelectorAll('.theme-selector');
  const themeMeta = document.querySelector('meta[name="theme-color"]');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');

  const resolveTheme = (themePreference) => {
    if (themePreference === 'system') {
      return prefersDark.matches ? 'dark' : 'light';
    }
    return themePreference === 'light' ? 'light' : 'dark';
  };

  const applyTheme = (themePreference) => {
    const resolvedTheme = resolveTheme(themePreference);
    document.documentElement.setAttribute('data-bs-theme', resolvedTheme);
    if (document.body) {
      document.body.setAttribute('data-bs-theme', resolvedTheme);
    }

    document.querySelectorAll('.modal[data-bs-theme]').forEach((modal) => {
      modal.setAttribute('data-bs-theme', resolvedTheme);
    });

    if (themeMeta) {
      themeMeta.setAttribute('content', resolvedTheme === 'dark' ? '#0A1628' : '#F8FAFC');
    }

    if (themeToggle) {
      const icon = themeToggle.querySelector('i');
      if (icon) {
        icon.className = resolvedTheme === 'dark' ? 'bi bi-moon-stars' : 'bi bi-sun';
      }
    }

    themeSelectors.forEach((selector) => {
      selector.checked = selector.value === themePreference;
    });
  };

  let storedTheme = localStorage.getItem('theme') || 'dark';
  applyTheme(storedTheme);

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-bs-theme');
      storedTheme = currentTheme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('theme', storedTheme);
      applyTheme(storedTheme);
    });
  }

  themeSelectors.forEach((selector) => {
    selector.addEventListener('change', () => {
      if (!selector.checked) return;
      storedTheme = selector.value;
      localStorage.setItem('theme', storedTheme);
      applyTheme(storedTheme);
    });
  });

  if (typeof prefersDark.addEventListener === 'function') {
    prefersDark.addEventListener('change', () => {
      const activeTheme = localStorage.getItem('theme') || storedTheme;
      if (activeTheme === 'system') {
        applyTheme('system');
      }
    });
  }

  // High Contrast Toggle
  const hcToggle = document.getElementById('high-contrast-toggle') || document.getElementById('contrast-toggle');
  if (hcToggle) {
    hcToggle.addEventListener('click', () => {
      const isHc = document.documentElement.getAttribute('data-high-contrast') === 'true';
      document.documentElement.setAttribute('data-high-contrast', !isHc);
    });
  }

  // Reduced Motion Detection
  const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (mediaQuery.matches) {
    document.documentElement.setAttribute('data-reduced-motion', 'true');
  }

  // Flash Message Auto-dismiss
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });

  // Form Validation
  const forms = document.querySelectorAll('.needs-validation');
  Array.from(forms).forEach(form => {
    form.addEventListener('submit', event => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add('was-validated');
    }, false);
  });

  // Service Worker Registration
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/sw.js')
        .then(registration => console.log('SW registered:', registration))
        .catch(error => console.log('SW registration failed:', error));
    });
  }

  // Show/Hide Password
  const pwdToggles = document.querySelectorAll('.toggle-password');
  pwdToggles.forEach(toggle => {
    toggle.addEventListener('click', function() {
      const input = document.querySelector(this.getAttribute('data-target'));
      if (input.type === 'password') {
        input.type = 'text';
        this.classList.replace('fa-eye', 'fa-eye-slash');
      } else {
        input.type = 'password';
        this.classList.replace('fa-eye-slash', 'fa-eye');
      }
    });
  });

  // Global Keyboard Shortcuts
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const modals = document.querySelectorAll('.modal.show');
      modals.forEach(modal => {
        const bsModal = bootstrap.Modal.getInstance(modal);
        if (bsModal) bsModal.hide();
      });
    }
  });

  // Smooth Scroll
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      document.querySelector(this.getAttribute('href')).scrollIntoView({
        behavior: 'smooth'
      });
    });
  });
});

// CSRF Token Helper
function getCSRFToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

// Fetch Wrapper
async function apiFetch(url, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCSRFToken(),
    ...options.headers
  };
  
  try {
    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API Fetch Error:', error);
    throw error;
  }
}
