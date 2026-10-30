/* Data layer. Two backends behind one interface:
     - API mode (python backend/server.py): talks to /api/...
     - static mode (GitHub Pages, window.AID_CONFIG.static): reads data/ files, optionally
       decrypting them with the shared password, and writes through the GitHub API by
       committing files to incoming/ and ops/ that the build workflow applies.
   Interface: load(), report(id), imageUrl(id, name), upload(fields, file), updateReport(id, p),
   deleteReport(id), saveSectors(list), login(pw), logout(), needsLogin(), canDownload(), mode.
*/
window.DataLayer = (function(){
  'use strict';
  const cfg = window.AID_CONFIG || {static: false};
  const ENC_MAGIC = 'AIDENC1';
  const ITER = 310000;
  const te = new TextEncoder(), td = new TextDecoder();

  /* ------------------------------------------------------------ crypto (matches backend/crypto_util.py) */
  let key = null;            // CryptoKey (AES-GCM) once signed in
  async function deriveKey(password, salt){
    const base = await crypto.subtle.importKey('raw', te.encode(password), 'PBKDF2', false, ['deriveKey']);
    return crypto.subtle.deriveKey({name: 'PBKDF2', salt: te.encode(salt), iterations: ITER, hash: 'SHA-256'}, base,
      {name: 'AES-GCM', length: 256}, true, ['encrypt', 'decrypt']);
  }
  async function decryptBuf(buf){
    const u = new Uint8Array(buf);
    const magic = td.decode(u.slice(0, ENC_MAGIC.length));
    if (magic !== ENC_MAGIC) throw new Error('not encrypted');
    const iv = u.slice(ENC_MAGIC.length, ENC_MAGIC.length + 12);
    const ct = u.slice(ENC_MAGIC.length + 12);
    return crypto.subtle.decrypt({name: 'AES-GCM', iv}, key, ct);
  }
  async function encryptBuf(buf){
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const ct = new Uint8Array(await crypto.subtle.encrypt({name: 'AES-GCM', iv}, key, buf));
    const out = new Uint8Array(ENC_MAGIC.length + 12 + ct.length);
    out.set(te.encode(ENC_MAGIC), 0); out.set(iv, ENC_MAGIC.length); out.set(ct, ENC_MAGIC.length + 12);
    return out;
  }
  async function restoreKey(){
    try {
      const raw = sessionStorage.getItem('aid_key');
      if (!raw) return false;
      const bytes = Uint8Array.from(atob(raw), c => c.charCodeAt(0));
      key = await crypto.subtle.importKey('raw', bytes, {name: 'AES-GCM'}, true, ['encrypt', 'decrypt']);
      return true;
    } catch (e) { return false; }
  }
  async function storeKey(){
    const raw = new Uint8Array(await crypto.subtle.exportKey('raw', key));
    sessionStorage.setItem('aid_key', btoa(String.fromCharCode.apply(null, raw)));
  }
  function b64(bytes){
    let s = '';
    for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return btoa(s);
  }

  /* ------------------------------------------------------------ fetch helpers */
  async function getBytes(path){
    const r = await fetch(path, {cache: 'no-cache'});
    if (r.status === 404) return null;
    if (!r.ok) throw new Error(r.status + ' ' + path);
    return r.arrayBuffer();
  }
  async function getJson(path){
    const plain = await getBytes(path);
    if (plain) return JSON.parse(td.decode(plain));
    if (!cfg.encrypted) return null;
    const enc = await getBytes(path + '.enc');
    if (!enc) return null;
    if (!key) throw Object.assign(new Error('login required'), {needLogin: true});
    return JSON.parse(td.decode(await decryptBuf(enc)));
  }

  /* ------------------------------------------------------------ GitHub API writes */
  const GH = 'https://api.github.com';
  function token(){ try { return localStorage.getItem('aid_gh_token') || ''; } catch (e) { return ''; } }
  function setToken(t){ try { if (t) localStorage.setItem('aid_gh_token', t); else localStorage.removeItem('aid_gh_token'); } catch (e) {} }
  let askToken = null;      // set by the app: () => Promise<string>
  async function ensureToken(){
    let t = token();
    if (!t && askToken) t = await askToken();
    if (!t) throw new Error('GitHub token required');
    return t;
  }
  async function gh(method, path, body){
    const t = await ensureToken();
    const r = await fetch(GH + path, {method, headers: {Authorization: 'Bearer ' + t, Accept: 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'Content-Type': 'application/json'}, body: body ? JSON.stringify(body) : undefined});
    let data = null; try { data = await r.json(); } catch (e) {}
    if (r.status === 401 || r.status === 403){ setToken(''); throw new Error('GitHub rejected the token (' + r.status + '): ' + ((data && data.message) || '')); }
    if (!r.ok) throw new Error('GitHub ' + r.status + ': ' + ((data && data.message) || path));
    return data;
  }
  async function putFile(path, bytes, message){
    let sha;
    try { const cur = await gh('GET', `/repos/${cfg.repo}/contents/${path}?ref=${cfg.branch}`); sha = cur && cur.sha; } catch (e) { sha = undefined; }
    const body = {message, content: b64(bytes), branch: cfg.branch};
    if (sha) body.sha = sha;
    return gh('PUT', `/repos/${cfg.repo}/contents/${path}`, body);
  }
  async function putJson(path, obj, message){
    let bytes = te.encode(JSON.stringify(obj, null, cfg.encrypted ? 0 : 2));
    if (cfg.encrypted){ bytes = await encryptBuf(bytes); path += '.enc'; }
    return putFile(path, bytes, message);
  }
  function uid(){ return (crypto.randomUUID ? crypto.randomUUID() : (Date.now().toString(16) + Math.random().toString(16).slice(2))).replace(/-/g, ''); }

  /* ------------------------------------------------------------ static backend */
  const imageCache = {};   // id -> {name: objectURL}
  const staticBackend = {
    mode: 'static',
    needsLogin(){ return !!cfg.encrypted && !key; },
    canDownload(){ return false; },
    async init(){ if (cfg.encrypted) await restoreKey(); },
    async login(password){
      const saltBuf = await getBytes('data/salt.txt');
      if (!saltBuf) throw new Error('data/salt.txt missing');
      key = await deriveKey(password, td.decode(saltBuf).trim());
      try { await getJson('data/index.json'); }
      catch (e) { key = null; throw new Error('wrong password'); }
      await storeKey();
    },
    async logout(){ key = null; try { sessionStorage.removeItem('aid_key'); } catch (e) {} },
    async load(){
      const idx = await getJson('data/index.json');
      if (!idx) throw new Error('data/index.json missing: run the build workflow once');
      const meta = idx.meta || {};
      meta.auth = !!cfg.encrypted;
      return {sectors: idx.sectors || [], reports: idx.reports || [], meta};
    },
    async report(id){
      if (cfg.encrypted){
        const buf = await getBytes(`data/reports/${id}/bundle.enc`);
        if (!buf) throw new Error('report not found');
        if (!key) throw Object.assign(new Error('login required'), {needLogin: true});
        const bundle = JSON.parse(td.decode(await decryptBuf(buf)));
        if (imageCache[id]) Object.values(imageCache[id]).forEach(u => URL.revokeObjectURL(u));
        imageCache[id] = {};
        Object.keys(bundle.images || {}).forEach(name => {
          const bytes = Uint8Array.from(atob(bundle.images[name]), c => c.charCodeAt(0));
          const ext = name.split('.').pop().toLowerCase();
          const type = ext === 'jpg' || ext === 'jpeg' ? 'image/jpeg' : (ext === 'gif' ? 'image/gif' : (ext === 'svg' ? 'image/svg+xml' : 'image/png'));
          imageCache[id][name] = URL.createObjectURL(new Blob([bytes], {type}));
        });
        return {meta: bundle.meta, content: bundle.content};
      }
      const content = await getJson(`data/reports/${id}/content.json`);
      const meta = await getJson(`data/reports/${id}/meta.json`);
      if (!content || !meta) throw new Error('report not found');
      return {meta, content};
    },
    imageUrl(id, name){
      if (cfg.encrypted) return (imageCache[id] && imageCache[id][name]) || '';
      return `data/reports/${id}/images/${encodeURIComponent(name)}`;
    },
    async upload(fields, file){
      const id = uid();
      const ext = (file.name.split('.').pop() || 'docx').toLowerCase();
      let bytes = new Uint8Array(await file.arrayBuffer());
      let path = `incoming/${id}.${ext}`;
      if (cfg.encrypted){ if (!key) throw Object.assign(new Error('login required'), {needLogin: true}); bytes = await encryptBuf(bytes); path += '.enc'; }
      await putFile(path, bytes, `upload: ${file.name}`);
      const side = Object.assign({}, fields, {source_name: file.name, uploaded_at: new Date().toISOString()});
      await putJson(`incoming/${id}.meta.json`, side, `upload meta: ${file.name}`);
      return {pending: true, id};
    },
    async updateReport(id, payload){ await putJson(`ops/${Date.now()}-${uid().slice(0, 6)}.json`, Object.assign({op: 'update_meta', id}, payload), `edit: ${id}`); return {pending: true, id}; },
    async deleteReport(id){ await putJson(`ops/${Date.now()}-${uid().slice(0, 6)}.json`, {op: 'delete', id}, `delete: ${id}`); return {pending: true}; },
    async saveSectors(list){
      const bytes = te.encode(JSON.stringify(list, null, 2));
      await putFile('data/sectors.json', bytes, 'sectors: update');
      return {pending: true, sectors: list};
    },
    setTokenPrompt(fn){ askToken = fn; },
    token, setToken,
    actionsUrl(){ return 'https://github.com/' + cfg.repo + '/actions'; },
  };

  /* ------------------------------------------------------------ API backend (local python server) */
  async function api(path, opts){
    const r = await fetch(path, opts);
    if (r.status === 401) throw Object.assign(new Error('login required'), {needLogin: true, redirect: '/login.html'});
    let data = null; try { data = await r.json(); } catch (e) {}
    if (!r.ok) throw new Error((data && data.error) || (r.status + ' ' + r.statusText));
    return data;
  }
  const J = {'Content-Type': 'application/json'};
  const apiBackend = {
    mode: 'api',
    needsLogin(){ return false; },
    canDownload(){ return true; },
    async init(){},
    async login(){ },
    async logout(){ try { await fetch('/api/logout', {method: 'POST'}); } catch (e) {} },
    async load(){
      const [sectors, reports, meta] = await Promise.all([api('/api/sectors'), api('/api/reports'), api('/api/meta')]);
      return {sectors, reports, meta};
    },
    report(id){ return api('/api/reports/' + encodeURIComponent(id)); },
    imageUrl(id, name){ return '/api/reports/' + encodeURIComponent(id) + '/images/' + encodeURIComponent(name); },
    async upload(fields, file){
      const fd = new FormData();
      fd.append('file', file);
      Object.keys(fields).forEach(k => fd.append(k, fields[k] == null ? '' : fields[k]));
      return api('/api/upload', {method: 'POST', body: fd});
    },
    updateReport(id, payload){ return api('/api/reports/' + encodeURIComponent(id), {method: 'PUT', headers: J, body: JSON.stringify(payload)}); },
    deleteReport(id){ return api('/api/reports/' + encodeURIComponent(id), {method: 'DELETE'}); },
    async saveSectors(list){
      // diff against the server: add new, update changed, delete missing, then set order
      const cur = await api('/api/sectors');
      const curIds = new Set(cur.map(s => s.id));
      for (const s of list){
        if (!curIds.has(s.id)) { const made = await api('/api/sectors', {method: 'POST', headers: J, body: JSON.stringify(s)}); s.id = made.id; }
        else await api('/api/sectors/' + encodeURIComponent(s.id), {method: 'PUT', headers: J, body: JSON.stringify(s)});
      }
      for (const s of cur) if (!list.find(x => x.id === s.id)) await api('/api/sectors/' + encodeURIComponent(s.id), {method: 'DELETE'});
      await api('/api/sectors-order', {method: 'PUT', headers: J, body: JSON.stringify({order: list.map(s => s.id)})});
      return {pending: false, sectors: await api('/api/sectors')};
    },
    sourceUrl(id){ return '/api/reports/' + encodeURIComponent(id) + '/source'; },
    setTokenPrompt(){},
    actionsUrl(){ return ''; },
  };

  return cfg.static ? staticBackend : apiBackend;
})();
