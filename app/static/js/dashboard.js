document.addEventListener('DOMContentLoaded', () => {
  // Simple Bar Chart for scores
  const canvas = document.getElementById('scoreChart');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    // Mock data for scores
    const scores = [65, 70, 78, 85, 82, 90, 88];
    const width = canvas.width;
    const height = canvas.height;
    
    const barWidth = width / scores.length - 10;
    const maxScore = 100;
    
    ctx.clearRect(0, 0, width, height);
    
    scores.forEach((score, index) => {
      const barHeight = (score / maxScore) * height;
      const x = index * (barWidth + 10) + 5;
      const y = height - barHeight;
      
      // Gradient
      const gradient = ctx.createLinearGradient(0, y, 0, height);
      gradient.addColorStop(0, '#4FC0D0');
      gradient.addColorStop(1, '#1B6B93');
      
      ctx.fillStyle = gradient;
      ctx.fillRect(x, y, barWidth, barHeight);
      
      // Label
      ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--color-text-secondary');
      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(score.toString(), x + barWidth / 2, y - 5);
    });
  }

  // Animate Stat Numbers
  const stats = document.querySelectorAll('.stat-number');
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const target = entry.target;
        const endValue = parseInt(target.getAttribute('data-value'), 10) || 0;
        let startValue = 0;
        const duration = 1500;
        const step = endValue / (duration / 16);
        
        function updateCounter() {
          startValue += step;
          if (startValue < endValue) {
            target.textContent = Math.floor(startValue);
            requestAnimationFrame(updateCounter);
          } else {
            target.textContent = endValue;
          }
        }
        
        updateCounter();
        observer.unobserve(target);
      }
    });
  }, { threshold: 0.5 });
  
  stats.forEach(stat => observer.observe(stat));
});
