// public/JS/login.js 

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("login-form");

  if (form) {
    form.addEventListener("submit", (e) => {
      const email = document.getElementById("email").value.trim();
      const password = document.getElementById("password").value.trim();

      if (!email || !password) {
        e.preventDefault();
        alert("Please fill in both fields"); 
      }
    });
  }

  const modal = document.getElementById("errorModal");

  if (modal) {
    modal.style.display = "block";

    const closeBtn = modal.querySelector(".close");


    closeBtn.onclick = function() {      modal.style.display = "none";
    }
    window.onclick = function(event) {
      if (event.target == modal) {
        modal.style.display = "none";
      }
    };
  }
});
