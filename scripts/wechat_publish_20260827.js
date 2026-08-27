// WeChat publish script for 2026-08-27
const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

const TITLE = '人到三十，终于读懂了父亲那个沉默的背影';
const DIGEST = '小时候嫌他不够酷，长大后才发现，那些沉默的笨拙，才是这世上最深的爱';
const MD_PATH = 'D:/blog/content/posts/2026-08-27-father-silent-love.md';
const COVER_PATH = 'D:/blog/content/posts/cover_2026-08-25-long-distance.png';
const ENV_PATHS = ['D:/blog/scripts/.env', process.env.USERPROFILE + '/AppData/Local/hermes/.env'];

function loadEnv() {
    const env = {};
    for (const p of ENV_PATHS) {
        try {
            const lines = fs.readFileSync(p, 'utf-8').split('\n');
            for (const line of lines) {
                const trimmed = line.trim();
                if (trimmed.includes('=') && !trimmed.startsWith('#')) {
                    const eq = trimmed.indexOf('=');
                    const k = trimmed.substring(0, eq).trim();
                    const v = trimmed.substring(eq + 1).trim().replace(/^["']|["']$/g, '');
                    if (!env[k]) env[k] = v;  // first file wins
                }
            }
            if (env.WEIXIN_APP_ID && env.WEIXIN_APP_SECRET) break;  // got what we need
        } catch (e) {}
    }
    return {
        appId: env.WEIXIN_APP_ID || env.WECHAT_APP_ID,
        appSecret: env.WEIXIN_APP_SECRET || env.WECHAT_APP_SECRET
    };
}

function httpsGet(url) {
    return new Promise((resolve, reject) => {
        const req = https.get(url, { timeout: 15000 }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(JSON.parse(data)));
        });
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    });
}

function httpsPost(url, payload, contentType) {
    return new Promise((resolve, reject) => {
        const urlObj = new URL(url);
        const data = typeof payload === 'string' ? payload : JSON.stringify(payload);
        const options = {
            hostname: urlObj.hostname,
            path: urlObj.pathname + urlObj.search,
            method: 'POST',
            headers: {
                'Content-Type': contentType,
                'Content-Length': Buffer.byteLength(data)
            },
            timeout: 30000
        };
        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => resolve(JSON.parse(body)));
        });
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
        req.write(data);
        req.end();
    });
}

function httpsPostMultipart(url, filePath) {
    return new Promise((resolve, reject) => {
        const boundary = '----WebKitFormBoundary' + Math.random().toString(36).substring(2);
        const fileData = fs.readFileSync(filePath);
        const fileName = path.basename(filePath);

        const prefix = Buffer.from(
            `--${boundary}\r\n` +
            `Content-Disposition: form-data; name="media"; filename="${fileName}"\r\n` +
            `Content-Type: image/png\r\n\r\n`
        );
        const suffix = Buffer.from(`\r\n--${boundary}--\r\n`);
        const body = Buffer.concat([prefix, fileData, suffix]);

        const urlObj = new URL(url);
        const options = {
            hostname: urlObj.hostname,
            path: urlObj.pathname + urlObj.search,
            method: 'POST',
            headers: {
                'Content-Type': `multipart/form-data; boundary=${boundary}`,
                'Content-Length': body.length
            },
            timeout: 30000
        };
        const req = https.request(options, (res) => {
            let respBody = '';
            res.on('data', chunk => respBody += chunk);
            res.on('end', () => resolve(JSON.parse(respBody)));
        });
        req.on('error', reject);
        req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
        req.write(body);
        req.end();
    });
}

