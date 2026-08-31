const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

const TITLE = "凌晨三点，我突然想起妈妈的白发";
const DIGEST = "凌晨三点突然醒来，想起妈妈弯腰切菜时白了一片的头发。那些平淡的日子，其实是妈妈用命在撑。";
const SLUG = "2026-08-31-mama-baifa";
const MD_PATH = "D:/blog/content/posts/" + SLUG + ".md";
const ENV_PATH = "D:/blog/scripts/.env";

function loadEnv() {
    const env = {};
    try {
        const lines = fs.readFileSync(ENV_PATH, 'utf-8').split('\n');
        for (const line of lines) {
            const t = line.trim();
            if (t.includes('=') && !t.startsWith('#')) {
                const eq = t.indexOf('=');
                const k = t.substring(0, eq).trim();
                const v = t.substring(eq + 1).trim().replace(/^["']|["']$/g, '');
                if (!env[k]) env[k] = v;
            }
        }
    } catch (e) { console.error('Failed to read env:', e.message); }
    return { appId: env.WEIXIN_APP_ID, appSecret: env.WEIXIN_APP_SECRET };
}

function httpGet(url, timeout) {
    timeout = timeout || 15000;
    return new Promise((resolve, reject) => {
        const mod = url.startsWith('https') ? https : http;
        mod.get(url, { timeout }, (res) => {
            if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                return httpGet(res.headers.location, timeout).then(resolve, reject);
            }
            const chunks = [];
            res.on('data', c => chunks.push(c));
            res.on('end', () => resolve(Buffer.concat(chunks)));
        }).on('error', reject);
    });
}

function httpsPost(url, payload, ct) {
    return new Promise((resolve, reject) => {
        const u = new URL(url);
        const data = typeof payload === 'string' ? payload : JSON.stringify(payload);
        const mod = u.protocol === 'https:' ? https : http;
        const opts = {
            hostname: u.hostname, port: u.port,
            path: u.pathname + u.search, method: 'POST',
            headers: { 'Content-Type': ct, 'Content-Length': Buffer.byteLength(data) },
            timeout: 30000
        };
        const req = mod.request(opts, (res) => {
            let b = '';
            res.on('data', c => b += c);
            res.on('end', () => { try { resolve(JSON.parse(b)); } catch(e) { resolve({ raw: b }); } });
        });
        req.on('error', reject); req.write(data); req.end();
    });
}

function httpsPostMultipart(url, filePath) {
    return new Promise((resolve, reject) => {
        const boundary = '----WebKitFormBoundary' + Math.random().toString(36).slice(2);
        const fileData = fs.readFileSync(filePath);
        const ext = path.extname(filePath).toLowerCase();
        const fileCt = (ext === '.jpg' || ext === '.jpeg') ? 'image/jpeg' : 'image/png';
        const prefix = Buffer.from('--' + boundary + '\r\nContent-Disposition: form-data; name="media"; filename="' + path.basename(filePath) + '"\r\nContent-Type: ' + fileCt + '\r\n\r\n');
        const suffix = Buffer.from('\r\n--' + boundary + '--\r\n');
        const body = Buffer.concat([prefix, fileData, suffix]);
        const u = new URL(url);
        const mod = u.protocol === 'https:' ? https : http;
        const opts = {
            hostname: u.hostname, port: u.port,
            path: u.pathname + u.search, method: 'POST',
            headers: { 'Content-Type': 'multipart/form-data; boundary=' + boundary, 'Content-Length': body.length },
            timeout: 60000
        };
        const req = mod.request(opts, (res) => {
            let b = '';
            res.on('data', c => b += c);
            res.on('end', () => { try { resolve(JSON.parse(b)); } catch(e) { resolve({ raw: b }); } });
        });
        req.on('error', reject); req.write(body); req.end();
    });
}

async function downloadCover() {
    const coverPath = 'D:/blog/content/posts/cover_' + SLUG + '.png';
    if (fs.existsSync(coverPath) && fs.statSync(coverPath).size > 10000) {
        console.log('Cover exists:', coverPath);
        return coverPath;
    }
    const seed = Math.floor(Math.random() * 99999);
    const prompt = encodeURIComponent('warm cozy night scene with soft street lamp light, mother figure silhouette, nostalgic healing atmosphere, pastel warm colors, dreamy bokeh, japanese anime aesthetic');
    const url = 'https://image.pollinations.ai/prompt/' + prompt + '?width=900&height=383&nologo=true&seed=' + seed;
    console.log('Downloading cover from Pollinations...');
    const imgData = await httpGet(url, 60000);
    fs.writeFileSync(coverPath, imgData);
    console.log('Cover saved:', coverPath, 'size:', imgData.length);
    return coverPath;
}

function mdToHtml(md) {
    const lines = md.split('\n');
    const html = [];
    let inBq = false;
    const inline = t => t.replace(/\*\*(.+?)\*\*/g, '<strong style="font-weight:bold;color:#222;">$1</strong>');
    for (let line of lines) {
        const s = line.trim();
        if (!s) { if (inBq) { html.push('</blockquote>'); inBq = false; } html.push('<br/>'); continue; }
        if (s === '---') { if (inBq) { html.push('</blockquote>'); inBq = false; } html.push('<section style="border-top:1px solid #e0e0e0;margin:30px 0;"></section>'); continue; }
        if (s.startsWith('## ')) { if (inBq) { html.push('</blockquote>'); inBq = false; } html.push('<h2 style="font-size:20px;font-weight:bold;color:#333;margin:30px 0 16px;border-left:4px solid #8B4513;padding-left:12px;">' + inline(s.slice(3)) + '</h2>'); continue; }
        if (s.startsWith('> ')) { if (!inBq) { html.push('<blockquote style="border-left:4px solid #e74c3c;padding:10px 15px;margin:20px 0;background:#fdf2f2;color:#666;font-style:italic;">'); inBq = true; } html.push('<p style="margin:5px 0;font-size:15px;line-height:1.8;color:#666;">' + inline(s.slice(2)) + '</p>'); continue; }
        if (inBq) { html.push('</blockquote>'); inBq = false; }
        html.push('<p style="font-size:16px;line-height:1.8;color:#333;margin:12px 0;text-indent:2em;">' + inline(s) + '</p>');
    }
    if (inBq) html.push('</blockquote>');
    return html.join('\n');
}

async function main() {
    const creds = loadEnv();
    console.log('App ID:', creds.appId ? creds.appId.substring(0,6) + '...' : 'MISSING');
    if (!creds.appId || !creds.appSecret) { console.error('Missing credentials'); process.exit(1); }

    // 1. Token
    console.log('Step 1: Getting access token...');
    const tokenBuf = await httpGet('https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=' + creds.appId + '&secret=' + creds.appSecret);
    const tokenRes = JSON.parse(tokenBuf.toString());
    if (!tokenRes.access_token) { console.error('Token error:', JSON.stringify(tokenRes)); process.exit(1); }
    const token = tokenRes.access_token;
    console.log('Token OK');

    // 2. Cover
    console.log('Step 2: Uploading cover...');
    const coverPath = await downloadCover();
    const uploadRes = await httpsPostMultipart(
        'https://api.weixin.qq.com/cgi-bin/material/add_material?access_token=' + token + '&type=image',
        coverPath
    );
    if (!uploadRes.media_id) { console.error('Upload error:', JSON.stringify(uploadRes)); process.exit(1); }
    console.log('Cover uploaded:', uploadRes.media_id);

    // 3. MD -> HTML
    console.log('Step 3: Converting markdown...');
    const md = fs.readFileSync(MD_PATH, 'utf-8');
    // Remove YAML frontmatter
    const body = md.replace(/^---[\s\S]*?---\s*/, '').trim();
    // Remove H1 title (already in title field)
    const bodyNoTitle = body.replace(/^#\s+.+\n/, '').trim();
    const htmlBody = mdToHtml(bodyNoTitle);
    const footer = '\n<section style="border-top:1px solid #e0e0e0;margin:40px 0 20px;"></section>\n<div style="text-align:center;margin:20px 0;">\n<p style="font-size:14px;color:#999;margin:0 0 8px;">深夜解忧铺</p>\n<p style="font-size:16px;color:#8B4513;font-weight:bold;margin:0;">你的心事，有人听</p>\n</div>';
    const htmlContent = '<section style="max-width:100%;padding:20px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,PingFang SC,Hiragino Sans GB,Microsoft YaHei,sans-serif;">\n' + htmlBody + '\n' + footer + '\n</section>';
    console.log('HTML length:', htmlContent.length);

    // 4. Create draft (NO author field!)
    console.log('Step 4: Creating draft...');
    const article = {
        title: TITLE,
        digest: DIGEST,
        content: htmlContent,
        thumb_media_id: uploadRes.media_id,
        content_source_url: '',
        need_open_comment: 1,
        only_fans_can_comment: 0
    };
    const draftData = JSON.stringify({ articles: [article] });
    const draftRes = await httpsPost(
        'https://api.weixin.qq.com/cgi-bin/draft/add?access_token=' + token,
        draftData,
        'application/json; charset=utf-8'
    );
    if (!draftRes.media_id) { console.error('Draft error:', JSON.stringify(draftRes)); process.exit(1); }
    console.log('Draft created:', draftRes.media_id);

    // 5. Verify
    console.log('Step 5: Verifying...');
    const bgRes = await httpsPost(
        'https://api.weixin.qq.com/cgi-bin/draft/batchget?access_token=' + token,
        JSON.stringify({ offset: 0, count: 5, no_content: true }),
        'application/json; charset=utf-8'
    );
    for (const item of (bgRes.item || [])) {
        if (item.media_id === draftRes.media_id) {
            const draftTitle = item.content.news_item[0].title;
            console.log('Verified title:', draftTitle);
            // Check for unicode escape (garbled)
            if (draftTitle.includes('\\u')) {
                console.error('WARNING: Title may be garbled!');
            }
            break;
        }
    }

    console.log('\n=== DONE ===');
    console.log('Title:', TITLE);
    console.log('Digest:', DIGEST);
    console.log('Draft media_id:', draftRes.media_id);
    console.log('Cover media_id:', uploadRes.media_id);
    console.log('Markdown:', MD_PATH);
    console.log('Action: Go to WeChat backend -> 草稿箱 -> publish manually');
}

main().catch(e => { console.error('Fatal:', e); process.exit(1); });
