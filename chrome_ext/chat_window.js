document.addEventListener('DOMContentLoaded', () => {
    const messages = document.getElementById("chatbot-messages");
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');

    const LOGIN_ENDPOINT = 'http://127.0.0.1:8000/auth/login';
    const REGISTER_ENDPOINT = 'http://127.0.0.1:8000/auth/register';


    /* -----------------------------------
       공통 메시지 출력 함수
    ----------------------------------- */
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

        wrapper.innerHTML = `
            <div class="user-bubble">${text}</div>
        `;

        messages.appendChild(wrapper);
        messages.scrollTop = messages.scrollHeight;
    }

    /* -----------------------------------
       이메일 입력 UI를 말풍선 형태로 출력
    ----------------------------------- */
    function appendEmailInputBubble() {
        const wrapper = document.createElement("div");
        wrapper.className = "bot-message-wrapper";

        wrapper.innerHTML = `
            <img class="message-icon" src="./profile.png">
            <div class="message-bubble" style="display:flex; flex-direction:column; gap:8px;">
                
                <div>안녕하세요! LOST112 챗봇입니다.<br>이메일을 입력해주세요!</div>

                <input 
                    id="email-input-field"
                    type="email" 
                    placeholder="you@example.com"
                    style="
                        width: 85%; 
                        padding: 10px; 
                        border-radius: 10px; 
                        border: 1px solid #aaa;
                        font-size: 14px;
                    "
                />

                <button
                    id="email-input-submit"
                    style="
                        background:#1b4ea3; 
                        color:white; 
                        border:none;
                        padding:10px;
                        border-radius:10px;
                        cursor:pointer;
                        font-weight:bold;
                    "
                >
                    제출
                </button>

                <div id="email-input-error" style="color:red; font-size:13px; display:none;"></div>
            </div>
        `;

        messages.appendChild(wrapper);
        messages.scrollTop = messages.scrollHeight;

        document.getElementById("email-input-submit")
            .addEventListener("click", handleEmailSubmit);

        document.getElementById("email-input-field")
            .addEventListener("keydown", e => {
                if (e.key === "Enter") handleEmailSubmit();
            });
    }

    /* -----------------------------------
       이메일 검증
    ----------------------------------- */
    function validateEmail(email) {
        return /\S+@\S+\.\S+/.test(email);
    }

    /* -----------------------------------
       이메일 제출 처리
    ----------------------------------- */
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
        /* =============================
           1) 로그인 먼저 시도
        ============================= */
        let res = await fetch(LOGIN_ENDPOINT, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });

        if (res.ok) {
            const data = await res.json();
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("user_email", data.email);
            localStorage.setItem("user_id", data.user_id);

            appendBotMessage("로그인되었습니다! 무엇을 도와드릴까요?");
            finishEmailInput();
            return;
        }

        /* =============================
           2) 로그인 실패 → 회원가입 시도
        ============================= */
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

        /* =============================
           3) 회원가입 성공 → 다시 로그인
        ============================= */
        res = await fetch(LOGIN_ENDPOINT, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email })
        });

        if (!res.ok) {
            errorField.innerText = "회원가입 후 로그인에 실패했습니다.";
            errorField.style.display = "block";
            return;
        }

        const data = await res.json();
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("user_email", data.email);
        localStorage.setItem("user_id", data.user_id);

        appendBotMessage("회원가입 완료! 로그인되었습니다.");
        finishEmailInput();

    } catch (e) {
        console.error(e);
        errorField.innerText = "서버 오류가 발생했습니다.";
        errorField.style.display = "block";
    }
}
    function finishEmailInput() {
        const emailField = document.getElementById("email-input-field");
        const submitBtn = document.getElementById("email-input-submit");

        if (emailField) emailField.disabled = true;
        if (submitBtn) submitBtn.disabled = true;

        chatInput.disabled = false;
        chatSend.disabled = false;
    }


    /* -----------------------------------
       초기 로딩 (토큰 여부 체크)
    ----------------------------------- */
    const token = localStorage.getItem("access_token");

    if (!token) {
        chatInput.disabled = true;
        chatSend.disabled = true;
        appendEmailInputBubble();
    } else {
        appendBotMessage("다시 오셨군요! 무엇을 도와드릴까요?");
    }

    /* -----------------------------------
       일반 채팅 전송 기능
    ----------------------------------- */
    chatSend.addEventListener("click", () => {
        const text = chatInput.value.trim();
        if (!text) return;
        appendUserMessage(text);
        chatInput.value = "";
    });

    chatInput.addEventListener("keydown", e => {
        if (e.key === "Enter") chatSend.click();
    });
});
