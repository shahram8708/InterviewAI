document.addEventListener('DOMContentLoaded', () => {
  const uploadZone = document.getElementById('upload-zone');
  const fileInput = document.getElementById('resume-file');
  const uploadForm = document.getElementById('upload-form');
  const analyzingState = document.getElementById('analyzing-state');

  if (uploadZone && fileInput) {
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      uploadZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
      e.preventDefault();
      e.stopPropagation();
    }

    // Highlight drop zone
    ['dragenter', 'dragover'].forEach(eventName => {
      uploadZone.addEventListener(eventName, () => uploadZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      uploadZone.addEventListener(eventName, () => uploadZone.classList.remove('dragover'), false);
    });

    // Handle dropped files
    uploadZone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      handleFiles(files);
    });

    uploadZone.addEventListener('click', () => {
      fileInput.click();
    });

    fileInput.addEventListener('change', function() {
      handleFiles(this.files);
    });

    function handleFiles(files) {
      if (files.length === 0) return;
      const file = files[0];
      
      // Validate PDF
      if (file.type !== 'application/pdf') {
        alert('Please upload a PDF file.');
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        alert('File size exceeds 5MB limit.');
        return;
      }
      
      // Assign file to input if dropped
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      fileInput.files = dataTransfer.files;
      
      // Simulate submission & analysis state
      uploadZone.style.display = 'none';
      if (analyzingState) analyzingState.style.display = 'block';
      
      if (uploadForm) {
        uploadForm.submit();
      }
    }
  }

  // Profile Edit Toggle
  const editBtn = document.getElementById('edit-profile-btn');
  const profileForm = document.getElementById('profile-form');
  const profileDisplay = document.getElementById('profile-display');
  
  if (editBtn && profileForm && profileDisplay) {
    editBtn.addEventListener('click', () => {
      profileDisplay.style.display = 'none';
      profileForm.style.display = 'block';
    });
    
    const cancelBtn = document.getElementById('cancel-edit-btn');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        profileForm.style.display = 'none';
        profileDisplay.style.display = 'block';
      });
    }
  }
});
