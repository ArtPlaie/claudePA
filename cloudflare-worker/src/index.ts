// Cloudflare Worker — passerelle entre Telegram et GitHub Actions.
//
// Reçoit les webhooks Telegram et :
// - Pour les commandes (/panic, /resume, /help) : agit directement.
// - Pour les boutons inline (callback_query) sur un draft : dispatch
//   apply-draft.yml.
// - Pour les messages libres : dépose un fichier dans inbox/ via
//   Contents API, puis dispatch on-webhook.yml. Latence aller-retour
//   typique ~30-90s (boot GH Actions).
//
// Cron triggers (cf. wrangler.toml [triggers]) : déclenchent le handler
// `scheduled()` qui dispatch les workflows récurrents via l'API GitHub.
// Latence ~1-2 min vs les 30min-2h des crons natifs GH Actions.

interface Env {
  TELEGRAM_BOT_TOKEN: string;
  TELEGRAM_WEBHOOK_SECRET: string;
  TELEGRAM_CHAT_PERSO: string;
  TELEGRAM_CHAT_FAMILLE: string;
  GITHUB_TOKEN: string;
  GITHUB_REPO: string;
  GITHUB_REF: string;
}

interface TelegramUser {
  id: number;
  first_name?: string;
  username?: string;
}

interface TelegramChat {
  id: number;
  type: string;
}

interface TelegramMessage {
  message_id: number;
  date: number;
  chat: TelegramChat;
  from?: TelegramUser;
  text?: string;
}

interface TelegramCallbackQuery {
  id: string;
  data?: string;
  message?: TelegramMessage;
  from: TelegramUser;
}

interface TelegramUpdate {
  update_id: number;
  message?: TelegramMessage;
  callback_query?: TelegramCallbackQuery;
}

// Mapping cron pattern (tel que déclaré dans wrangler.toml) → workflow
// GH Actions à dispatch. Doit rester synchro avec [triggers].crons.
// Garder UN cron par workflow pour rester lisible côté logs CF.
const CRON_TO_WORKFLOW: Record<string, string> = {
  "30 5 * * *": "task-daily-digest.yml",
  "0 6 * * *": "task-mail-review.yml",
  "0 3 * * *": "task-sliding-window.yml",
  "0 4 * * *": "task-location-context.yml",
  "0 18 * * 0": "task-weekly-lookahead.yml",
};

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (url.pathname === "/health") return new Response("ok");
    if (url.pathname === "/telegram" && req.method === "POST") {
      return handleTelegram(req, env);
    }
    return new Response("not found", { status: 404 });
  },

  async scheduled(
    event: ScheduledEvent,
    env: Env,
    ctx: ExecutionContext,
  ): Promise<void> {
    const workflow = CRON_TO_WORKFLOW[event.cron];
    if (!workflow) {
      console.error("unknown cron pattern (no mapping)", event.cron);
      return;
    }
    // waitUntil garantit qu'on attend la fin du dispatch même si le
    // handler "termine" tôt. Sans ça, le worker peut être tué avant.
    ctx.waitUntil(
      (async () => {
        try {
          await dispatchWorkflow(env, workflow, {});
          console.log("cron dispatched", workflow, "at", event.cron);
        } catch (e) {
          console.error("cron dispatch failed", workflow, e);
        }
      })(),
    );
  },
};

async function handleTelegram(req: Request, env: Env): Promise<Response> {
  const sig = req.headers.get("X-Telegram-Bot-Api-Secret-Token");
  if (sig !== env.TELEGRAM_WEBHOOK_SECRET) {
    return new Response("unauthorized", { status: 401 });
  }

  let update: TelegramUpdate;
  try {
    update = (await req.json()) as TelegramUpdate;
  } catch {
    return new Response("bad payload", { status: 400 });
  }

  try {
    if (update.callback_query) {
      await handleCallback(update.callback_query, env);
    } else if (update.message) {
      await handleMessage(update.message, env);
    }
  } catch (err) {
    console.error("handler error", err);
    // Toujours retourner 200 à Telegram pour éviter le retry-storm.
  }
  return new Response("ok");
}

function chatIdToChannel(chatId: string, env: Env): string | null {
  if (chatId === env.TELEGRAM_CHAT_PERSO) return "perso";
  if (chatId === env.TELEGRAM_CHAT_FAMILLE) return "famille";
  return null;
}

