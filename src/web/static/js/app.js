// app.js — 같이읽자 뉴트로 전역 JS

// ── 세션 유틸 ──
const RT = {
  getToken:         () => sessionStorage.getItem('token'),
  getMeetingId:     () => sessionStorage.getItem('meeting_id'),
  getParticipantId: () => parseInt(sessionStorage.getItem('participant_id') || '0'),
  isHost:           () => sessionStorage.getItem('is_host') === 'true',
  getNickname:      () => localStorage.getItem('rt_nickname') || '',

  authHeaders() {
    return {
      'Authorization': 'Bearer ' + this.getToken(),
      'Content-Type':  'application/json',
    };
  },

  guardAuth() {
    if (!this.getToken()) window.location.href = '/';
  },
};

// ── HTMX 전역 이벤트 훅 ──
document.addEventListener('htmx:configRequest', function(evt) {
  const token = RT.getToken();
  if (token) evt.detail.headers['Authorization'] = 'Bearer ' + token;
});

document.addEventListener('htmx:responseError', function(evt) {
  try {
    const data = JSON.parse(evt.detail.xhr.responseText);
    showToast(data.error?.message || 'API 오류', 'error');
  } catch { showToast('API 오류', 'error'); }
});

// 전역 노출
window.RT = RT;
