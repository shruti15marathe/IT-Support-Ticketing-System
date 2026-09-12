if (!window.notificationsLoaded) {
    window.notificationsLoaded = true;

    const currentUser =
        JSON.parse(localStorage.getItem("user"));

    const notificationBtn =
        document.getElementById("notificationBtn");

    const notificationPanel =
        document.getElementById("notificationPanel");

    const notificationList =
        document.getElementById("notificationList");

    const notifBadge =
        document.getElementById("notifBadge");

    const markAllReadBtn =
        document.getElementById("markAllReadBtn");

        const clearAllBtn = document.getElementById("clearAllBtn");
const closeBtn = document.getElementById("closeBtn");

// Close panel
closeBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    notificationPanel.classList.remove("show");
});

// Clear all notifications
clearAllBtn.addEventListener("click", async (e) => {
    e.stopPropagation();

    await fetch(`/notifications/${currentUser.id}/clear`, {
        method: "DELETE"
    });

    await loadNotifications();
});

    async function loadNotifications() {
        if (!currentUser) return;

        try {
            const response = await fetch(
                `/notifications/${currentUser.id}`
            );

            if (!response.ok) {
                throw new Error("Failed to load notifications");
            }

            const notifications = await response.json();

            const unreadCount =
                notifications.filter(n => !n.is_read).length;

            notifBadge.innerText = unreadCount;

            notifBadge.style.display =
                unreadCount > 0 ? "inline-block" : "none";

            if (!notifications.length) {
                notificationList.innerHTML = `
                    <div class="notification-empty">
                        No notifications
                    </div>
                `;
                return;
            }

            notificationList.innerHTML =
                notifications.map(notification => `
                    <div
                        class="notification-item ${
                            !notification.is_read ? "unread" : ""
                        }"
                        data-id="${notification.id}">

                        <strong>
                            ${notification.title}
                        </strong>

                        <p>
                            ${notification.message}
                        </p>

                        <small>
                            ${formatNotificationDate(
                                notification.created_at
                            )}
                        </small>

                    </div>
                `).join("");

            document
                .querySelectorAll(".notification-item")
                .forEach(item => {
                    item.addEventListener("click", () => {
                        markAsRead(item.dataset.id);
                    });
                });

        } catch (error) {
            console.error(
                "Notification error:",
                error
            );
        }
    }

 function formatNotificationDate(value) {
    if (!value) return "";

    const date = new Date(value);

    const day = String(date.getUTCDate()).padStart(2, "0");
    const month = date.toLocaleString("en-IN", {
        month: "short",
        timeZone: "Asia/Kolkata"
    });


    let hours = date.getUTCHours();
    const minutes = String(date.getUTCMinutes()).padStart(2, "0");

    const period = hours >= 12 ? "PM" : "AM";
    hours = hours % 12 || 12;

    return `${month} ${day}, ${hours}:${minutes} ${period}`;
}
    async function markAsRead(id) {
        try {
            await fetch(
                `/notifications/${id}/read`,
                {
                    method: "PUT"
                }
            );

            await loadNotifications();

        } catch (error) {
            console.error(error);
        }
    }

    notificationBtn.addEventListener("click", event => {
        event.stopPropagation();

        notificationPanel.classList.toggle("show");
    });

    markAllReadBtn.addEventListener("click", async event => {
        event.stopPropagation();

        const items =
            document.querySelectorAll(
                ".notification-item.unread"
            );

        for (const item of items) {
            await markAsRead(item.dataset.id);
        }

        await loadNotifications();
    });

    document.addEventListener("click", event => {
        if (
            !notificationPanel.contains(event.target) &&
            !notificationBtn.contains(event.target)
        ) {
            notificationPanel.classList.remove("show");
        }
    });


closeBtn.addEventListener("click",(e)=>{
    e.stopPropagation();
    notificationPanel.classList.remove("show");
});

clearAllBtn.addEventListener("click",async(e)=>{
    e.stopPropagation();
    await fetch(`/notifications/${currentUser.id}/clear`,{
        method:"DELETE"
    });
    loadNotifications();
});

    loadNotifications();
    setInterval(loadNotifications,5000);
} 
