// Global App Functions

function logout() {
    localStorage.removeItem("user");
    window.location.href = "/login";
}

// Show logged-in user
const user = JSON.parse(localStorage.getItem("user"));

if (user) {
    const name = document.getElementById("userName");
    if (name) {
        name.innerText = user.full_name;
    }
}

