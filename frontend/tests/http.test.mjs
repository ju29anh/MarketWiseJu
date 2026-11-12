import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test, afterEach } from 'node:test';
import ts from 'typescript';

// Exercise the real TypeScript client with the browser transport replaced.
const asModule = source => 'data:text/javascript;base64,' + Buffer.from(ts.transpileModule(source, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext },
}).outputText).toString('base64');
const errors = asModule(await readFile(new URL('../src/utils/errors.ts', import.meta.url), 'utf8'));
const source = (await readFile(new URL('../src/api/http.ts', import.meta.url), 'utf8'))
  .replace("'../utils/errors'", JSON.stringify(errors)).replace('import.meta.env.VITE_API_BASE_URL', "''");
const { safeFetch, uploadFile, downloadDatasetCsv } = await import(asModule(source));
const nativeFetch = globalThis.fetch;
afterEach(() => { globalThis.fetch = nativeFetch; delete globalThis.XMLHttpRequest; });

test('network failure is visible and does not replay a POST', async () => {
  let calls = 0;
  globalThis.fetch = async () => { calls++; throw new TypeError('Failed to fetch'); };
  await assert.rejects(safeFetch('/api/analysis/jobs', { method: 'POST', body: '{}' }), /Không kết nối được máy chủ/);
  assert.equal(calls, 1);
});

test('proxy failures and missing sessions are never replaced with results', async () => {
  for (const status of [404, 405, 429, 502, 503, 504]) {
    globalThis.fetch = async () => new Response(JSON.stringify({ detail: 'Session unavailable' }), { status });
    await assert.rejects(safeFetch('/api/analysis/missing'), /Session unavailable/);
  }
});

test('a static-host HTML fallback is rejected even with status 200', async () => {
  globalThis.fetch = async () => new Response('<html>SPA</html>', { headers: { 'content-type': 'text/html' } });
  await assert.rejects(safeFetch('/api/datasets'), /dịch vụ/);
});

test('valid JSON is passed through and cancellation stays an AbortError', async () => {
  globalThis.fetch = async () => Response.json({ status: 'ok' });
  assert.deepEqual(await (await safeFetch('/api/health')).json(), { status: 'ok' });
  const controller = new AbortController();
  controller.abort();
  globalThis.fetch = async (_input, init) => { init.signal.throwIfAborted(); };
  await assert.rejects(safeFetch('/api/health', { signal: controller.signal }), { name: 'AbortError' });
  await assert.rejects(safeFetch(new Request('https://example.invalid/api/health', { signal: controller.signal })), { name: 'AbortError' });
});

test('CSV errors are surfaced before creating a download', async () => {
  globalThis.fetch = async () => Response.json({ status: 'ok' });
  let prevented = false;
  await assert.rejects(downloadDatasetCsv('missing', { preventDefault() { prevented = true; } }), /CSV hợp lệ/);
  assert.equal(prevented, true);
});

class FakeXHR {
  upload = {};
  status = 200;
  responseText = '{}';
  open() {}
  abort() { this.onabort(); }
  send() { queueMicrotask(() => FakeXHR.respond(this)); }
}

test('uploads reject network, timeout, proxy and malformed JSON failures', async () => {
  globalThis.XMLHttpRequest = FakeXHR;
  const file = new File(['value\n1'], 'sample.csv');
  for (const failure of [
    xhr => xhr.onerror(),
    xhr => xhr.ontimeout(),
    xhr => { xhr.status = 503; xhr.onload(); },
    xhr => { xhr.responseText = '<html>SPA</html>'; xhr.onload(); },
  ]) {
    FakeXHR.respond = failure;
    await assert.rejects(uploadFile('/datasets/upload', file, 'Sample'));
  }
});

test('uploads return actual responses and respect cancellation', async () => {
  globalThis.XMLHttpRequest = FakeXHR;
  const file = new File(['value\n1'], 'sample.csv');
  FakeXHR.respond = xhr => { xhr.responseText = '{"filename":"upload_real.csv"}'; xhr.onload(); };
  assert.deepEqual(await uploadFile('/datasets/upload', file, 'Sample'), { filename: 'upload_real.csv' });
  const controller = new AbortController();
  FakeXHR.respond = () => controller.abort();
  await assert.rejects(uploadFile('/datasets/upload', file, 'Sample', undefined, controller.signal), { name: 'AbortError' });
  await assert.rejects(uploadFile('/datasets/upload', file, 'Sample', undefined, controller.signal), { name: 'AbortError' });
});
