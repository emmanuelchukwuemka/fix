// Theme toggle functionality
function initTheme() {
  const themeToggles = document.querySelectorAll('#themeToggle, #themeToggleMobile');
  
  // Check for saved theme or default to light mode
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
    document.body.classList.add('dark-mode');
    themeToggles.forEach(toggle => {
      const icon = toggle ? toggle.querySelector('i') : null;
      if (icon) {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
      }
    });
  } else {
    document.body.classList.remove('dark-mode');
    themeToggles.forEach(toggle => {
      const icon = toggle ? toggle.querySelector('i') : null;
      if (icon) {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
      }
    });
  }
  
  // Make sure the buttons are visible and properly sized
  themeToggles.forEach(toggle => {
    if (toggle) {
      toggle.classList.add('theme-toggle-visible');
    }
  });
}

function toggleTheme() {
  const themeToggles = document.querySelectorAll('#themeToggle, #themeToggleMobile');
  
  document.body.classList.toggle('dark-mode');
  
  if (document.body.classList.contains('dark-mode')) {
    localStorage.setItem('theme', 'dark');
    themeToggles.forEach(toggle => {
      const icon = toggle ? toggle.querySelector('i') : null;
      if (icon) {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
      }
    });
  } else {
    localStorage.setItem('theme', 'light');
    themeToggles.forEach(toggle => {
      const icon = toggle ? toggle.querySelector('i') : null;
      if (icon) {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
      }
    });
  }
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', function() {
  initTheme();
  
  // Add event listeners to theme toggle buttons
  const themeToggles = document.querySelectorAll('#themeToggle, #themeToggleMobile');
  themeToggles.forEach(toggle => {
    if (toggle) {
      toggle.addEventListener('click', toggleTheme);
    }
  });
});

// Also initialize theme when the page is loaded (for SPA-like behavior)
window.addEventListener('load', initTheme);