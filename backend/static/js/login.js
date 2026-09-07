const form = document.getElementById("loginForm");
const message = document.getElementById("message");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {

        const response = await fetch("/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        const result = await response.json();

        if (result.success) {

            localStorage.setItem("user", JSON.stringify(result.user));

            if (result.user.role === "admin") {
                window.location.href = "/admin";
            }
            else if (result.user.role === "technician") {
                window.location.href = "/technicians";
            }
            else if (result.user.role === "customer") {
                window.location.href = "/customer";
            }

        } else {
            message.style.color = "red";
            message.innerText = result.message;
        }

    } catch (err) {
        message.style.color = "red";
        message.innerText = "Server not connected";
        console.error(err);
    }
});