async function handleMessage(msg: TelegramMessage, env: Env): Promise<void> {
  const chatId = String(msg.chat.id);
  const text = (msg.text ?? "").trim();
  const channel = chatIdToChannel(chatId, env);

  if (channel === null) {
    console.log("ignoring message from unknown chat", chatId);
    return;
  }

  if (text === "/help" || text === "/start") {
    await tg(env, "sendMessage", {
      chat_id: chatId,
      text:
        "claudePA — commandes :\n" +
        "/panic — kill switch (pose la sentinelle)\n" +
        "/resume — réactive\n" +
        "/help — ce message\n\n" +
        "Sinon écris-moi librement, je réponds (~30-90s — cold start GH Actions).",
    });
    return;
  }

  if (text.startsWith("/panic")) {
    const reason = text.slice("/panic".length).trim();
    await dispatchWorkflow(env, "panic.yml", {
      action: "activate",
      reason: reason || `via Telegram by chat ${chatId}`,
    });
    await tg(env, "sendMessage", { chat_id: chatId, text: "🔴 panic dispatched" });
    return;
  }

  if (text.startsWith("/resume")) {
    await dispatchWorkflow(env, "panic.yml", { action: "release", reason: "" });
    await tg(env, "sendMessage", { chat_id: chatId, text: "🟢 resume dispatched" });
    return;
  }

  // Free-form → deposit + dispatch on-webhook.
  const inboxPath = await depositInbox(env, channel, msg);
  await dispatchWorkflow(env, "on-webhook.yml", {
    inbox_path: inboxPath,
    chat_id: chatId,
    channel: channel,
  });
  await tg(env, "sendMessage", {
    chat_id: chatId,
    text: "✓ reçu, je travaille dessus…",
  });
}

async function handleCallback(cb: TelegramCallbackQuery, env: Env): Promise<void> {
  const data = cb.data ?? "";
  const parts = data.split("|");
  // Format attendu: "draft|<OK|SKIP|EDIT>|<draft_path>"
  if (parts[0] !== "draft" || parts.length < 3) {
    await tg(env, "answerCallbackQuery", {
      callback_query_id: cb.id,
      text: "callback inconnu",
    });
    return;
  }
  const action = parts[1];
  const draftPath = parts.slice(2).join("|");
  const chatId = cb.message ? String(cb.message.chat.id) : "";

  if (chatId && chatIdToChannel(chatId, env) === null) {
    await tg(env, "answerCallbackQuery", {
      callback_query_id: cb.id,
      text: "chat non autorisé",
    });
    return;
  }

  await dispatchWorkflow(env, "apply-draft.yml", {
    draft_path: draftPath,
    action: action,
    chat_id: chatId,
    reason: "",
  });

  await tg(env, "answerCallbackQuery", {
    callback_query_id: cb.id,
    text: `${action} → en cours`,
  });
}

function utf8ToBase64(s: string): string {
  const bytes = new TextEncoder().encode(s);
  let bin = "";
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}

async function depositInbox(
  env: Env,
  channel: string,
  msg: TelegramMessage,
): Promise<string> {
  const ts = new Date(msg.date * 1000).toISOString();
  const safeTs = ts.replace(/[:.]/g, "-").slice(0, 19);
  const path = `inbox/${safeTs}-${channel}-${msg.message_id}.md`;
  const author = msg.from?.first_name ?? msg.from?.username ?? "unknown";
  const body = `---
channel: ${channel}
from: ${author}
timestamp: ${ts}
chat_id: ${msg.chat.id}
message_id: ${msg.message_id}
---

${msg.text ?? ""}
`;

  const url = `https://api.github.com/repos/${env.GITHUB_REPO}/contents/${path}`;
  const r = await fetch(url, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      "Content-Type": "application/json",
      "User-Agent": "claudepa-gateway",
      Accept: "application/vnd.github+json",
    },
    body: JSON.stringify({
      message: `inbox: ${channel} message ${msg.message_id}`,
      content: utf8ToBase64(body),
      branch: env.GITHUB_REF,
    }),
  });
  if (!r.ok) {
    console.error("contents api failed", r.status, await r.text());
    throw new Error(`contents api ${r.status}`);
  }
  return path;
}

async function dispatchWorkflow(
  env: Env,
  workflow: string,
  inputs: Record<string, string>,
): Promise<void> {
  const url = `https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/${workflow}/dispatches`;
  const r = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      "Content-Type": "application/json",
      "User-Agent": "claudepa-gateway",
      Accept: "application/vnd.github+json",
    },
    body: JSON.stringify({ ref: env.GITHUB_REF, inputs }),
  });
  if (!r.ok) {
    console.error("dispatch failed", workflow, r.status, await r.text());
    throw new Error(`dispatch ${workflow} ${r.status}`);
  }
}

async function tg(
  env: Env,
  method: string,
  payload: Record<string, unknown>,
): Promise<void> {
  const r = await fetch(
    `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/${method}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  if (!r.ok) {
    console.error("telegram", method, r.status, await r.text());
  }
}
