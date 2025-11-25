// Basic form handlers for Sign In and Sign Up

document.addEventListener("DOMContentLoaded", function () {
  const signInForm = document.getElementById("signInForm");
  if (signInForm) {
    signInForm.addEventListener("submit", function (e) {
      e.preventDefault();
      // Simulate sign in
      alert("Sign In successful (demo)");
      // Redirect to dashboard page
      window.location.href = "dashboard.html";
    });
  }

  const signUpForm = document.getElementById("signUpForm");
  if (signUpForm) {
    signUpForm.addEventListener("submit", function (e) {
      e.preventDefault();
      // Simulate sign up
      alert("Account created successfully (demo)");
      // Redirect to Sign In page
      window.location.href = "index.html";
    });
  }
});
