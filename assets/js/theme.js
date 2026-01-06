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

// Sidebar user info synchronization
function updateSidebar() {
  // Use setTimeout to ensure DOM is fully loaded
  setTimeout(() => {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;

    const savedName = localStorage.getItem('userName');
    const savedEmail = localStorage.getItem('userEmail');
    const savedAvatar = localStorage.getItem('userAvatar');

    // Support both user dashboard IDs and generic admin selectors
    const nameEl = document.getElementById('sidebarUserName') || document.getElementById('adminName') || sidebar.querySelector('.font-semibold');
    const emailEl = document.getElementById('sidebarUserEmail') || document.getElementById('adminEmail') || sidebar.querySelector('.text-gray-600') || sidebar.querySelector('.dark\\:text-gray-400');
    const avatarEl = document.getElementById('sidebarAvatar') || document.getElementById('adminAvatar') || sidebar.querySelector('img[alt="User"]');

    if (savedName && nameEl) {
      nameEl.textContent = savedName;
      // Also update other common header elements if they exist
      const headerName = document.getElementById('headerUserName');
      if (headerName) headerName.textContent = savedName.split(' ')[0] + '!';
      const welcomeName = document.getElementById('welcomeUserName');
      if (welcomeName) welcomeName.textContent = savedName.split(' ')[0];
    } else if (nameEl) {
      nameEl.textContent = 'Guest';
    }

    if (savedEmail && emailEl) {
      emailEl.textContent = savedEmail;
    } else if (emailEl) {
      emailEl.textContent = 'guest@example.com';
    }

    if (avatarEl) {
      if (savedAvatar) {
        avatarEl.src = savedAvatar;
      } else if (savedName && !avatarEl.src.includes('logo.png')) {
        avatarEl.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${savedName}`;
      }
    }
  }, 100);
}

// Global profile synchronization
function syncUserProfile() {
  const token = localStorage.getItem('access_token');
  if (!token) return;

  fetch('/api/auth/profile', {
    headers: { 'Authorization': 'Bearer ' + token }
  })
    .then(response => {
      if (response.status === 401) return; // Silent fail for auth issues here
      return response.json();
    })
    .then(data => {
      if (data && data.user) {
        localStorage.setItem('userName', data.user.full_name);
        localStorage.setItem('userEmail', data.user.email);
        if (data.user.avatar_url) {
          localStorage.setItem('userAvatar', data.user.avatar_url);
        }
        updateSidebar();
      }
    })
    .catch(err => console.debug('Profile sync skipped:', err));
}

// Initialize theme and sidebar on page load
document.addEventListener('DOMContentLoaded', function () {
  initTheme();
  updateSidebar();
  syncUserProfile(); // Proactively sync on every page load

  // Add event listeners to theme toggle buttons
  const themeToggles = document.querySelectorAll('#themeToggle, #themeToggleMobile');
  themeToggles.forEach(toggle => {
    if (toggle) {
      toggle.addEventListener('click', toggleTheme);
    }
  });
});

// Also initialize on load
window.addEventListener('load', function () {
  initTheme();
  updateSidebar();
});

// Listen for storage changes to update sidebar when user logs in/out on another tab
window.addEventListener('storage', function (e) {
  if (['userName', 'userEmail', 'userAvatar', 'access_token'].includes(e.key)) {
    updateSidebar();
  }
});
