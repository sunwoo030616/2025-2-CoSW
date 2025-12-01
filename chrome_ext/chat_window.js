// chat_window.js 파일 내용 (팝업 창 닫기 로직)
document.addEventListener('DOMContentLoaded', () => {
    const closeButton = document.getElementById('chatbot-close-button');
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            // 새 창을 닫는 JavaScript 명령
            window.close();
        });
    }
});