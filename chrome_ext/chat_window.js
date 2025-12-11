document.addEventListener('DOMContentLoaded', () => {

    /* ============================================================
       기본 DOM 요소
    ============================================================ */
    const messages = document.getElementById("chatbot-messages");
    const chatInput = document.getElementById("chat-input");
    const chatSend = document.getElementById("chat-send");

    const attachButton = document.getElementById("attach-button");
    const imageInput = document.getElementById("image-input");
    const imagePreviewBox = document.getElementById("image-preview-box");

    let selectedImageFile = null;   // ← 선택된 단일 이미지 저장


    /* ============================================================
       EMAIL LOGIN / REGISTER 부분 (그대로 유지)
    ============================================================ */

    const LOGIN_ENDPOINT = 'http://127.0.0.1:8000/auth/login';
    const REGISTER_ENDPOINT = 'http://127.0.0.1:8000/auth/register';

    function appendBotMessage(text) {
        const wrapper = document.createElement("div");
        wrapper.className = "bot-message-wrapper";

        wrapper.innerHTML = `
            <img class="message-icon" src="./profile.png">
            <div class="message-bubble">${text}</div>
        `;
        messages.appendChild(wrapper);
        messages.scrollTop = messages.scrollHeight;
    }

    function appendUserMessage(text) {
        const wrapper = document.createElement("div");
        wrapper.className = "user-message-wrapper";
        wrapper.innerHTML = `<div class="user-bubble">${text}</div>`;
        messages.appendChild(wrapper);
        messages.scrollTop = messages.scrollHeight;
    }

    function appendEmailInputBubble() {
        const wrapper = document.createElement("div");
        wrapper.className = "bot-message-wrapper";

        wrapper.innerHTML = `
            <img class="message-icon" src="./profile.png">
            <div class="message-bubble" style="display:flex; flex-direction:column; gap:8px;">
                <div>안녕하세요! LOST112 챗봇입니다.<br>이메일을 입력해주세요!</div>

                <input id="email-input-field" type="email" placeholder="you@example.com"
                       style="width: 85%; padding: 10px; border-radius: 10px; border: 1px solid #aaa; font-size: 14px;" />

                <button id="email-input-submit"
                    style="background:#1b4ea3; color:white; border:none; padding:10px; border-radius:10px; cursor:pointer; font-weight:bold;">
                    제출
                </button>

                <div id="email-input-error" style="color:red; font-size:13px; display:none;"></div>
            </div>
        `;
        messages.appendChild(wrapper);
        messages.scrollTop = messages.scrollHeight;

        document.getElementById("email-input-submit").addEventListener("click", handleEmailSubmit);
        document.getElementById("email-input-field").addEventListener("keydown", e => {
            if (e.key === "Enter") handleEmailSubmit();
        });
    }

    function validateEmail(email) {
        return /\S+@\S+\.\S+/.test(email);
    }

    async function handleEmailSubmit() {
        const emailField = document.getElementById("email-input-field");
        const errorField = document.getElementById("email-input-error");
        const email = emailField.value.trim();

        if (!validateEmail(email)) {
            errorField.innerText = "유효한 이메일을 입력해주세요.";
            errorField.style.display = "block";
            return;
        }
        errorField.style.display = "none";

        try {
            let res = await fetch(LOGIN_ENDPOINT, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email })
            });

            if (res.ok) {
                const data = await res.json();
                saveAuth(data);
                appendBotMessage("로그인되었습니다! 무엇을 도와드릴까요?");
                finishEmailInput();
                return;
            }

            res = await fetch(REGISTER_ENDPOINT, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email })
            });

            if (!res.ok) {
                errorField.innerText = "회원가입 실패했습니다.";
                errorField.style.display = "block";
                return;
            }

            res = await fetch(LOGIN_ENDPOINT, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email })
            });

            const data = await res.json();
            saveAuth(data);
            appendBotMessage("회원가입 완료! 로그인되었습니다.");
            finishEmailInput();
        } catch (e) {
            console.error(e);
            errorField.innerText = "서버 오류가 발생했습니다.";
            errorField.style.display = "block";
        }
    }

    function saveAuth(data) {
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("user_email", data.email);
        localStorage.setItem("user_id", data.user_id);
    }

    function finishEmailInput() {
        chatInput.disabled = false;
        chatSend.disabled = false;
    }

    const tokenNow = localStorage.getItem("access_token");
    if (!tokenNow) {
        chatInput.disabled = true;
        chatSend.disabled = true;
        appendEmailInputBubble();
    } else {
        appendBotMessage("다시 오셨군요! 무엇을 도와드릴까요?");
    }


    /* ============================================================
       📸 이미지 첨부 기능
    ============================================================ */

    attachButton.addEventListener("click", () => imageInput.click());

    imageInput.addEventListener("change", () => {
        if (imageInput.files && imageInput.files[0]) {
            selectedImageFile = imageInput.files[0];

            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreviewBox.innerHTML = `
                    <img src="${e.target.result}" style="height:60px; border-radius:8px; border:1px solid #ccc;">
                    <span id="image-preview-remove" style="font-size:20px; font-weight:bold; cursor:pointer;">✖</span>
                `;
                imagePreviewBox.style.display = "flex";
            };
            reader.readAsDataURL(selectedImageFile);
        }
    });

    imagePreviewBox.addEventListener("click", (e) => {
        if (e.target.id === "image-preview-remove") {
            selectedImageFile = null;
            imageInput.value = "";
            imagePreviewBox.style.display = "none";
        }
    });


    /* ============================================================
       ✉️ 메시지 전송 (텍스트 + 이미지 동시)
    ============================================================ */

    function sendMessage() {
        const text = chatInput.value.trim();
        if (!text && !selectedImageFile) return;

        if (text) appendUserMessage(text);
        if (selectedImageFile) appendUserImage(selectedImageFile);

        handleUserLostItem(text, selectedImageFile);

        chatInput.value = "";
        selectedImageFile = null;
        imageInput.value = "";
        imagePreviewBox.style.display = "none";
    }

    chatSend.addEventListener("click", sendMessage);
    chatInput.addEventListener("keyup", e => {
        if (e.key === "Enter") sendMessage();
    });

    function appendUserImage(file) {
        const wrapper = document.createElement("div");
        wrapper.className = "user-message-wrapper";

        const imgURL = URL.createObjectURL(file);

        wrapper.innerHTML = `
            <div class="user-bubble">
                <img src="${imgURL}" style="max-width:200px; border-radius:12px; object-fit:cover;">
            </div>
        `;
        messages.appendChild(wrapper);
        messages.scrollTop = messages.scrollHeight;
    }


    /* ============================================================
       🔥 POST /items (텍스트 + 이미지 지원)
    ============================================================ */
    async function handleUserLostItem(text, imageFile) {
        const token = localStorage.getItem("access_token");
        if (!token) {
            appendBotMessage("로그인 후 이용해주세요.");
            return;
        }

        const formData = new FormData();
        if (text) formData.append("description", text);
        if (imageFile) formData.append("image", imageFile);

        try {
            const res = await fetch("http://127.0.0.1:8000/items", {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` },
                body: formData
            });

            const data = await res.json();
            appendMatchResult(data);

        } catch (err) {
            console.error(err);
            appendBotMessage("서버 오류가 발생했습니다.");
        }
    }


    /* ============================================================
       🎯 매칭 UI
    ============================================================ */
    function appendMatchResult(data) {
        const wrapper = document.createElement("div");
        wrapper.className = "bot-message-wrapper";

        let html = `
            <img class="message-icon" src="./profile.png">
            <div class="message-bubble">
                입력하신 정보와 유사한 분실물 ${data.immediate_matches.length}건을 찾았어요.<br>
                아래에서 확인해주세요.<br><br>
                <div class="match-container">
        `;

        data.immediate_matches.forEach(item => {
            html += `
                <div class="match-card" data-detail="${item.detail_link}">
                    <img src="${item.police_image_url}" class="match-img">
                    <div class="match-name">${item.item_name}</div>
                    <div class="match-desc">${item.ai_generated_desc}</div>
                </div>
            `;
        });

        html += `
                </div>
                <button class="no-item-button">제 물건이 없어요</button>
                <button class="found-button" data-request-id="${data.registered_item.request_id}">
                    찾았어요 (알림 중지)
                </button>
            </div>
        `;

        wrapper.innerHTML = html;
        messages.appendChild(wrapper);
        messages.scrollTop = messages.scrollHeight;
    }


    /* ============================================================
       🔕 PATCH /items/cease/{id}
    ============================================================ */
    async function stopNotification(requestId) {
        const token = localStorage.getItem("access_token");

        try {
            const res = await fetch(`http://127.0.0.1:8000/items/cease/${requestId}`, {
                method: "PATCH",
                headers: { "Authorization": `Bearer ${token}` }
            });

            const data = await res.json();
            appendBotMessage(data.message);

        } catch (err) {
            console.error(err);
            appendBotMessage("알림 중지에 실패했습니다.");
        }
    }


    /* ============================================================
       전역 클릭 이벤트 처리
    ============================================================ */
    document.addEventListener("click", (e) => {

        if (e.target.closest(".match-card")) {
            const url = e.target.closest(".match-card").dataset.detail;
            window.open(url, "_blank");
            return;
        }

        if (e.target.classList.contains("no-item-button")) {
            appendBotMessage("걱정마세요! 유사한 물건이 등록되는 즉시 이메일로 알려드릴게요.");
            return;
        }

        if (e.target.classList.contains("found-button")) {
            const requestId = e.target.dataset.requestId;
            stopNotification(requestId);
            return;
        }
    });

});
