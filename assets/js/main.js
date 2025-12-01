// Basic form handlers for Sign In and Sign Up

document.addEventListener("DOMContentLoaded", function () {
  const signInForm = document.getElementById("signInForm");
  if (signInForm) {
    signInForm.addEventListener("submit", function (e) {
      e.preventDefault();
      // Get form values
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;
      
      // Simple validation
      if (!email || !password) {
        alert("Please fill in all fields");
        return;
      }
      
      // Send login request to backend
      fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password })
      })
      .then(response => response.json())
      .then(data => {
        if (data.access_token) {
          localStorage.setItem("access_token", data.access_token);
          // Store user data
          if (data.user) {
            localStorage.setItem('userName', data.user.full_name);
            localStorage.setItem('userEmail', data.user.email);
          }
          // Redirect to dashboard page
          window.location.href = "dashboard.html";
        } else {
          alert("Login failed: " + (data.message || "Invalid credentials"));
        }
      })
      .catch(error => {
        console.error("Error:", error);
        alert("Login failed. Please try again.");
      });
    });
  }

  const signUpForm = document.getElementById("signUpForm");
  if (signUpForm) {
    signUpForm.addEventListener("submit", function (e) {
      e.preventDefault();
      // Get form values
      const fullName = document.getElementById("full_name").value;
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;
      
      // Simple validation
      if (!fullName || !email || !password) {
        alert("Please fill in all required fields");
        return;
      }
      
      if (password.length < 8) {
        alert("Password must be at least 8 characters long");
        return;
      }
      
      // Prepare data for backend
      const data = {
        full_name: fullName,
        email: email,
        password: password,
        role: "user" // Default role
      };
      
      // Send signup request to backend
      fetch("/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      })
      .then(response => response.json())
      .then(data => {
        if (data.access_token) {
          localStorage.setItem("access_token", data.access_token);
          // Store user data
          if (data.user) {
            localStorage.setItem('userName', data.user.full_name);
            localStorage.setItem('userEmail', data.user.email);
          }
          alert("Account created successfully");
          // Redirect to dashboard page
          window.location.href = "dashboard.html";
        } else {
          alert("Registration failed: " + (data.message || "Please try again"));
        }
      })
      .catch(error => {
        console.error("Error:", error);
        alert("Registration failed. Please try again.");
      });
    });
  }
});
