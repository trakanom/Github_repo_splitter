async function fetchUsername() {
    const usernameResponse = await fetch("/get-username");
    if (usernameResponse.ok) {
        const { username } = await usernameResponse.json();
        if (username) {
            document.getElementById("connect-github").textContent = "Swap Users";
            document.getElementById("user-status").innerHTML = `✅ Github connected! User: <b>${username}</b>`;
        } else {
            document.getElementById("user-status").innerHTML = "❌ Github not connected";
        }
    }
}

document.getElementById("connect-github").addEventListener("click", async (event) => {
    event.preventDefault();
    const isSwapping = document.getElementById("connect-github").textContent === "Swap Users";
    if (isSwapping) {
        await fetch("/clear-token", { method: "POST" });
        document.getElementById("connect-github").textContent = "Connect Github";
        document.getElementById("user-status").innerHTML = "❌ Github not connected";
    } else {
        const oauth_url = `/connect-github`;
        const auth_window = window.open(oauth_url, "_blank", "width=800, height=600");
        const checkConnect = setInterval(async () => {
            if (auth_window.closed) {
                clearInterval(checkConnect);
                await fetchUsername();
            }
        }, 1000);
    }
});

document.getElementById("start-split").addEventListener("click", () => {
    const requirePreview = document.getElementById("require-preview").checked;
    const clearOriginalRepo = document.getElementById("clear-original-repo").checked;
    const showSummary = document.getElementById("show-summary").checked;

    fetch("/split-repo", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            url: document.getElementById("repo-url").value,
            requirePreview,
            clearOriginalRepo,
            showSummary,
        }),
    })
        .then((response) => response.json())
        .then((data) => {
            console.log(data);
        });
});


document.getElementById("repo-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const repoUrl = document.getElementById("repo-url").value;
    const status = document.getElementById("status");
    status.textContent = "Processing...";

    try {
        const response = await fetch(`/split-repo?url=${encodeURIComponent(repoUrl)}`, { method: "POST" });
        if (response.ok) {
            const data = await response.json();
            status.textContent = `Pull request created: ${data.pull_request_url}`;
        } else {
            status.textContent = "Error: Failed to split the repository.";
        }
    } catch (error) {
        console.error(error);
        status.textContent = "Error: Failed to split the repository.";
    }
});
fetchUsername();