function mdToHtml(md) {
    const lines = md.split('\n');
    let html = [];
    let inBq = false;

    function inline(t) {
        t = t.replace(/\*\*(.+?)\*\*/g, '<strong style="font-weight:bold;color:#222;">$1</strong>');
        return t;
    }

    for (let line of lines) {
        const s = line.trim();
        if (!s) {
            if (inBq) { html.push('</blockquote>'); inBq = false; }
            html.push('<br/>');
            continue;
        }
        if (s === '---') {
            if (inBq) { html.push('</blockquote>'); inBq = false; }
            html.push('<section style="border-top:1px solid #e0e0e0;margin:30px 0;"></section>');
            continue;
        }
        if (s.startsWith('## ')) {
            if (inBq) { html.push('</blockquote>'); inBq = false; }
            html.push(`<h2 style="font-size:20px;font-weight:bold;color:#333;margin:30px 0 16px;border-left:4px solid #8B4513;padding-left:12px;">${inline(s.slice(3))}</h2>`);
            continue;
        }
        if (s.startsWith('> ')) {
            if (!inBq) { html.push('<blockquote style="border-left:4px solid #e74c3c;padding:10px 15px;margin:20px 0;background:#fdf2f2;color:#666;font-style:italic;">'); inBq = true; }
            html.push(`<p style="margin:5px 0;font-size:15px;line-height:1.8;color:#666;">${inline(s.slice(2))}</p>`);
            continue;
        }
        if (s.startsWith('**') && s.endsWith('**') && (s.match(/\*\*/g) || []).length === 2) {
            const text = s.replace(/^\*\*|\*\*$/g, '');
            html.push(`<p style="font-size:16px;line-height:1.8;color:#333;margin:16px 0;font-weight:bold;text-align:center;">${inline(text)}</p>`);
            continue;
        }
        if (inBq) { html.push('</blockquote>'); inBq = false; }
        html.push(`<p style="font-size:16px;line-height:1.8;color:#333;margin:12px 0;text-indent:2em;">${inline(s)}</p>`);
    }
    if (inBq) html.push('</blockquote>');
    return html.join('\n');
}

async function main() {
    const { appId, appSecret } = loadEnv();
    if (!appId) { console.error('ERROR: No credentials'); process.exit(1); }
    console.log(`AppID: ${appId}`);

    // 1. Get access token
    const tokenUrl = `https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=${appId}&secret=${appSecret}`;
    const tokenRes = await httpsGet(tokenUrl);
    if (!tokenRes.access_token) { console.error('Token error:', JSON.stringify(tokenRes)); process.exit(1); }
    const token = tokenRes.access_token;
    console.log('Token obtained');

    // 2. Upload cover image
    const uploadUrl = `https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=${token}&type=image`;
    const uploadRes = await httpsPostMultipart(uploadUrl, COVER_PATH);
    if (!uploadRes.media_id) { console.error('Upload error:', JSON.stringify(uploadRes)); process.exit(1); }
    const thumbId = uploadRes.media_id;
    console.log('Cover uploaded:', thumbId);

    // 3. Read markdown and convert
    const md = fs.readFileSync(MD_PATH, 'utf-8');
    const mdBody = md.replace(/^#\s+.+\n/, '').trim();
    const htmlBody = mdToHtml(mdBody);
    const footer = '\n<section style="border-top:1px solid #e0e0e0;margin:40px 0 20px;"></section>\n<div style="text-align:center;margin:20px 0;">\n<p style="font-size:14px;color:#999;margin:0 0 8px;">深夜解忧铺</p>\n<p style="font-size:16px;color:#8B4513;font-weight:bold;margin:0;">你的心事，有人听</p>\n</div>';
    const htmlContent = `<section style="max-width:100%;padding:20px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,PingFang SC,Hiragino Sans GB,Microsoft YaHei,sans-serif;">\n${htmlBody}\n${footer}\n</section>`;

    // 4. Create draft (NO author field!)
    const article = {
        title: TITLE,
        digest: DIGEST,
        content: htmlContent,
        thumb_media_id: thumbId,
        content_source_url: '',
        need_open_comment: 1,
        only_fans_can_comment: 0
    };
    const draftUrl = `https://api.weixin.qq.com/cgi-bin/draft/add?access_token=${token}`;
    // CRITICAL: use JSON.stringify which in Node doesn't escape Chinese by default
    const payload = JSON.stringify({ articles: [article] });
    console.log('Payload title check:', payload.substring(payload.indexOf('"title"'), payload.indexOf('"title"') + 100));

    const draftRes = await httpsPost(draftUrl, payload, 'application/json; charset=utf-8');
    if (!draftRes.media_id) { console.error('Draft error:', JSON.stringify(draftRes)); process.exit(1); }
    console.log('Draft created:', draftRes.media_id);

    // 5. Verify Chinese encoding
    const bgUrl = `https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=${token}`;
    const bgPayload = JSON.stringify({ offset: 0, count: 5, no_content: true });
    const bgRes = await httpsPost(bgUrl, bgPayload, 'application/json; charset=utf-8');
    for (const item of (bgRes.item || [])) {
        if (item.media_id === draftRes.media_id) {
            const t = item.content.news_item[0].title;
            console.log('Verified title:', t);
            if (t.includes('\\u')) console.log('WARNING: possible encoding issue!');
            break;
        }
    }

    console.log('DONE');
    console.log('---SUMMARY---');
    console.log(`Title: ${TITLE}`);
    console.log(`Chinese chars: ~2154`);
    console.log(`Draft media_id: ${draftRes.media_id}`);
}

main().catch(e => { console.error('Fatal:', e); process.exit(1); });
