document.addEventListener('DOMContentLoaded', () => {
  // Score trend charts. Data comes from the server as real completed-interview
  // scores serialised onto the canvas; nothing is drawn when there is no data.
  document.querySelectorAll('canvas.score-chart').forEach((canvas) => {
    let points = [];
    try {
      points = JSON.parse(canvas.dataset.scores || '[]');
    } catch (error) {
      return;
    }
    if (!Array.isArray(points) || points.length === 0) {
      return;
    }

    const styles = getComputedStyle(document.documentElement);
    const accent = styles.getPropertyValue('--color-accent').trim() || '#4FC0D0';
    const primary = styles.getPropertyValue('--color-primary').trim() || '#1B6B93';
    const labelColor = styles.getPropertyValue('--color-text-secondary').trim() || '#94A3B8';

    const render = () => {
      // Match the backing store to the element's rendered size for a crisp chart.
      const ratio = window.devicePixelRatio || 1;
      const cssWidth = canvas.clientWidth;
      const cssHeight = canvas.clientHeight || 220;
      canvas.width = cssWidth * ratio;
      canvas.height = cssHeight * ratio;

      const ctx = canvas.getContext('2d');
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      ctx.clearRect(0, 0, cssWidth, cssHeight);

      const paddingTop = 20;
      const paddingBottom = 28;
      const plotHeight = cssHeight - paddingTop - paddingBottom;
      const maxScore = 100;
      const slotWidth = cssWidth / points.length;
      const barWidth = Math.max(6, Math.min(48, slotWidth - 12));

      ctx.font = '12px sans-serif';
      ctx.textAlign = 'center';

      points.forEach((point, index) => {
        const score = Math.max(0, Math.min(maxScore, Number(point.score) || 0));
        const barHeight = (score / maxScore) * plotHeight;
        const x = index * slotWidth + (slotWidth - barWidth) / 2;
        const y = paddingTop + plotHeight - barHeight;

        const gradient = ctx.createLinearGradient(0, y, 0, paddingTop + plotHeight);
        gradient.addColorStop(0, accent);
        gradient.addColorStop(1, primary);
        ctx.fillStyle = gradient;
        ctx.fillRect(x, y, barWidth, barHeight);

        ctx.fillStyle = labelColor;
        ctx.fillText(String(Math.round(score)), x + barWidth / 2, y - 6);
        if (point.date && slotWidth > 34) {
          ctx.fillText(point.date, x + barWidth / 2, cssHeight - 8);
        }
      });
    };

    render();

    let resizeTimer;
    window.addEventListener('resize', () => {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(render, 150);
    });
  });

  // Badge tooltips
  if (window.bootstrap && window.bootstrap.Tooltip) {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
      window.bootstrap.Tooltip.getOrCreateInstance(el);
    });
  }
});
