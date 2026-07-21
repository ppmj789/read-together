/* read-together 동작 테스트 하네스
 * index.html 을 jsdom 으로 그대로 구동한다. Supabase CDN 이 없으므로
 * 앱이 스스로 오프라인(localStorage) 모드로 폴백 — 실제 코드 경로를 그대로 탄다. */
import { JSDOM, VirtualConsole } from 'jsdom';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = fileURLToPath(new URL('../..', import.meta.url));
const HTML = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');

export const tick = () => new Promise((r) => setTimeout(r, 0));

export function boot() {
  const errors = [];
  const vc = new VirtualConsole();
  vc.on('jsdomError', (e) => {
    // scrollTo / window.open 은 jsdom 미구현 — 앱 오류가 아니므로 무시
    if (!/scrollTo|window\.open|Not implemented/.test(String(e.message))) errors.push(e);
  });
  vc.on('error', () => {});
  const dom = new JSDOM(HTML, {
    runScripts: 'dangerously',
    url: 'http://localhost/',
    pretendToBeVisual: true,
    virtualConsole: vc,
  });
  const w = dom.window;
  w.scrollTo = () => {};
  w.open = () => null;
  // 다이얼로그 기본값: 모두 승인 / 입력 취소. 테스트에서 개별 재정의 가능.
  w.confirm = () => true;
  w.prompt = () => null;
  w.alert = () => {};
  // 인앱 다이얼로그(uiConfirm/uiPrompt)도 기본 스텁 — 실제 모달 UI 테스트는 __real* 로 복원
  w.__realUiConfirm = w.uiConfirm;
  w.__realUiPrompt = w.uiPrompt;
  w.uiConfirm = async () => true;
  w.uiPrompt = async () => null;
  const d = w.document;

  const api = {
    dom,
    w,
    d,
    errors,
    /** 현재 활성 페이지 이름 (page-xxx → xxx) */
    page() {
      const p = d.querySelector('.page.active');
      return p ? p.id.replace('page-', '') : null;
    },
    toasts() {
      return [...d.querySelectorAll('#toast-area .alert')].map((e) => e.textContent);
    },
    lastToast() {
      const t = api.toasts();
      return t.length ? t[t.length - 1] : null;
    },
    logoutVisible() {
      return d.getElementById('logout-btn').style.display !== 'none';
    },
    /** 휴대폰 4자리 로그인 (기본 1234) — 오프라인이라 동기 완료 */
    async loginAs(p4 = '1234') {
      d.getElementById('pin').value = p4;
      await w.login();
      await tick();
    },
    /** popstate 시뮬레이션 — 앱이 pushState 한 것과 같은 형태의 state 로 발화 */
    async pop(state) {
      w.dispatchEvent(new w.PopStateEvent('popstate', { state }));
      await tick();
    },
    close() {
      w.close();
    },
  };
  return api;
}

/** node:test 용 — 테스트 종료 시 창 자동 정리 */
export function app(t) {
  const a = boot();
  t.after(() => a.close());
  return a;
}
