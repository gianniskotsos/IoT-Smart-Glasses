// public/JS/home.js
document.querySelectorAll(".user-card .view-btn").forEach(btn => {
  btn.addEventListener("click", (e) => {
    const userId = e.target.closest(".user-card").dataset.userid;
    // Redirect to the user's page
    window.location.href = `/live-view/${userId}`;
  });
});


document.getElementById("logout-btn").addEventListener("click", () => {
    window.location.href = "/logout";
}); 