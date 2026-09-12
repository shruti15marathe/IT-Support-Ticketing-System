const form = document.getElementById("loginForm");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    const response = await fetch("/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password })
    });

    const result = await response.json();

    if (!result.success) {
        alert(result.message);
        return;
    }

    localStorage.setItem("user", JSON.stringify(result.user));

    if (result.user.role === "admin") {
        window.location.href = "/admin";
    } else if (result.user.role === "technician") {
        window.location.href = "/technicians";
    } else {
        window.location.href = "/customer";
    }
});