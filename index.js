addEventListener("fetch", event => event.respondWith(handle(event.request)));

async function handle(request){
  const url = new URL(request.url);
  if (url.pathname === "/api/chat" && request.method === "POST") return handleChat(request);
  if (url.pathname === "/api/reset" && request.method === "POST") return handleReset(request);
  return new Response("not found", {status:404});
}

async function handleChat(request){
  let { OPENROUTER_API_KEY, KV_SESSIONS } = globalThis;

  let body;
  try{ body = await request.json(); } catch(e){ body = {}; }
  const userMsg = String(body.message||"").slice(0,2000);
  if(!userMsg) return json({error:"empty"},400);

  const cookies = (request.headers.get("cookie")||"").split(";").map(s=>s.trim());
  let sid = cookies.find(c=>c.startsWith("anon_sid="))?.split("=")[1];
  if(!sid) sid = crypto.randomUUID();

  const raw = await KV_SESSIONS.get(sid);
  let msgs = raw ? JSON.parse(raw) : [];
  msgs.push({role:"user", content:userMsg});
  msgs = msgs.slice(-6);

  const payload = { messages: [{role:"system", content:"You are light-hearted and brief."}, ...msgs] };
  const orResp = await fetch("https://api.openrouter.ai/v1/chat/completions", {
    method:"POST",
    headers:{
      "Authorization": `Bearer ${OPENROUTER_API_KEY}`,
      "Content-Type":"application/json"
    },
    body: JSON.stringify(payload),
  }).catch(()=>null);

  const j = orResp ? await orResp.json().catch(()=>({})) : {};
  const reply = (j?.choices?.[0]?.message?.content) || j?.reply || "sorry, no reply";

  msgs.push({role:"assistant", content:reply});
  await KV_SESSIONS.put(sid, JSON.stringify(msgs), { expirationTtl: 86400 });

  const headers = {
    "Content-Type":"application/json",
    "Set-Cookie": `anon_sid=${sid}; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=86400`
  };
  return new Response(JSON.stringify({reply}), {status:200, headers});
}

async function handleReset(request){
  const cookies = (request.headers.get("cookie")||"").split(";").map(s=>s.trim());
  const sid = cookies.find(c=>c.startsWith("anon_sid="))?.split("=")[1];
  if(sid) await KV_SESSIONS.delete(sid);
  return new Response(JSON.stringify({ok:true}), {
    status:200,
    headers:{
      "Content-Type":"application/json",
      "Set-Cookie":"anon_sid=deleted; HttpOnly; Secure; SameSite=Strict; Max-Age=0"
    }
  });
}

function json(obj, status=200){
  return new Response(JSON.stringify(obj), {status, headers:{"Content-Type":"application/json"}});
}
