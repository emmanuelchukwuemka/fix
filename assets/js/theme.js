// Theme toggle functionality
function initTheme() {
  const themeToggle = document.getElementById('themeToggle');
  const icon = themeToggle.querySelector('i');
  
  // Check for saved theme or default to light mode
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
    document.body.classList.add('dark-mode');
    icon.classList.remove('fa-moon');
    icon.classList.add('fa-sun');
  } else {
    document.body.classList.remove('dark-mode');
    icon.classList.remove('fa-sun');
    icon.classList.add('fa-moon');
  }
}

function toggleTheme() {
  const themeToggle = document.getElementById('themeToggle');
  const icon = themeToggle.querySelector('i');
  
  document.body.classList.toggle('dark-mode');
  
  if (document.body.classList.contains('dark-mode')) {
    localStorage.setItem('theme', 'dark');
    icon.classList.remove('fa-moon');
    icon.classList.add('fa-sun');
  } else {
    localStorage.setItem('theme', 'light');
    icon.classList.remove('fa-sun');
    icon.classList.add('fa-moon');
  }
}

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', initTheme);

// Add event listener to theme toggle button
document.getElementById('themeToggle').addEventListener('click', toggleTheme);