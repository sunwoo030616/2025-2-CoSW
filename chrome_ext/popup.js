document.getElementById('pingBtn').addEventListener('click', async () => {
    const result = document.getElementById('result');
    result.textContent = '요청 중...';
    try {
        const res = await fetch('http://127.0.0.1:8000/api/ping/');
        const data = await res.json();
        result.textContent = JSON.stringify(data);
    } catch (err) {
        result.textContent = '에러: ' + err.message;
    }
});
